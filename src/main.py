from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .fetch.nhk import NHKTimetableSource
from .normalize import deduplicate
from .playlist import find_channel, load_playlist
from .translate import TranslationEngine, load_json_yaml
from .validate import validate_feed
from .xmltv import build_xmltv, write_xmltv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAYLIST = "https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u"


def build(args: argparse.Namespace) -> dict:
    config = load_json_yaml(ROOT / "config/channels.yaml")["channels"]["nhk_g_tokyo"]
    playlist_channels = load_playlist(args.playlist)
    playlist_channel = find_channel(playlist_channels, name=config["playlist_name"])
    expected_id = config["expected_tvg_id"]
    if playlist_channel.tvg_id != expected_id:
        raise RuntimeError(
            f"Playlist changed: NHK G tvg-id is {playlist_channel.tvg_id!r}, expected {expected_id!r}. "
            "Refusing to generate a mismatched feed."
        )

    now = datetime.now(timezone.utc)
    source = NHKTimetableSource(**config["source_options"])
    programmes = deduplicate(source.fetch(channel_id=playlist_channel.tvg_id, now=now, days=args.days))
    translator = TranslationEngine(
        title_overrides_path=ROOT / "config/title_overrides.yaml",
        translation_overrides_path=ROOT / "config/translation_overrides.yaml",
        cache_path=ROOT / "cache/translations.json",
        description_limit=args.description_chars,
    )
    translator.enrich(programmes)

    tree = build_xmltv(
        programmes,
        channel_id=playlist_channel.tvg_id,
        display_name_en=config["display_name_en"],
        display_name_ja=config["display_name_ja"],
        icon_url=playlist_channel.tvg_logo,
    )
    output_path = ROOT / args.output
    write_xmltv(tree, output_path)
    result = validate_feed(
        output_path,
        expected_channel_id=expected_id,
        playlist_channel_id=playlist_channel.tvg_id,
        now=now,
    )
    result.update(
        {
            "channel_id": playlist_channel.tvg_id,
            "source": source.name,
            "output": str(output_path),
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an English-first Japanese XMLTV feed")
    parser.add_argument("--playlist", default=DEFAULT_PLAYLIST)
    parser.add_argument("--days", type=int, default=1, help="Upcoming days to retain (default: 1)")
    parser.add_argument("--description-chars", type=int, default=48, help="Japanese characters sent for English summary MT")
    parser.add_argument("--output", default="output/epg.xml")
    args = parser.parse_args()
    result = build(args)
    printable = {key: value.isoformat() if isinstance(value, datetime) else value for key, value in result.items()}
    print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
