from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ..models import Programme
from .base import SourceError

JST = ZoneInfo("Asia/Tokyo")
RANGE_RE = re.compile(r"^(\d{2}):(\d{2})〜(\d{2}):(\d{2})$")


class _ScheduleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.dates: list[date] = []
        self.rows: list[tuple[date, str, str]] = []
        self.section = ""
        self.column = -1
        self.item: dict[str, str] | None = None
        self.capture = ""
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = dict(attrs)
        if tag == "div" and "p-schedule__hdr" in a.get("class", "").split() and a.get("data-date"):
            self.dates.append(date.fromisoformat(a["data-date"]))
        if tag == "tr" and a.get("id") in {"js-am", "js-pm", "js-md"}:
            self.section = a["id"]
            self.column = -1
        elif self.section and tag == "td":
            self.column += 1
        elif self.section and tag == "li" and "p-program__item" in a.get("class", "").split():
            self.item = {}
        elif self.item is not None and tag == "p":
            classes = a.get("class", "").split()
            if "p-program__range" in classes:
                self.capture = "range"
                self.parts = []
            elif "p-program__name" in classes:
                self.capture = "title"
                self.parts = []

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self.capture:
            if self.item is not None:
                self.item[self.capture] = " ".join("".join(self.parts).split())
            self.capture = ""
        elif tag == "li" and self.item is not None:
            if self.column >= 0 and self.column < len(self.dates) and self.item.get("range") and self.item.get("title"):
                day = self.dates[self.column] + timedelta(days=1 if self.section == "js-md" else 0)
                self.rows.append((day, self.item["range"], self.item["title"]))
            self.item = None
        elif tag == "tr" and self.section:
            self.section = ""


class SkyPerfectVSource:
    """Sky PerfecTV's published CS527 electronic programme guide."""

    name = "Sky PerfecTV premium CS527 programme guide"
    url = "https://www.skyperfectv.co.jp/program/schedule/premium/channel%3A527/"

    def __init__(self, *, timeout: int = 30):
        self.timeout = timeout

    def fetch(self, *, channel_id: str, now: datetime, days: int = 1) -> list[Programme]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        try:
            with urlopen(Request(self.url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"}), timeout=self.timeout) as response:
                html = response.read().decode("utf-8")
        except Exception as exc:
            raise SourceError(f"Sky PerfecTV CS527 request failed: {exc}") from exc
        if "channel%3A527/" not in html or "ジュエリー☆ＧＳＴＶ" not in html:
            raise SourceError("Sky PerfecTV guide no longer identifies premium CS527 GSTV")
        parser = _ScheduleParser()
        parser.feed(html)
        if len(parser.dates) < 2 or len(parser.rows) < 3:
            raise SourceError("Sky PerfecTV CS527 guide has no usable dated schedule")
        now_jst = now.astimezone(JST)
        limit = now_jst + timedelta(days=days, hours=5)
        programmes: list[Programme] = []
        for day, time_range, title in parser.rows:
            match = RANGE_RE.fullmatch(time_range)
            if not match:
                raise SourceError(f"Sky PerfecTV CS527 has invalid time range: {time_range!r}")
            h1, m1, h2, m2 = map(int, match.groups())
            if h1 > 23 or h2 > 24 or m1 > 59 or m2 > 59 or (h2 == 24 and m2):
                raise SourceError(f"Sky PerfecTV CS527 has invalid time range: {time_range!r}")
            start = datetime.combine(day, datetime.min.time(), JST) + timedelta(hours=h1, minutes=m1)
            stop = datetime.combine(day, datetime.min.time(), JST) + timedelta(hours=h2, minutes=m2)
            if stop <= start:
                stop += timedelta(days=1)
            if stop > now_jst and start < limit:
                programmes.append(Programme(channel_id=channel_id, start=start, stop=stop,
                                            title_ja=title, source_url=self.url))
        programmes.sort(key=lambda p: p.start)
        if len(programmes) < 3 or programmes[-1].stop < now_jst + timedelta(hours=2):
            raise SourceError("Sky PerfecTV CS527 guide has insufficient current/future coverage")
        if any(a.stop > b.start for a, b in zip(programmes, programmes[1:])):
            raise SourceError("Sky PerfecTV CS527 guide has overlapping programmes")
        return programmes
