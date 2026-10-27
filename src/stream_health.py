from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ATTRIBUTE_RE = re.compile(r'([\w-]+)="([^"]*)"')
USER_AGENT = "Japan-EPG/1.0 (+stream health checker)"


@dataclass(frozen=True)
class StreamEntry:
    key: str
    name: str
    url: str
    tvg_id: str
    tvg_name: str
    tvg_logo: str
    group_title: str
    extinf: str


@dataclass(frozen=True)
class ProbeResult:
    key: str
    passed: bool
    media: tuple[str, ...]
    elapsed_seconds: float
    error: str = ""


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def download_text(url: str, timeout: int = 30) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _stable_keys(raw_entries: list[dict[str, str]]) -> list[str]:
    tvg_counts: dict[str, int] = {}
    name_counts: dict[tuple[str, str], int] = {}
    for item in raw_entries:
        if item["tvg_id"]:
            tvg_counts[item["tvg_id"]] = tvg_counts.get(item["tvg_id"], 0) + 1
        pair = (item["group_title"], item["name"])
        name_counts[pair] = name_counts.get(pair, 0) + 1

    keys: list[str] = []
    for item in raw_entries:
        tvg_id = item["tvg_id"]
        pair = (item["group_title"], item["name"])
        if tvg_id and tvg_counts[tvg_id] == 1:
            keys.append(f"tvg:{tvg_id}")
        elif name_counts[pair] == 1:
            digest = hashlib.sha256(("\0".join(pair)).encode("utf-8")).hexdigest()[:16]
            keys.append(f"name:{digest}")
        else:
            digest = hashlib.sha256(
                ("\0".join((item["group_title"], item["name"], item["url"]))).encode("utf-8")
            ).hexdigest()[:16]
            keys.append(f"url:{digest}")
    return keys


def parse_playlist(text: str) -> tuple[str, list[StreamEntry]]:
    lines = [line.rstrip("\r") for line in text.splitlines()]
    header = next((line for line in lines if line.startswith("#EXTM3U")), "#EXTM3U")
    raw_entries: list[dict[str, str]] = []
    pending: str | None = None

    for raw in lines:
        line = raw.strip()
        if line.startswith("#EXTINF:"):
            pending = raw
            continue
        if pending is not None and line and not line.startswith("#"):
            attrs = dict(ATTRIBUTE_RE.findall(pending))
            raw_entries.append(
                {
                    "name": pending.rsplit(",", 1)[-1].strip(),
                    "url": line,
                    "tvg_id": attrs.get("tvg-id", ""),
                    "tvg_name": attrs.get("tvg-name", ""),
                    "tvg_logo": attrs.get("tvg-logo", ""),
                    "group_title": attrs.get("group-title", ""),
                    "extinf": pending,
                }
            )
            pending = None

    if not raw_entries:
        raise RuntimeError("Playlist contained no #EXTINF channel entries")

    keys = _stable_keys(raw_entries)
    entries = [
        StreamEntry(key=key, **item)
        for key, item in zip(keys, raw_entries, strict=True)
    ]
    return header, entries


def probe(entry: StreamEntry, *, timeout_seconds: int, rw_timeout_microseconds: int) -> ProbeResult:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-rw_timeout",
                str(rw_timeout_microseconds),
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
                entry.url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        elapsed = time.monotonic() - started
        media = tuple(
            row.strip()
            for row in proc.stdout.splitlines()
            if row.strip() in {"audio", "video"}
        )
        passed = bool(media)
        error = "" if passed else proc.stderr.strip().replace("\n", " ")[:500]
        return ProbeResult(entry.key, passed, media, elapsed, error)
    except subprocess.TimeoutExpired:
        return ProbeResult(entry.key, False, (), float(timeout_seconds), "TIMEOUT")


def probe_all(
    entries: list[StreamEntry],
    *,
    workers: int,
    timeout_seconds: int,
    rw_timeout_microseconds: int,
) -> dict[str, ProbeResult]:
    results: dict[str, ProbeResult] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                probe,
                entry,
                timeout_seconds=timeout_seconds,
                rw_timeout_microseconds=rw_timeout_microseconds,
            ): entry
            for entry in entries
        }
        for future in as_completed(futures):
            result = future.result()
            results[result.key] = result
    return results


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def make_record(entry: StreamEntry, now: str, *, bootstrap: bool) -> dict:
    return {
        "tvg_id": entry.tvg_id,
        "name": entry.name,
        "url": entry.url,
        "group_title": entry.group_title,
        "state": "healthy" if bootstrap else "new",
        "present_upstream": True,
        "grandfathered": bootstrap,
        "ever_succeeded": False,
        "first_seen_at": now,
        "last_seen_upstream_at": now,
        "last_checked_at": None,
        "last_success_at": None,
        "last_failure_at": None,
        "consecutive_failures": 0,
        "consecutive_successes": 0,
        "last_result": None,
        "last_error": None,
    }


