"""NHK WORLD-JAPAN's public, English-language live TV timetable."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

from ..models import Programme
from .base import SourceError
from .bangumi import JST


class NHKWorldSource:
    name = "NHK WORLD-JAPAN official live TV timetable"
    endpoint = "https://masterpl.hls.nhkworld.jp/epg/w/{date}.json"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def fetch(self, *, channel_id: str, now: datetime, days: int = 1) -> list[Programme]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        now_jst = now.astimezone(JST)
        future_limit = now_jst + timedelta(days=days, hours=5)
        programmes = []
        for offset in range((future_limit.date() - now_jst.date()).days + 1):
            day = now_jst.date() + timedelta(days=offset)
            url = self.endpoint.format(date=day.strftime("%Y%m%d"))
            try:
                with urlopen(Request(url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"}),
                             timeout=self.timeout) as response:
                    payload = json.load(response)
            except Exception as exc:
                raise SourceError(f"NHK WORLD timetable request failed for {day}: {exc}") from exc
            rows = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(rows, list) or len(rows) < 3:
                raise SourceError(f"NHK WORLD returned no meaningful timetable for {day}")
            for row in rows:
                try:
                    start = datetime.fromisoformat(row["startTime"])
                    stop = datetime.fromisoformat(row["endTime"])
                    title = row["title"].strip()
                except (KeyError, TypeError, ValueError) as exc:
                    raise SourceError(f"NHK WORLD timetable row is malformed for {day}") from exc
                if not title or start.utcoffset() != timedelta(hours=9) or stop <= start:
                    raise SourceError(f"NHK WORLD timetable row is invalid for {day}")
                if stop <= now_jst or start >= future_limit:
                    continue
                episode = (row.get("episodeTitle") or "").strip()
                programmes.append(Programme(
                    channel_id=channel_id, start=start, stop=stop,
                    title_ja="", title_en=f"{title}: {episode}" if episode else title,
                    description_en=(row.get("description") or "").strip(),
                    source_id=row.get("episodeId", ""), source_url=row.get("episodeLink") or url,
                ))
        if len(programmes) < 3:
            raise SourceError("NHK WORLD returned fewer than three current/future programmes")
        return programmes
