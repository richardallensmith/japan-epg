"""Fast TV guide rows stay tied to their exact live playlist stream."""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from src.fetch.base import SourceError
from src.fetch.fastv import FastVSource
from src.playlist import load_playlist

ROOT = Path(__file__).resolve().parents[1]


class FastVSourceTests(unittest.TestCase):
    def setUp(self):
        fixture = json.loads((ROOT / "tests/fixtures/fastv_busns_rows.json").read_text())
        self.channel = fixture["channel"]
        self.rows = fixture["epgs"]
        self.now = datetime.fromtimestamp(self.rows[0]["starttime"] + 1, timezone.utc)
        self.source = FastVSource(source_channel_id="busns", source_channel_name="ビジネス",
                                  playlist_stream_url=self.channel["channel_url"])
        FastVSource._channels = None

    def test_exact_stream_and_current_programmes(self):
        playlist = load_playlist(str(ROOT / "output/japan-live.m3u"))
        live = next(row for row in playlist if row.tvg_id == "fastch_v2_busns")
        self.assertEqual(live.url, self.channel["channel_url"])
        with patch.object(self.source, "_get", side_effect=[
            {"error": 0, "channels": [self.channel]},
            {"error": 0, "epgs": self.rows},
        ]):
            result = self.source.fetch(channel_id=live.tvg_id, now=self.now, days=2)
        self.assertEqual(4, len(result))
        self.assertEqual(self.rows[0]["title"], result[0].title_ja)
        self.assertEqual(self.rows[-1]["endtime"], int(result[-1].stop.timestamp()))

    def test_changed_stream_is_rejected(self):
        changed = dict(self.channel, channel_url="https://example.invalid/other.m3u8")
        with patch.object(self.source, "_get", return_value={"error": 0, "channels": [changed]}):
            with self.assertRaisesRegex(SourceError, "stream changed"):
                self.source.fetch(channel_id="fastch_v2_busns", now=self.now, days=2)

    def test_public_ad_wrapper_resolves_to_exact_live_stream(self):
        wrapped = dict(self.channel, channel_url=(
            "https://ssai.gumgum.com/gs/stream/master/bbm/content.m3u8?stream_url="
            + quote(self.channel["channel_url"], safe="")))
        with patch.object(self.source, "_get", side_effect=[
            {"error": 0, "channels": [wrapped]},
            {"error": 0, "epgs": self.rows},
        ]):
            self.assertEqual(4, len(self.source.fetch(channel_id="fastch_v2_busns",
                                                        now=self.now, days=2)))

    def test_missing_programme_placeholder_is_excluded(self):
        placeholder = dict(self.rows[0], asset_id="no_program_asset", title="番組がありません。")
        with patch.object(self.source, "_get", side_effect=[
            {"error": 0, "channels": [self.channel]},
            {"error": 0, "epgs": [placeholder, *self.rows]},
        ]):
            result = self.source.fetch(channel_id="fastch_v2_busns", now=self.now, days=2)
        self.assertEqual(4, len(result))

    def test_expansion_feeds_pin_each_live_stream_and_current_guide(self):
        fixture = json.loads((ROOT / "tests/fixtures/fastv_expansion_2026-11-06.json").read_text())
        configs = json.loads((ROOT / "config/channels.yaml").read_text())["channels"]
        playlist = {row.tvg_id: row for row in load_playlist(str(ROOT / "output/japan-live.m3u"))}
        for item in fixture:
            channel = item["channel"]
            source_id = channel["channel_id"]
            tvg_id = "fastch_v2_" + source_id
            with self.subTest(channel=tvg_id):
                config = configs["fastv_" + source_id]
                self.assertTrue(config["enabled"])
                self.assertEqual(tvg_id, config["expected_tvg_id"])
                self.assertEqual(playlist[tvg_id].name, config["playlist_name"])
                self.assertEqual(playlist[tvg_id].url, channel["channel_url"])
                self.assertEqual(source_id, config["source_options"]["source_channel_id"])
                self.assertEqual(channel["channel_name"], config["source_options"]["source_channel_name"])
                now = datetime.fromtimestamp(item["epgs"][0]["starttime"] + 1, timezone.utc)
                FastVSource._channels = None
                source = FastVSource(**config["source_options"], playlist_stream_url=playlist[tvg_id].url)
                with patch.object(source, "_get", side_effect=[
                    {"error": 0, "channels": [channel]},
                    {"error": 0, "epgs": item["epgs"]},
                ]):
                    programmes = source.fetch(channel_id=tvg_id, now=now, days=2)
                self.assertGreaterEqual(len(programmes), 3)
                self.assertEqual(" ".join(item["epgs"][0]["title"].split()), programmes[0].title_ja)
                self.assertGreater(programmes[-1].stop, now)
                self.assertTrue(all(p.channel_id == tvg_id for p in programmes))
                FastVSource._channels = None
                wrong = FastVSource(**config["source_options"], playlist_stream_url="https://wrong.example/")
                with patch.object(wrong, "_get", return_value={"error": 0, "channels": [channel]}):
                    with self.assertRaisesRegex(SourceError, "stream changed"):
                        wrong.fetch(channel_id=tvg_id, now=now, days=2)


if __name__ == "__main__":
    unittest.main()
