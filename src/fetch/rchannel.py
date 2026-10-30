"""R Channel's own dated programme grid, guarded against playlist drift."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ..models import Programme
from .base import SourceError

JST = ZoneInfo("Asia/Tokyo")


class RChannelSource:
    name = "R Channel official programme grid"
    endpoint = "https://backendapi.channel.rakuten.co.jp/platform/content/programs"
    _page_cache: dict[str, list[dict]] = {}

    def __init__(self, *, source_channel_id: int, source_title: str,
                 playlist_stream_url: str, source_language: str = "ja", timeout: int = 30):
        if source_language not in {"ja", "en"}:
            raise ValueError(f"Unsupported R Channel source language: {source_language!r}")
        self.source_channel_id = source_channel_id
        self.source_title = source_title
        self.playlist_stream_url = playlist_stream_url
        self.source_language = source_language
        self.timeout = timeout

    def _page(self, day: str) -> list[dict]:
        if day in self._page_cache:
            return self._page_cache[day]
        url = self.endpoint + "?" + urlencode({"date": day, "platform": "WEB"})
        try:
            request = Request(url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"})
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except Exception as exc:
            raise SourceError(f"R Channel grid request failed for {day}: {exc}") from exc
        if payload.get("status") != 200 or not isinstance(payload.get("data"), list):
            raise SourceError(f"R Channel returned no usable grid for {day}")
        self._page_cache[day] = payload["data"]
        return payload["data"]

    def fetch(self, *, channel_id: str, now: datetime, days: int = 1) -> list[Programme]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if channel_id != f"rch_{self.source_channel_id}":
            raise SourceError(f"R Channel ID {self.source_channel_id} differs from playlist ID {channel_id!r}")
        now_jst = now.astimezone(JST)
        limit = now_jst + timedelta(days=days, hours=5)
        first = now_jst.date() - timedelta(days=1)
        last = limit.date()
        programmes: dict[tuple[datetime, datetime, str], Programme] = {}
        for offset in range((last - first).days + 1):
            day = (first + timedelta(days=offset)).isoformat()
            matches = [row for row in self._page(day) if row.get("id") == self.source_channel_id]
            if len(matches) != 1:
                raise SourceError(f"R Channel {self.source_channel_id} missing or duplicated on {day}")
            channel = matches[0]
            if channel.get("title") != self.source_title or channel.get("manifestUrl") != self.playlist_stream_url:
                raise SourceError(f"R Channel {self.source_channel_id} identity or stream changed on {day}")
            rows = channel.get("programs")
            if not isinstance(rows, list) or len(rows) < 3:
                raise SourceError(f"R Channel {self.source_channel_id} has no usable programmes on {day}")
            for row in rows:
                try:
                    start = datetime.fromisoformat(row["start"])
                    stop = datetime.fromisoformat(row["end"])
                    title = " ".join(row["title"].split())
                except (KeyError, TypeError, ValueError, AttributeError) as exc:
                    raise SourceError(f"R Channel {self.source_channel_id} has malformed programme data") from exc
                if (row.get("channelId") != self.source_channel_id or start.utcoffset() != timedelta(hours=9)
                        or stop.utcoffset() != timedelta(hours=9) or stop <= start or not title):
                    raise SourceError(f"R Channel {self.source_channel_id} has invalid programme data")
                if stop <= now_jst or start >= limit:
                    continue
                description = " ".join((row.get("description") or "").split())
                genre = " ".join((row.get("genreName") or "").split())
                key = (start, stop, title)
                programmes[key] = Programme(
                    channel_id=channel_id, start=start, stop=stop,
                    title_ja=title if self.source_language == "ja" else "",
                    title_en=title if self.source_language == "en" else "",
                    description_ja=description if self.source_language == "ja" else "",
                    description_en=description if self.source_language == "en" else "",
                    categories_ja=[genre] if genre else [],
                    source_id=str(row.get("id") or ""),
                    source_url=f"https://channel.rakuten.co.jp/schedule/{day}",
                )
        result = sorted(programmes.values(), key=lambda p: (p.start, p.stop))
        if self.source_channel_id == 120:
            # Reuters occasionally publishes two conflicting slots. Neither
            # interval can be trusted, so omit both rather than invent an end.
            conflicted = set()
            for index, (current, following) in enumerate(zip(result, result[1:])):
                if current.stop - following.start > timedelta(seconds=1):
                    conflicted.update((index, index + 1))
            if conflicted:
                if len(conflicted) != 2:
                    raise SourceError("R Channel 120 has multiple conflicting programmes")
                result = [p for index, p in enumerate(result) if index not in conflicted]
        if len(result) < 3 or result[-1].stop < now_jst + timedelta(hours=2):
            raise SourceError(f"R Channel {self.source_channel_id} has insufficient current/future coverage")
        for current, following in zip(result, result[1:]):
            overlap = current.stop - following.start
            if overlap > timedelta(seconds=1):
                raise SourceError(f"R Channel {self.source_channel_id} has overlapping programmes")
            if overlap > timedelta(0):
                # The source occasionally rounds adjacent FAST events one second apart.
                current.stop = following.start
        return result
