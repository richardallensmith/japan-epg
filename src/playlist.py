from __future__ import annotations

import re
from pathlib import Path
from urllib.request import Request, urlopen

from .models import PlaylistChannel

ATTRIBUTE_RE = re.compile(r'([\w-]+)="([^"]*)"')


class PlaylistError(RuntimeError):
    pass


def download_text(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="strict")


def parse_m3u(text: str) -> list[PlaylistChannel]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    channels: list[PlaylistChannel] = []
    pending: tuple[dict[str, str], str] | None = None
    for line in lines:
        if line.startswith("#EXTINF:"):
            attrs = dict(ATTRIBUTE_RE.findall(line))
            name = line.rsplit(",", 1)[-1].strip()
            pending = (attrs, name)
        elif not line.startswith("#") and pending:
            attrs, name = pending
            channels.append(
                PlaylistChannel(
                    name=name,
                    url=line,
                    tvg_id=attrs.get("tvg-id", ""),
                    tvg_name=attrs.get("tvg-name", ""),
                    tvg_logo=attrs.get("tvg-logo", ""),
                    group_title=attrs.get("group-title", ""),
                )
            )
            pending = None
    if not channels:
        raise PlaylistError("Playlist contained no #EXTINF channel entries")
    return channels


def load_playlist(location: str) -> list[PlaylistChannel]:
    if location.startswith(("http://", "https://")):
        return parse_m3u(download_text(location))
    return parse_m3u(Path(location).read_text(encoding="utf-8"))


def find_channel(channels: list[PlaylistChannel], *, name: str) -> PlaylistChannel:
    matches = [c for c in channels if c.name == name or c.tvg_name == name]
    if len(matches) != 1:
        raise PlaylistError(f"Expected exactly one playlist channel named {name!r}; found {len(matches)}")
    if not matches[0].tvg_id:
        raise PlaylistError(f"Playlist channel {name!r} has no tvg-id")
    return matches[0]