def reconcile_inventory(state: dict, entries: list[StreamEntry], now: str, *, bootstrap: bool) -> None:
    records = state.setdefault("channels", {})
    current_keys = {entry.key for entry in entries}

    for key, record in records.items():
        if key not in current_keys:
            record["present_upstream"] = False
            record["state"] = "upstream_removed"

    for entry in entries:
        record = records.get(entry.key)
        if record is None:
            record = make_record(entry, now, bootstrap=bootstrap)
            records[entry.key] = record
        record.update(
            {
                "tvg_id": entry.tvg_id,
                "name": entry.name,
                "url": entry.url,
                "group_title": entry.group_title,
                "present_upstream": True,
                "last_seen_upstream_at": now,
            }
        )
        if record.get("state") == "upstream_removed":
            record["state"] = "new"
            record["grandfathered"] = False
            record["consecutive_failures"] = 0
            record["consecutive_successes"] = 0


def should_suppress_mass_failure(
    state: dict,
    results: dict[str, ProbeResult],
    *,
    threshold: float,
    minimum_baseline: int,
) -> tuple[bool, int, int, float]:
    baseline = []
    for key, record in state.get("channels", {}).items():
        if (
            record.get("present_upstream")
            and record.get("ever_succeeded")
            and record.get("state") in {"healthy", "suspect"}
            and key in results
        ):
            baseline.append(key)

    if len(baseline) < minimum_baseline:
        return False, len(baseline), 0, 0.0

    failed = sum(1 for key in baseline if not results[key].passed)
    ratio = failed / len(baseline)
    return ratio > threshold, len(baseline), failed, ratio


def apply_results(
    state: dict,
    results: dict[str, ProbeResult],
    *,
    now: str,
    suspect_after: int,
    remove_after: int,
    restore_after: int,
    new_successes_required: int,
    suppress_failures: bool,
) -> list[dict]:
    changes: list[dict] = []
    records = state["channels"]

    for key, result in results.items():
        record = records[key]
        before = record["state"]
        record["last_checked_at"] = now
        record["last_result"] = "pass" if result.passed else "fail"
        record["last_error"] = result.error or None
        record["last_probe_seconds"] = round(result.elapsed_seconds, 3)
        record["last_media"] = list(result.media)

        if result.passed:
            record["ever_succeeded"] = True
            record["last_success_at"] = now
            record["consecutive_failures"] = 0
            record["consecutive_successes"] = int(record.get("consecutive_successes", 0)) + 1

            if before == "removed":
                if record["consecutive_successes"] >= restore_after:
                    record["state"] = "healthy"
                    record["grandfathered"] = False
            elif before == "new":
                if record["consecutive_successes"] >= new_successes_required:
                    record["state"] = "healthy"
                    record["grandfathered"] = False
            else:
                record["state"] = "healthy"
                record["grandfathered"] = False
        else:
            record["last_failure_at"] = now
            record["consecutive_successes"] = 0
            if not suppress_failures:
                record["consecutive_failures"] = int(record.get("consecutive_failures", 0)) + 1
                failures = record["consecutive_failures"]
                if before in {"healthy", "suspect"}:
                    if failures >= remove_after:
                        record["state"] = "removed"
                    elif failures >= suspect_after:
                        record["state"] = "suspect"
                elif before == "removed":
                    record["state"] = "removed"
                elif before == "new":
                    record["state"] = "new"

        after = record["state"]
        if before != after:
            changes.append({"key": key, "name": record["name"], "from": before, "to": after})

    return changes


def publishable_keys(state: dict) -> set[str]:
    return {
        key
        for key, record in state.get("channels", {}).items()
        if record.get("present_upstream") and record.get("state") in {"healthy", "suspect"}
    }


def reviewed_display_names(path: Path) -> dict[str, str]:
    """Return reviewed English-first visible names keyed by tvg-id."""
    data = load_json(path, {})
    overrides: dict[str, str] = {}
    for config in data.get("channels", {}).values():
        if not config.get("enabled", True):
            continue
        tvg_id = config.get("expected_tvg_id", "")
        english = (config.get("display_name_en") or "").strip()
        original = (config.get("playlist_name") or "").strip()
        if not tvg_id or not english:
            continue
        if original and original != english and any(ord(ch) > 127 for ch in original):
            overrides[tvg_id] = f"{english} ({original})"
        else:
            overrides[tvg_id] = english
    return overrides


def _visible_extinf(extinf: str, visible_name: str) -> str:
    prefix, separator, _ = extinf.rpartition(",")
    return f"{prefix}{separator}{visible_name}" if separator else extinf


def render_playlist(
    header: str,
    entries: list[StreamEntry],
    allowed: set[str],
    name_overrides: dict[str, str] | None = None,
) -> str:
    lines = [header]
    overrides = name_overrides or {}
    for entry in entries:
        if entry.key in allowed:
            visible_name = overrides.get(entry.tvg_id)
            extinf = _visible_extinf(entry.extinf, visible_name) if visible_name else entry.extinf
            lines.extend(["", extinf, entry.url])
    return "\n".join(lines).rstrip() + "\n"


