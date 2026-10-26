from __future__ import annotations

import json
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ..models import Programme
from .base import SourceError

JST = ZoneInfo("Asia/Tokyo")


class WeathernewsSource:
    """Weathernews LiVE's broadcaster-published rolling programme timetable."""

    name = "Weathernews LiVE official timetable"
    url = "https://site.weathernews.jp/site/live/json/timetable.json"

    def __init__(self, *, timeout: int = 30):
        self.timeout = timeout

    def fetch(self, *, channel_id: str, now: datetime, days: int = 1) -> list[Programme]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        request = Request(self.url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                rows = json.load(response)
        except Exception as exc:
            raise SourceError(f"Weathernews timetable request failed: {exc}") from exc
        if not isinstance(rows, list) or len(rows) < 4:
            raise SourceError("Weathernews timetable has too few entries")

        now_jst = now.astimezone(JST)
        starts: list[datetime] = []
        titles: list[str] = []
        previous = None
        for row in rows:
            if not isinstance(row, dict):
                raise SourceError("Weathernews timetable entry is not an object")
            try:
                hour = datetime.strptime(row["hour"], "%H:%M").time()
                title = row["title"].strip()
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise SourceError("Weathernews timetable has a malformed entry") from exc
            if not title:
                raise SourceError("Weathernews timetable has an empty programme title")
            if previous is None:
                # The first entry is the current programme. Its clock time can
                # precede the current clock time, including across midnight.
                start = datetime.combine(now_jst.date(), hour, JST)
                if start > now_jst:
                    start -= timedelta(days=1)
                if now_jst - start > timedelta(hours=6):
                    raise SourceError("Weathernews timetable does not begin near the current time")
            else:
                start = datetime.combine(previous.date(), hour, JST)
                if start <= previous:
                    start += timedelta(days=1)
                if start - previous > timedelta(hours=8):
                    raise SourceError("Weathernews timetable has an implausible gap")
            starts.append(start)
            titles.append(title)
            previous = start

        limit = now_jst + timedelta(days=days, hours=5)
        programmes = [
            Programme(channel_id=channel_id, start=start, stop=stop,
                      title_ja=title, source_url="https://weathernews.jp/wnl/timetable.html")
            for start, stop, title in zip(starts, starts[1:], titles)
            if stop > now_jst and start < limit
        ]
        if len(programmes) < 3 or programmes[-1].stop < now_jst + timedelta(hours=2):
            raise SourceError("Weathernews timetable has insufficient current/future coverage")
        return programmes
