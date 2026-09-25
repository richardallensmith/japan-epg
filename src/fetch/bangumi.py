from __future__ import annotations

import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ..models import Programme
from .base import SourceError

JST = ZoneInfo("Asia/Tokyo")
EPISODE_RE = re.compile(r"(?:#|＃|第|（|\()\s*([0-9０-９]+)\s*(?:話|回|）|\))?")

GENRE_NAMES = {
    "gc-anime": "アニメ／特撮",
    "gc-drama": "ドラマ",
    "gc-movie": "映画",
    "gc-music": "音楽",
    "gc-sports": "スポーツ",
}


class _BangumiParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.channel_names: list[str] = []
        self.program_lines: dict[int, list[dict]] = {}
        self._in_channel_area = False
        self._channel_depth = 0
        self._capture_channel = False
        self._current_line: int | None = None
        self._current: dict | None = None
        self._capture_field: str | None = None
        self._buffer: list[str] = []

    @staticmethod
    def _attrs(attrs) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = self._attrs(attrs)
        if tag == "div" and attributes.get("id") == "ch_area":
            self._in_channel_area = True
            self._channel_depth = 1
            return
        if self._in_channel_area and tag == "div":
            self._channel_depth += 1
        if self._in_channel_area and tag == "p":
            self._capture_channel = True
            self._buffer = []
            return

        if tag == "ul" and attributes.get("id", "").startswith("program_line_"):
            self._current_line = int(attributes["id"].rsplit("_", 1)[1])
            self.program_lines.setdefault(self._current_line, [])
            return
        if self._current_line is not None and tag == "li" and attributes.get("s") and attributes.get("e"):
            self._current = {
                "start": attributes["s"],
                "stop": attributes["e"],
                "source_id": attributes.get("se-id") or attributes.get("pid", ""),
                "title": "",
                "description": "",
                "genre": "",
                "href": "",
            }
            return
        if self._current is not None and tag == "a" and "title_link" in attributes.get("class", "").split():
            self._current["href"] = attributes.get("href", "")
        if self._current is not None and tag == "div":
            classes = attributes.get("class", "").split()
            for css_class in classes:
                if css_class.startswith("gc-"):
                    self._current["genre"] = GENRE_NAMES.get(css_class, "")
        if self._current is not None and tag == "p":
            classes = attributes.get("class", "").split()
            if "program_title" in classes:
                self._capture_field = "title"
                self._buffer = []
            elif "program_detail" in classes:
                self._capture_field = "description"
                self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture_channel or self._capture_field:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._capture_channel and tag == "p":
            name = " ".join("".join(self._buffer).split())
            if name:
                self.channel_names.append(name)
            self._capture_channel = False
            self._buffer = []
            return
        if self._capture_field and tag == "p":
            self._current[self._capture_field] = " ".join("".join(self._buffer).split())
            self._capture_field = None
            self._buffer = []
            return
        if self._current is not None and tag == "li":
            self.program_lines[self._current_line].append(self._current)
            self._current = None
            return
        if self._current_line is not None and tag == "ul":
            self._current_line = None
            return
        if self._in_channel_area and tag == "div":
            self._channel_depth -= 1
            if self._channel_depth <= 0:
                self._in_channel_area = False


class BangumiSource:
    """Tokyo terrestrial schedules from G.GUIDE's broadcaster-supplied listings."""

    name = "G.GUIDE broadcaster-official Tokyo listings (bangumi.org)"
    endpoint = "https://bangumi.org/epg/td?broad_cast_date={date}&ggm_group_id=42"
    _page_cache: dict[str, _BangumiParser] = {}

    def __init__(self, *, station: str, timeout: int = 30):
        self.station = station
        self.timeout = timeout

    def _get_page(self, date_string: str) -> _BangumiParser:
        if date_string in self._page_cache:
            return self._page_cache[date_string]
        url = self.endpoint.format(date=date_string)
        request = Request(url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                html = response.read().decode(response.headers.get_content_charset() or "utf-8")
        except Exception as exc:
            raise SourceError(f"G.GUIDE request failed for {date_string}: {exc}") from exc
        parser = _BangumiParser()
        parser.feed(html)
        if not parser.channel_names or not parser.program_lines:
            raise SourceError(f"G.GUIDE returned a structurally valid page but no meaningful schedule for {date_string}")
        self._page_cache[date_string] = parser
        return parser

    @staticmethod
    def _markers(title: str) -> set[str]:
        markers: set[str] = set()
        if any(mark in title for mark in ("🈞", "[再]", "［再］", "【再】")):
            markers.add("repeat")
        if any(mark in title for mark in ("🈢", "[生]", "［生］", "【生】")):
            markers.add("live")
        if "🈡" in title or "最終回" in title:
            markers.add("finale")
        if any(mark in title for mark in ("スペシャル", "SP", "ＳＰ", "特集")):
            markers.add("special")
        return markers

    @staticmethod
    def _episode_number(title: str) -> str:
        match = EPISODE_RE.search(title)
        if not match:
            return ""
        return match.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789"))

    def _parse(self, page: _BangumiParser, channel_id: str, request_date: str) -> list[Programme]:
        matches = [
            index
            for index, name in enumerate(page.channel_names, start=1)
            if name.endswith(self.station) or self.station in name
        ]
        if len(matches) != 1:
            raise SourceError(
                f"Expected one G.GUIDE station matching {self.station!r} for {request_date}; found {len(matches)}"
            )
        rows = page.program_lines.get(matches[0], [])
        programmes: list[Programme] = []
        for row in rows:
            if not row["title"]:
                continue
            categories = [row["genre"]] if row["genre"] else []
            programmes.append(
                Programme(
                    channel_id=channel_id,
                    start=datetime.strptime(row["start"], "%Y%m%d%H%M").replace(tzinfo=JST),
                    stop=datetime.strptime(row["stop"], "%Y%m%d%H%M").replace(tzinfo=JST),
                    title_ja=row["title"],
                    description_ja=row["description"],
                    episode_number=self._episode_number(row["title"]),
                    categories_ja=categories,
                    markers=self._markers(row["title"]),
                    source_id=row["source_id"],
                    source_url=urljoin("https://bangumi.org", row["href"]),
                )
            )
        if len(programmes) < 3:
            raise SourceError(
                f"G.GUIDE returned only {len(programmes)} meaningful {self.station} entries for {request_date}"
            )
        return programmes

    def fetch(self, *, channel_id: str, now: datetime, days: int = 1) -> list[Programme]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        now_jst = now.astimezone(JST)
        dates = [(now_jst.date() - timedelta(days=1) + timedelta(days=i)) for i in range(days + 2)]
        all_programmes: list[Programme] = []
        for day in dates:
            date_string = day.strftime("%Y%m%d")
            all_programmes.extend(self._parse(self._get_page(date_string), channel_id, date_string))
        future_limit = now_jst + timedelta(days=days, hours=5)
        return [p for p in all_programmes if p.stop > now_jst and p.start < future_limit]
