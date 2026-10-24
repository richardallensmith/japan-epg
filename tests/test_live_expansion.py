"""Pinned identities and offline source rows from the 2026-10-25 live run."""
import io
import json
import unittest
from datetime import datetime
from html import escape
from pathlib import Path
from unittest.mock import patch

from src.fetch.bangumi import BangumiSource, _BangumiParser, JST
from src.fetch.base import SourceError
from src.fetch.nhk_world import NHKWorldSource
from src.models import XmltvChannel
from src.playlist import load_playlist
from src.translate import load_json_yaml
from src.validate import validate_feed
from src.xmltv import build_xmltv

ROOT = Path(__file__).resolve().parents[1]


class ShoppingMappingTests(unittest.TestCase):
    def test_cs_shopping_rows_match_exact_playlist_ids_and_services(self):
        fixture = load_json_yaml(ROOT / 'tests/fixtures/live_shopping_rows.json')
        configs = load_json_yaml(ROOT / 'config/channels.yaml')['channels']
        playlist = {c.name: c for c in load_playlist(str(ROOT / 'output/japan-live.m3u'))}
        html = '<div id="ch_area">' + ''.join(f'<p>{escape(n)}</p>' for n in fixture['channel_names']) + '</div>'
        for channel in fixture['channels']:
            html += f'<ul id="program_line_{channel["station_line"]}">'
            for row in channel['rows']:
                html += (f'<li s="{row["start"]}" e="{row["stop"]}" se-id="{row["source_id"]}">'
                         f'<p class="program_title">{escape(row["title"])}</p>'
                         f'<p class="program_detail">{escape(row["description"])}</p></li>')
            html += '</ul>'
        page = _BangumiParser()
        page.feed(html)
        for row in fixture['channels']:
            with self.subTest(channel=row['playlist_name']):
                config = configs[row['config_key']]
                self.assertEqual(row['tvg_id'], playlist[row['playlist_name']].tvg_id)
                self.assertEqual(row['tvg_id'], config['expected_tvg_id'])
                self.assertEqual(row['station_id'], config['source_options']['station_id'])
                programmes = BangumiSource(**config['source_options'])._parse(page, row['tvg_id'], '20261025')
                self.assertEqual(3, len(programmes))
                self.assertTrue(all(p.source_id.startswith(row['station_id'] + '-') for p in programmes))
                self.assertEqual(row['rows'][0]['title'], programmes[0].title_ja)
                changed = dict(config['source_options'], station_id='999')
                with self.assertRaisesRegex(SourceError, 'service ID changed'):
                    BangumiSource(**changed)._parse(page, row['tvg_id'], '20261025')


class NHKWorldMappingTests(unittest.TestCase):
    def test_official_english_rows_preserve_language_and_times(self):
        fixture = load_json_yaml(ROOT / 'tests/fixtures/nhk_world_rows.json')
        configs = load_json_yaml(ROOT / 'config/channels.yaml')['channels']
        config = configs['nhk_world_japan']
        playlist = {c.name: c for c in load_playlist(str(ROOT / 'output/japan-live.m3u'))}
        self.assertEqual(playlist[config['playlist_name']].tvg_id, config['expected_tvg_id'])
        with patch('src.fetch.nhk_world.urlopen', return_value=io.BytesIO(json.dumps(fixture).encode())):
            programmes = NHKWorldSource().fetch(
                channel_id=config['expected_tvg_id'], now=datetime(2026, 10, 25, 3, 55, tzinfo=JST), days=0)
        self.assertEqual(3, len(programmes))
        self.assertEqual('Manben: Behind the Scenes of Manga with Urasawa Naoki: Sugimura Shinichi', programmes[1].title_en)
        self.assertEqual('', programmes[1].title_ja)
        self.assertEqual(fixture['data'][1]['description'], programmes[1].description_en)
        tree = build_xmltv(programmes, channels=[XmltvChannel(config['expected_tvg_id'], 'NHK WORLD-JAPAN', 'NHK WORLD-JAPAN')])
        self.assertIsNone(tree.find("programme/title[@lang='ja']"))
        result = validate_feed(tree, expected_channel_ids={config['expected_tvg_id']},
                               playlist_channel_ids={config['expected_tvg_id']},
                               now=datetime(2026, 10, 25, 3, 55, tzinfo=JST), min_future_hours=0,
                               min_programmes=3)
        self.assertEqual(3, result['programmes'])


if __name__ == '__main__':
    unittest.main()
