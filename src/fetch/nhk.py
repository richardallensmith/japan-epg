from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ..models import Programme

JST = ZoneInfo("Asia/Tokyo")
EPISODE_RE = re.compile(r"(?:\(|（)([0-9０-９]+)(?:\)|）)")


class SourceError(RuntimeError):
    pass


class NHKTimetableSource:
    """Adapter for the JSON endpoint used by NHK's public timetable page."""

    name = "NHK official public timetable (api.nhk.jp/r8)"
    endpoint = "https://api.nhk.jp/r8/pg/date/tv/{area}/{date}.json"

    def __init__(self, *, area: str = "130", service: str = "g1", timeout: int = 30):
        self.area = area
        self.service = service
        self.timeout = timeout

    def _get_json(self, date_string: str) -> dict:
        url = self.endpoint.format(area=self.area, date=date_string)
        request = Request(url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SourceError(f"NHK timetable request failed for {date_string}: {exc}") from exc

    @staticmethod
    def _markers(item: dict) -> set[str]:
        title = item.get("name", "")
        markers: set[str] = set()
        if any(mark in title for mark in ("🈞", "[再]", "［再］", "【再】")):
            markers.add("repeat")
        if any(mark in title for mark in ("🈢", "[生]", "［生］", "【生】")):
            markers.add("live")
        if "🈡" in title or "最終回" in title:
            markers.add("finale")
        if any(mark in title for mark in ("スペシャル", "ＳＰ", "特集")):
            markers.add("special")
        return markers

    @staticmethod
    def _episode_number(item: dict) -> str:
        group = item.get("identifierGroup") or {}
        episode_name = group.get("tvEpisodeName") or ""
        match = EPISODE_RE.search(episode_name) or EPISODE_RE.search(item.get("name", ""))
        if match:
            return match.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        return ""

    def _parse(self, payload: dict, channel_id: str, request_date: str) -> list[Programme]:
        service_data = payload.get(self.service)
        publications = service_data.get("publication") if isinstance(service_data, dict) else None
        if not isinstance(publications, list) or not publications:
            raise SourceError(
                f"NHK returned structurally valid data but no meaningful {self.service} schedule for {request_date}"
            )
        programmes: list[Programme] = []
        for item in publications:
            title = item.get("name")
            start_raw = item.get("startDate")
            stop_raw = item.get("endDate")
            if not title or not start_raw or not stop_raw:
                continue
            group = item.get("identifierGroup") or {}
            genres = group.get("genre") or []
            categories = []
            for genre in genres:
                for key in ("name1", "name2"):
                    value = genre.get(key)
                    if value and value not in categories:
                        categories.append(value)
            programmes.append(
                Programme(
                    channel_id=channel_id,
                    start=datetime.fromisoformat(start_raw),
                    stop=datetime.fromisoformat(stop_raw),
                    title_ja=title,
                    description_ja=item.get("description") or (item.get("detailedDescription") or {}).get("epg200", ""),
                    episode_number=self._episode_number(item),
                    categories_ja=categories,
                    markers=self._markers(item),
                    source_id=item.get("id", ""),
                    source_url=item.get("url", ""),
                )
            )
        if len(programmes) < 3:
            raise SourceError(f"NHK returned only {len(programmes)} meaningful entries for {request_date}")
        return programmes

    def fetch(self, *, channel_id: str, now: datetime, days: int = 1) -> list[Programme]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        now_jst = now.astimezone(JST)
        # NHK broadcast days run roughly 05:00 to 05:00, so include yesterday.
        dates = [(now_jst.date() - timedelta(days=1) + timedelta(days=i)) for i in range(days + 2)]
        all_programmes: list[Programme] = []
        for day in dates:
            date_string = day.isoformat()
            all_programmes.extend(self._parse(self._get_json(date_string), channel_id, date_string))
        future_limit = now_jst + timedelta(days=days, hours=5)
        return [p for p in all_programmes if p.stop > now_jst and p.start < future_limit]
