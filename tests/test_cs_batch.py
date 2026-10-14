"""Exact CS mappings and drift checks using rows captured from the live lineup.

Fixtures are for offline parser tests only; builds always fetch public sources.
"""
import json
import unittest
from datetime import datetime
from html import escape
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from src.fetch.base import SourceError
from src.fetch.bangumi import BangumiSource, JST, _BangumiParser
from src.models import PlaylistChannel
from src.playlist import find_channel

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'Toei Channel': ('CH.629', '218', 2),
    'Eisei Gekijo': ('CH.628', '219', 3),
    'Neco Channel': ('rch_59', '223', 4),
    'The Cinema': ('CH.631', '227', 5),
    'Movie Plus': ('CH.632', '240', 6),
    'Jidaigeki Senmon': ('CH.662', '292', 12),
    'Family Gekijyo': ('CH.660', '293', 13),
    'Home Drama Channel': ('CH.661', '294', 14),
    'TBS Channel 1': ('CH.616', '296', 16),
    'TBS Channel 2': ('CH.617', '297', 17),
    'TV Asahi Channel 1': ('CH.611', '298', 18),
    'TV Asahi Channel 2': ('CH.612', '299', 19),
    'Nittele Plus': ('CH.619', '300', 20),
    'Channel Ginga': ('CH.664', '305', 22),
    'Fuji TV ONE': ('CH.614', '307', 23),
    'Fuji TV TWO': ('CH.615', '308', 24),
    'Fuji TV NEXT': ('CH.613', '309', 25),
}


class CSBatchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / 'tests/fixtures/cs_identity_rows.json').read_text())
        self.configs = json.loads((ROOT / 'config/channels.yaml').read_text())['channels']
        identities = json.loads((ROOT / 'tests/fixtures/playlist_identities.json').read_text())
        self.playlist = [PlaylistChannel(name=r['playlist_name'], tvg_id=r['tvg_id'], url='') for r in identities]
        html = '<div id="ch_area">' + ''.join('<p>' + escape(n) + '</p>' for n in self.fixture['channel_names']) + '</div>'
        for channel in self.fixture['channels']:
            html += '<ul id="program_line_' + str(channel['station_line']) + '">'
            for row in channel['rows']:
                html += (f'<li s="{row["start"]}" e="{row["stop"]}" se-id="{row["source_id"]}">'
                         f'<a class="title_link" href="{escape(row["href"])}">'
                         f'<p class="program_title">{escape(row["title"])}</p>'
                         f'<p class="program_detail">{escape(row["description"])}</p></a></li>')
            html += '</ul>'
        self.page = _BangumiParser()
        self.page.feed(html)

    def test_all_17_exact_identities_and_distinct_service_guards(self):
        self.assertEqual(set(EXPECTED), {r['playlist_name'] for r in self.fixture['channels']})
        for row in self.fixture['channels']:
            with self.subTest(channel=row['playlist_name']):
                tvg, service, line = EXPECTED[row['playlist_name']]
                config = self.configs[row['config_key']]
                self.assertTrue(config['enabled'])
                self.assertEqual(tvg, find_channel(self.playlist, name=row['playlist_name']).tvg_id)
                self.assertEqual(tvg, config['expected_tvg_id'])
                options = config['source_options']
                self.assertEqual(('cs', service, line), (options['lineup'], options['station_id'], options['station_line']))
                programmes = BangumiSource(**options)._parse(self.page, tvg, '20261014')
                self.assertEqual(3, len(programmes))
                self.assertTrue(all(p.channel_id == tvg and p.source_id.startswith(service + '-') for p in programmes))
                self.assertEqual(row['rows'][0]['title'], programmes[0].title_ja)
                self.assertEqual(row['rows'][0]['description'], programmes[0].description_ja)
                self.assertEqual(row['rows'][0]['start'] + '00 +0900', programmes[0].start.strftime('%Y%m%d%H%M%S %z'))

    def test_identical_truncated_labels_cannot_swap_services(self):
        for left, right in [('tbs_channel1', 'tbs_channel2'), ('tv_asahi_channel1', 'tv_asahi_channel2'),
                            ('fuji_tv_one', 'fuji_tv_two'), ('fuji_tv_two', 'fuji_tv_next')]:
            with self.subTest(pair=(left, right)):
                options = dict(self.configs[left]['source_options'])
                options['station_line'] = self.configs[right]['source_options']['station_line']
                # Even if the visible number is dropped, the event IDs guard the mapping.
                options['station'] = options['station'].split(' ', 1)[1]
                with self.assertRaisesRegex(SourceError, 'service ID changed'):
                    BangumiSource(**options)._parse(self.page, self.configs[left]['expected_tvg_id'], '20261014')

    def test_empty_station_rows_are_rejected(self):
        options = self.configs['toei_channel']['source_options']
        self.page.program_lines[options['station_line']] = []
        with self.assertRaisesRegex(SourceError, 'only 0 meaningful'):
            BangumiSource(**options)._parse(self.page, 'CH.629', '20261014')


class ExpiredBroadcastDateTests(unittest.TestCase):
    def failure(self, code):
        cause = HTTPError('https://bangumi.org/epg/cs', code, 'Unavailable', {}, None)
        error = SourceError('Public date unavailable')
        error.__cause__ = cause
        return error

    def test_previous_404_optional_after_boundary(self):
        source = BangumiSource(station='test', lineup='cs')
        with patch.object(source, '_get_page', side_effect=[self.failure(404), object(), object()]) as fetch, patch.object(source, '_parse', return_value=[]):
            source.fetch(channel_id='exact', now=datetime(2026, 10, 14, 13, tzinfo=JST))
        self.assertEqual(['20261013', '20261014', '20261015'], [c.args[0] for c in fetch.call_args_list])

    def test_prior_404_required_before_boundary(self):
        source = BangumiSource(station='test', lineup='cs')
        with patch.object(source, '_get_page', side_effect=self.failure(404)):
            with self.assertRaises(SourceError):
                source.fetch(channel_id='exact', now=datetime(2026, 10, 14, 4, tzinfo=JST))

    def test_current_and_future_404_are_fatal(self):
        for responses in [[object(), self.failure(404)], [object(), object(), self.failure(404)]]:
            with self.subTest(responses=len(responses)):
                source = BangumiSource(station='test', lineup='cs')
                with patch.object(source, '_get_page', side_effect=responses), patch.object(source, '_parse', return_value=[]):
                    with self.assertRaises(SourceError):
                        source.fetch(channel_id='exact', now=datetime(2026, 10, 14, 13, tzinfo=JST))

    def test_access_denial_and_server_failure_remain_fatal(self):
        for code in [403, 429, 500]:
            with self.subTest(code=code):
                source = BangumiSource(station='test', lineup='cs')
                with patch.object(source, '_get_page', side_effect=self.failure(code)):
                    with self.assertRaises(SourceError):
                        source.fetch(channel_id='exact', now=datetime(2026, 10, 14, 13, tzinfo=JST))
