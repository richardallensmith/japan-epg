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
from src.fetch.weathernews import WeathernewsSource
from src.fetch.skyperfectv import SkyPerfectVSource
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


class WeathernewsMappingTests(unittest.TestCase):
    def test_official_rolling_timetable_matches_live_identity_and_crosses_midnight(self):
        fixture = load_json_yaml(ROOT / 'tests/fixtures/weathernews_rows.json')
        config = load_json_yaml(ROOT / 'config/channels.yaml')['channels']['weather_news']
        playlist = {c.name: c for c in load_playlist(str(ROOT / 'output/japan-live.m3u'))}
        self.assertEqual('rch_45', playlist[config['playlist_name']].tvg_id)
        self.assertEqual('rch_45', config['expected_tvg_id'])
        now = datetime(2026, 10, 26, 14, 42, tzinfo=JST)
        with patch('src.fetch.weathernews.urlopen', return_value=io.BytesIO(json.dumps(fixture).encode())):
            programmes = WeathernewsSource().fetch(channel_id='rch_45', now=now, days=2)
        self.assertEqual(len(fixture) - 1, len(programmes))
        self.assertEqual(datetime(2026, 10, 26, 14, tzinfo=JST), programmes[0].start)
        self.assertEqual(datetime(2026, 10, 27, 0, tzinfo=JST), programmes[3].stop)
        self.assertEqual(fixture[0]['title'], programmes[0].title_ja)
        self.assertTrue(all(p.channel_id == 'rch_45' and p.stop > p.start for p in programmes))
        for programme in programmes:
            programme.title_en = programme.title_ja
        tree = build_xmltv(programmes, channels=[XmltvChannel('rch_45', 'Weathernews LiVE', 'ウェザーニュースLiVE')])
        validate_feed(tree, expected_channel_ids={'rch_45'}, playlist_channel_ids={'rch_45'}, now=now)


class GSTVCSMappingTests(unittest.TestCase):
    def test_sky_guide_uses_exact_cs527_identity_and_midnight_date(self):
        config = load_json_yaml(ROOT / 'config/channels.yaml')['channels']['gstv_cs']
        playlist = {c.name: c for c in load_playlist(str(ROOT / 'output/japan-live.m3u'))}
        self.assertEqual('CH.527', playlist[config['playlist_name']].tvg_id)
        self.assertEqual('CH.527', config['expected_tvg_id'])
        html = '<meta content="https://www.skyperfectv.co.jp/program/schedule/premium/channel%3A527/"><title>ジュエリー☆ＧＳＴＶ</title>'
        html += '<div class="p-schedule__hdr" data-date="2026-10-26"></div>'
        html += '<div class="p-schedule__hdr" data-date="2026-10-27"></div>'
        html += '<tr id="js-pm"><td>'
        for time_range, title in [('22:00〜23:00', 'ジュエリー特集'), ('23:00〜00:00', '麗しの宝石ショッピング')]:
            html += f'<li class="p-program__item"><p class="p-program__range">{time_range}</p><p class="p-program__name">{title}</p></li>'
        html += '</td><td></td></tr><tr id="js-md"><td>'
        for time_range in ['00:00〜02:00', '02:00〜03:00', '03:00〜04:00']:
            html += f'<li class="p-program__item"><p class="p-program__range">{time_range}</p><p class="p-program__name">GSTVリピート放送</p></li>'
        html += '</td><td></td></tr>'
        now = datetime(2026, 10, 26, 22, 30, tzinfo=JST)
        with patch('src.fetch.skyperfectv.urlopen', return_value=io.BytesIO(html.encode())):
            programmes = SkyPerfectVSource().fetch(channel_id='CH.527', now=now, days=2)
        self.assertEqual(5, len(programmes))
        self.assertEqual(datetime(2026, 10, 27, 0, tzinfo=JST), programmes[2].start)
        self.assertEqual(datetime(2026, 10, 27, 4, tzinfo=JST), programmes[-1].stop)
        self.assertTrue(all(p.channel_id == 'CH.527' for p in programmes))


if __name__ == '__main__':
    unittest.main()
