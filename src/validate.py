from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^(\d{14}) ([+-]\d{4})$")


class ValidationError(RuntimeError):
    pass


def parse_xmltv_timestamp(value: str) -> datetime:
    if not TIMESTAMP_RE.fullmatch(value):
        raise ValidationError(f"Malformed XMLTV timestamp: {value!r}")
    try:
        return datetime.strptime(value, "%Y%m%d%H%M%S %z")
    except ValueError as exc:
        raise ValidationError(f"Malformed XMLTV timestamp: {value!r}") from exc


def validate_feed(
    source: Path | ET.ElementTree,
    *,
    expected_channel_id: str,
    playlist_channel_id: str,
    now: datetime | None = None,
    min_future_hours: float = 2.0,
) -> dict:
    if expected_channel_id != playlist_channel_id:
        raise ValidationError(
            f"Configured NHK G id {expected_channel_id!r} does not match playlist id {playlist_channel_id!r}"
        )
    tree = ET.parse(source) if isinstance(source, Path) else source
    root = tree.getroot()
    if root.tag != "tv":
        raise ValidationError("Document root is not <tv>")
    channel_ids = [element.get("id") for element in root.findall("channel")]
    if expected_channel_id not in channel_ids:
        raise ValidationError(f"Missing expected channel {expected_channel_id!r}")
    if len(channel_ids) != len(set(channel_ids)):
        raise ValidationError("Duplicate <channel> entries")

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    seen: set[tuple[str, str, str, str]] = set()
    current_or_future = 0
    starts: list[datetime] = []
    stops: list[datetime] = []
    bilingual_titles = 0
    bilingual_descriptions = 0
    for element in root.findall("programme"):
        channel = element.get("channel", "")
        if channel != expected_channel_id:
            raise ValidationError(f"Programme references unexpected channel {channel!r}")
        start = parse_xmltv_timestamp(element.get("start", ""))
        stop = parse_xmltv_timestamp(element.get("stop", ""))
        if stop <= start:
            raise ValidationError(f"Programme stop is not after start: {start} / {stop}")
        ja_title = element.findtext("title[@lang='ja']", default="")
        en_title = element.findtext("title[@lang='en']", default="")
        if not ja_title or not en_title:
            raise ValidationError("Every programme must have non-empty English and Japanese titles")
        key = (channel, element.get("start", ""), element.get("stop", ""), ja_title)
        if key in seen:
            raise ValidationError(f"Duplicate programme entry: {key}")
        seen.add(key)
        if stop > now:
            current_or_future += 1
        starts.append(start)
        stops.append(stop)
        bilingual_titles += 1
        if element.find("desc[@lang='ja']") is not None and element.find("desc[@lang='en']") is not None:
            bilingual_descriptions += 1

    if not starts:
        raise ValidationError("Channel exists but has zero programme entries")
    if current_or_future == 0:
        raise ValidationError("Channel exists but has zero current/future programme entries")
    if max(stops) < now + timedelta(hours=min_future_hours):
        raise ValidationError(
            f"Schedule is suspiciously stale/short: latest stop {max(stops).isoformat()} is less than "
            f"{min_future_hours:g} hours ahead"
        )
    return {
        "programmes": len(starts),
        "current_or_future": current_or_future,
        "earliest": min(starts),
        "latest": max(stops),
        "bilingual_titles": bilingual_titles,
        "bilingual_descriptions": bilingual_descriptions,
    }
