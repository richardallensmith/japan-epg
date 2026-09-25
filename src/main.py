from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .fetch.bangumi import BangumiSource
from .fetch.nhk import NHKTimetableSource
from .models import XmltvChannel
from .normalize import deduplicate
from .playlist import find_channel, load_playlist
from .translate import TranslationEngine, load_json_yaml
from .validate import validate_feed
from .xmltv import build_xmltv, write_xmltv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAYLIST = "https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u"


def build(args: argparse.Namespace) -> dict:
    all_configs = load_json_yaml(ROOT / "config/channels.yaml")["channels"]
    selected_keys = set(args.channel or [])
    configs = {
        key: value
        for key, value in all_configs.items()
        if value.get("enabled", True) and (not selected_keys or key in selected_keys)
    }
    unknown = selected_keys - set(all_configs)
    if unknown:
        raise RuntimeError(f"Unknown channel config key(s): {', '.join(sorted(unknown))}")
    if not configs:
        raise RuntimeError("No enabled channels selected")
    playlist_channels = load_playlist(args.playlist)
    now = datetime.now(timezone.utc)
    programmes = []
    xmltv_channels: list[XmltvChannel] = []
    expected_ids: set[str] = set()
    playlist_ids: set[str] = set()
    source_names: set[str] = set()
    for key, config in configs.items():
        playlist_channel = find_channel(playlist_channels, name=config["playlist_name"])
        expected_id = config["expected_tvg_id"]
        if playlist_channel.tvg_id != expected_id:
            raise RuntimeError(
                f"Playlist changed for {key}: tvg-id is {playlist_channel.tvg_id!r}, expected {expected_id!r}. "
                "Refusing to generate a mismatched feed."
            )
        source_factories = {"nhk": NHKTimetableSource, "bangumi": BangumiSource}
        try:
            source = source_factories[config["source"]](**config["source_options"])
        except KeyError as exc:
            raise RuntimeError(f"Unsupported source {config['source']!r} for {key}") from exc
        source_names.add(source.name)
        programmes.extend(source.fetch(channel_id=playlist_channel.tvg_id, now=now, days=args.days))
        expected_ids.add(expected_id)
        playlist_ids.add(playlist_channel.tvg_id)
        xmltv_channels.append(
            XmltvChannel(
                channel_id=playlist_channel.tvg_id,
                display_name_en=config["display_name_en"],
                display_name_ja=config["display_name_ja"],
                icon_url=playlist_channel.tvg_logo,
            )
        )
    programmes = deduplicate(programmes)
    translator = TranslationEngine(
        title_overrides_path=ROOT / "config/title_overrides.yaml",
        translation_overrides_path=ROOT / "config/translation_overrides.yaml",
        cache_path=ROOT / "cache/translations.json",
        description_limit=args.description_chars,
    )
    translator.enrich(programmes)

    tree = build_xmltv(
        programmes,
        channels=xmltv_channels,
    )
    output_path = ROOT / args.output
    write_xmltv(tree, output_path)
    result = validate_feed(
        output_path,
        expected_channel_ids=expected_ids,
        playlist_channel_ids=playlist_ids,
        now=now,
    )
    result.update(
        {
            "channel_ids": sorted(expected_ids),
            "sources": sorted(source_names),
            "output": str(output_path),
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an English-first Japanese XMLTV feed")
    parser.add_argument("--playlist", default=DEFAULT_PLAYLIST)
    parser.add_argument(
        "--channel",
        action="append",
        help="Channel config key to build; repeat for multiple. Defaults to every enabled channel.",
    )
    parser.add_argument("--days", type=int, default=1, help="Upcoming days to retain (default: 1)")
    parser.add_argument("--description-chars", type=int, default=48, help="Japanese characters sent for English summary MT")
    parser.add_argument("--output", default="output/epg.xml")
    args = parser.parse_args()
    result = build(args)
    def printable(value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: printable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [printable(item) for item in value]
        return value

    printable = printable(result)
    print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
