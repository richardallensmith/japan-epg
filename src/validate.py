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
    expected_channel_ids: set[str],
    playlist_channel_ids: set[str],
    now: datetime | None = None,
    min_future_hours: float = 2.0,
    min_programmes: int = 3,
) -> dict:
    if expected_channel_ids != playlist_channel_ids:
        raise ValidationError(
            f"Configured channel ids {sorted(expected_channel_ids)!r} do not match playlist ids "
            f"{sorted(playlist_channel_ids)!r}"
        )
    tree = ET.parse(source) if isinstance(source, Path) else source
    root = tree.getroot()
    if root.tag != "tv":
        raise ValidationError("Document root is not <tv>")
    channel_ids = [element.get("id") for element in root.findall("channel")]
    if set(channel_ids) != expected_channel_ids:
        raise ValidationError(
            f"XMLTV channel ids {sorted(channel_ids)!r} do not match expected ids {sorted(expected_channel_ids)!r}"
        )
    if len(channel_ids) != len(set(channel_ids)):
        raise ValidationError("Duplicate <channel> entries")

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    seen: set[tuple[str, str, str, str]] = set()
    current_or_future = {channel_id: 0 for channel_id in expected_channel_ids}
    per_channel_count = {channel_id: 0 for channel_id in expected_channel_ids}
    per_channel_stops: dict[str, list[datetime]] = {channel_id: [] for channel_id in expected_channel_ids}
    per_channel_starts = {channel_id: [] for channel_id in expected_channel_ids}
    per_channel_titles = {channel_id: set() for channel_id in expected_channel_ids}
    starts: list[datetime] = []
    stops: list[datetime] = []
    bilingual_titles = 0
    bilingual_descriptions = 0
    for element in root.findall("programme"):
        channel = element.get("channel", "")
        if channel not in expected_channel_ids:
            raise ValidationError(f"Programme references unexpected channel {channel!r}")
        start = parse_xmltv_timestamp(element.get("start", ""))
        stop = parse_xmltv_timestamp(element.get("stop", ""))
        if any(not element.get(field, "").endswith(" +0900") for field in ("start", "stop")):
            raise ValidationError("Programme timestamps must use +0900 Japan time")
        if stop <= start:
            raise ValidationError(f"Programme stop is not after start: {start} / {stop}")
        ja_title = element.findtext("title[@lang='ja']", default="")
        en_title = element.findtext("title[@lang='en']", default="")
        if not ja_title.strip() or not en_title.strip():
            raise ValidationError("Every programme must have non-empty English and Japanese titles")
        key = (channel, element.get("start", ""), element.get("stop", ""), ja_title)
        if key in seen:
            raise ValidationError(f"Duplicate programme entry: {key}")
        seen.add(key)
        per_channel_count[channel] += 1
        per_channel_stops[channel].append(stop)
        per_channel_starts[channel].append(start)
        per_channel_titles[channel].add(ja_title.strip())
        if stop > now:
            current_or_future[channel] += 1
        starts.append(start)
        stops.append(stop)
        bilingual_titles += 1
        ja_description = element.findtext("desc[@lang='ja']", default="").strip()
        en_description = element.findtext("desc[@lang='en']", default="").strip()
        if bool(ja_description) != bool(en_description):
            raise ValidationError("Source descriptions must retain both Japanese and English text")
        if ja_description and en_description:
            bilingual_descriptions += 1

    if not starts:
        raise ValidationError("Channel exists but has zero programme entries")
    for channel_id in sorted(expected_channel_ids):
        if per_channel_count[channel_id] == 0:
            raise ValidationError(f"Channel {channel_id!r} exists but has zero programme entries")
        if per_channel_count[channel_id] < min_programmes:
            raise ValidationError(f"Channel {channel_id!r} has too few meaningful programme entries")
        if per_channel_titles[channel_id] <= {'休止', '放送休止', '番組情報がありません', '未定', '番組未定'}:
            raise ValidationError(f"Channel {channel_id!r} contains only schedule placeholders")
        if min(per_channel_starts[channel_id]) > now + timedelta(hours=6):
            raise ValidationError(f"Channel {channel_id!r} has no listings near the current time")
        intervals = sorted(zip(per_channel_starts[channel_id], per_channel_stops[channel_id]))
        if any(start < previous_stop for (_, previous_stop), (start, _) in zip(intervals, intervals[1:])):
            raise ValidationError(f"Channel {channel_id!r} has overlapping or conflicting programme entries")
        if current_or_future[channel_id] == 0:
            raise ValidationError(f"Channel {channel_id!r} has zero current/future programme entries")
        latest = max(per_channel_stops[channel_id])
        if latest < now + timedelta(hours=min_future_hours):
            raise ValidationError(
                f"Schedule for {channel_id!r} is suspiciously stale/short: latest stop {latest.isoformat()} "
                f"is less than {min_future_hours:g} hours ahead"
            )
    return {
        "programmes": len(starts),
        "current_or_future": sum(current_or_future.values()),
        "earliest": min(starts),
        "latest": max(stops),
        "bilingual_titles": bilingual_titles,
        "bilingual_descriptions": bilingual_descriptions,
        "per_channel": {
            channel_id: {
                "programmes": per_channel_count[channel_id],
                "current_or_future": current_or_future[channel_id],
                "latest": max(per_channel_stops[channel_id]),
                "earliest": min(per_channel_starts[channel_id]),
            }
            for channel_id in sorted(expected_channel_ids)
        },
    }
