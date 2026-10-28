"""Pinned R Channel identities and actual dated programme rows from 2026-10-27."""
import json
import unittest
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.fetch.base import SourceError
from src.fetch.rchannel import JST, RChannelSource
from src.playlist import load_playlist, find_configured_channel

ROOT = Path(__file__).resolve().parents[1]


class RChannelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads((ROOT / "tests/fixtures/rchannel_rows.json").read_text())
        cls.configs = json.loads((ROOT / "config/channels.yaml").read_text())["channels"]
        cls.playlist = load_playlist(str(ROOT / "output/japan-live.m3u"))

    def test_each_identity_has_current_source_programmes(self):
        now = datetime(2026, 10, 27, 0, 1, tzinfo=JST)
        with patch.object(RChannelSource, "_page", return_value=self.rows):
            for key, config in self.configs.items():
                if config["source"] != "rchannel" or config["source_options"]["source_channel_id"] not in {row["id"] for row in self.rows}:
                    continue
                with self.subTest(channel=key):
                    playlist = find_configured_channel(self.playlist, name=config["playlist_name"],
                                                       expected_id=config["expected_tvg_id"])
                    self.assertEqual(playlist.tvg_id, config["expected_tvg_id"])
                    source = RChannelSource(**config["source_options"], playlist_stream_url=playlist.url)
                    programmes = source.fetch(channel_id=playlist.tvg_id, now=now, days=1)
                    self.assertGreaterEqual(len(programmes), 3)
                    self.assertGreater(programmes[-1].stop, now)
                    self.assertTrue(all(p.channel_id == playlist.tvg_id for p in programmes))
                    field = "title_en" if config["source_options"].get("source_language") == "en" else "title_ja"
                    self.assertTrue(all(getattr(p, field) for p in programmes))
                    self.assertTrue(all(a.stop <= b.start for a, b in zip(programmes, programmes[1:])))

    def test_stream_or_source_id_change_is_rejected(self):
        config = self.configs["rchannel_ntv_news"]
        now = datetime(2026, 10, 27, 0, 1, tzinfo=JST)
        with patch.object(RChannelSource, "_page", return_value=self.rows):
            source = RChannelSource(**config["source_options"], playlist_stream_url="https://wrong.example/stream")
            with self.assertRaisesRegex(SourceError, "identity or stream changed"):
                source.fetch(channel_id="rch_47", now=now, days=1)
            playlist = find_configured_channel(self.playlist, name=config["playlist_name"],
                                               expected_id=config["expected_tvg_id"])
            source = RChannelSource(**config["source_options"], playlist_stream_url=playlist.url)
            with self.assertRaisesRegex(SourceError, "differs from playlist ID"):
                source.fetch(channel_id="rch_48", now=now, days=1)

    def test_material_source_overlap_is_rejected(self):
        rows = deepcopy(self.rows)
        channel = next(row for row in rows if row["id"] == 47)
        channel["programs"][0]["end"] = "2026-10-27T01:00:02.000+09:00"
        config = self.configs["rchannel_ntv_news"]
        playlist = find_configured_channel(self.playlist, name=config["playlist_name"],
                                           expected_id=config["expected_tvg_id"])
        source = RChannelSource(**config["source_options"], playlist_stream_url=playlist.url)
        with patch.object(RChannelSource, "_page", return_value=rows):
            with self.assertRaisesRegex(SourceError, "overlapping programmes"):
                source.fetch(channel_id="rch_47", now=datetime(2026, 10, 27, 0, 1, tzinfo=JST), days=1)

    def test_expansion_rows_pin_each_live_channel_and_stream(self):
        rows = json.loads((ROOT / "tests/fixtures/rchannel_expansion_rows.json").read_text())
        by_id = {row["id"]: row for row in rows}
        now = datetime(2026, 10, 28, 0, 1, tzinfo=JST)
        with patch.object(RChannelSource, "_page", return_value=rows):
            for key, config in self.configs.items():
                if config["source"] != "rchannel" or config["source_options"]["source_channel_id"] not in by_id:
                    continue
                with self.subTest(channel=key):
                    playlist = find_configured_channel(self.playlist, name=config["playlist_name"],
                                                       expected_id=config["expected_tvg_id"])
                    source = RChannelSource(**config["source_options"], playlist_stream_url=playlist.url)
                    programmes = source.fetch(channel_id=playlist.tvg_id, now=now, days=1)
                    self.assertGreaterEqual(len(programmes), 3)
                    self.assertEqual(by_id[config["source_options"]["source_channel_id"]]["programs"][0]["title"],
                                     programmes[0].title_ja)
                    with self.assertRaisesRegex(SourceError, "identity or stream changed"):
                        RChannelSource(**config["source_options"], playlist_stream_url="https://wrong.example/").fetch(
                            channel_id=playlist.tvg_id, now=now, days=1)


if __name__ == "__main__":
    unittest.main()