def render_report(state: dict, changes: list[dict]) -> str:
    records = state.get("channels", {})
    counts: dict[str, int] = {}
    for record in records.values():
        state_name = record.get("state", "unknown")
        counts[state_name] = counts.get(state_name, 0) + 1

    run = state["last_run"]
    lines = [
        "# Japan IPTV Stream Health",
        "",
        f"- Updated: {state['updated_at']}",
        f"- Run status: {run['status']}",
        f"- Upstream channels: {run['upstream_channels']}",
        f"- Checked: {run['checked']}",
        f"- Passed: {run['passed']}",
        f"- Failed: {run['failed']}",
        f"- Published: {run['published']}",
        f"- Healthy: {counts.get('healthy', 0)}",
        f"- Suspect: {counts.get('suspect', 0)}",
        f"- Removed: {counts.get('removed', 0)}",
        f"- New/unverified: {counts.get('new', 0)}",
        f"- Upstream removed: {counts.get('upstream_removed', 0)}",
        f"- Mass-failure suppression: {'yes' if run['suppressed'] else 'no'}",
    ]
    if run.get("baseline_size"):
        lines.append(
            f"- Proven-good baseline failures: {run['baseline_failures']}/{run['baseline_size']} "
            f"({run['baseline_failure_ratio']:.1%})"
        )

    lines.extend(["", "## Status changes", ""])
    if changes:
        for change in changes:
            lines.append(f"- {change['name']}: {change['from']} -> {change['to']}")
    else:
        lines.append("- None")

    problem_records = [
        record
        for record in records.values()
        if record.get("present_upstream") and record.get("state") in {"suspect", "removed"}
    ]
    lines.extend(["", "## Current suspect/removed channels", ""])
    if problem_records:
        for record in sorted(problem_records, key=lambda item: (item["state"], item["name"])):
            suffix = f" - {record.get('last_error')}" if record.get("last_error") else ""
            lines.append(
                f"- [{record['state']}] {record['name']} "
                f"(failures: {record.get('consecutive_failures', 0)}){suffix}"
            )
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"


def run(args: argparse.Namespace) -> dict:
    config = load_json(Path(args.config), {})
    source_playlist = args.playlist or config["source_playlist"]
    workers = args.workers or int(config["workers"])
    timeout_seconds = int(config["probe_timeout_seconds"])
    rw_timeout = int(config["ffprobe_rw_timeout_microseconds"])

    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is not installed or not present in PATH")

    text = download_text(source_playlist)
    header, entries = parse_playlist(text)

    state_path = Path(args.state)
    previous = load_json(state_path, {})
    bootstrap = not previous.get("channels")
    state = previous or {
        "version": 1,
        "source_playlist": source_playlist,
        "channels": {},
    }

    started_at = utcnow_iso()
    reconcile_inventory(state, entries, started_at, bootstrap=bootstrap)
    results = probe_all(
        entries,
        workers=workers,
        timeout_seconds=timeout_seconds,
        rw_timeout_microseconds=rw_timeout,
    )

    suppressed, baseline_size, baseline_failures, baseline_ratio = should_suppress_mass_failure(
        state,
        results,
        threshold=float(config["mass_failure_threshold"]),
        minimum_baseline=int(config["mass_failure_minimum_baseline"]),
    )

    completed_at = utcnow_iso()
    changes = apply_results(
        state,
        results,
        now=completed_at,
        suspect_after=int(config["suspect_after_failures"]),
        remove_after=int(config["remove_after_failures"]),
        restore_after=int(config["restore_after_successes"]),
        new_successes_required=int(config["new_channel_successes_required"]),
        suppress_failures=suppressed,
    )

    allowed = publishable_keys(state)
    state["updated_at"] = completed_at
    state["source_playlist"] = source_playlist
    state["last_run"] = {
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "suppressed_mass_failure" if suppressed else "ok",
        "upstream_channels": len(entries),
        "checked": len(results),
        "passed": sum(1 for item in results.values() if item.passed),
        "failed": sum(1 for item in results.values() if not item.passed),
        "published": len(allowed),
        "suppressed": suppressed,
        "baseline_size": baseline_size,
        "baseline_failures": baseline_failures,
        "baseline_failure_ratio": baseline_ratio,
    }

    name_overrides = reviewed_display_names(ROOT / "config" / "channels.yaml")
    playlist_text = render_playlist(header, entries, allowed, name_overrides)
    report_text = render_report(state, changes)

    if not args.dry_run:
        save_json(state_path, state)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(playlist_text, encoding="utf-8")
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")

    summary = dict(state["last_run"])
    summary["bootstrap"] = bootstrap
    summary["changes"] = changes
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe and filter the Japan IPTV playlist")
    parser.add_argument("--config", default=str(ROOT / "config/stream_health_config.json"))
    parser.add_argument("--playlist", help="Override upstream playlist URL")
    parser.add_argument("--state", default=str(ROOT / "config/stream_health.json"))
    parser.add_argument("--output", default=str(ROOT / "output/japan-live.m3u"))
    parser.add_argument("--report", default=str(ROOT / "output/stream-health.md"))
    parser.add_argument("--workers", type=int, help="Override concurrent probe count")
    parser.add_argument("--dry-run", action="store_true", help="Probe without writing state or outputs")
    args = parser.parse_args()
    print(json.dumps(run(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
