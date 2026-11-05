"""Fast TV's public player guide, pinned to the live stream identity."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ..models import Programme
from .base import SourceError

JST = ZoneInfo("Asia/Tokyo")


class FastVSource:
    name = "Fast TV public player guide"
    base = "https://fastv-v2.routez.cloud/api/v2/fastv2/api/"
    # Public key embedded in the player on fastv.jp, not a user credential.
    app_key = "0FIpP%2BH3RDgE%2BOc5uU7cmA%3D%3D"
    _channels: list[dict] | None = None

    def __init__(self, *, source_channel_id: str, source_channel_name: str,
                 playlist_stream_url: str, timeout: int = 30):
        self.source_channel_id = source_channel_id
        self.source_channel_name = source_channel_name
        self.playlist_stream_url = playlist_stream_url
        self.timeout = timeout

    def _get(self, url: str) -> dict:
        try:
            request = Request(url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"})
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except Exception as exc:
            raise SourceError(f"Fast TV request failed: {exc}") from exc
        if not isinstance(payload, dict) or payload.get("error") != 0:
            raise SourceError(f"Fast TV returned an unusable response: {url}")
        return payload

    def fetch(self, *, channel_id: str, now: datetime, days: int = 1) -> list[Programme]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if channel_id != f"fastch_v2_{self.source_channel_id}":
            raise SourceError("Fast TV source ID differs from playlist ID")
        if self._channels is None:
            payload = self._get(self.base + "getChannelList?did=null&app=" + self.app_key)
            if not isinstance(payload.get("channels"), list):
                raise SourceError("Fast TV returned no channel list")
            type(self)._channels = payload["channels"]
        matches = [row for row in self._channels if row.get("channel_id") == self.source_channel_id]
        if len(matches) != 1 or matches[0].get("channel_name") != self.source_channel_name:
            raise SourceError(f"Fast TV channel identity changed: {self.source_channel_id}")
        stream = matches[0].get("channel_url", "")
        stream = parse_qs(urlparse(stream).query).get("stream_url", [stream])[0]
        if stream != self.playlist_stream_url:
            raise SourceError(f"Fast TV stream changed: {self.source_channel_id}")

        payload = self._get(self.base + "getWebProgramList/" + self.source_channel_id)
        rows = payload.get("epgs")
        if not isinstance(rows, list):
            raise SourceError(f"Fast TV has no guide for {self.source_channel_id}")
        limit = now.astimezone(JST) + timedelta(days=days, hours=5)
        programmes = []
        for row in rows:
            try:
                start = datetime.fromtimestamp(row["starttime"], timezone.utc).astimezone(JST)
                stop = datetime.fromtimestamp(row["endtime"], timezone.utc).astimezone(JST)
                title = " ".join(row["title"].split())
                asset_id = row["asset_id"]
            except (KeyError, TypeError, ValueError, OverflowError, AttributeError) as exc:
                raise SourceError(f"Fast TV has malformed guide data for {self.source_channel_id}") from exc
            if asset_id == "no_program_asset":
                continue
            if stop <= start or not title or not isinstance(asset_id, str) or not asset_id.startswith(self.source_channel_id.upper() + "_"):
                raise SourceError(f"Fast TV has invalid guide data for {self.source_channel_id}")
            if stop <= now or start >= limit:
                continue
            description = " ".join((row.get("description") or "").split())
            programmes.append(Programme(channel_id=channel_id, start=start, stop=stop,
                                         title_ja=title, description_ja=description,
                                         source_id=asset_id, source_url="https://fastv.jp/"))
        programmes.sort(key=lambda p: (p.start, p.stop))
        if len(programmes) < 3 or programmes[0].start > now + timedelta(hours=6) or programmes[-1].stop < now + timedelta(hours=2):
            raise SourceError(f"Fast TV has insufficient current/future guide for {self.source_channel_id}")
        for current, following in zip(programmes, programmes[1:]):
            if current.stop > following.start:
                raise SourceError(f"Fast TV has overlapping guide entries for {self.source_channel_id}")
        return programmes
