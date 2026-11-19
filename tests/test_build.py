import argparse
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from src.fetch.rchannel import ChannelAbsentFromGrid
from src.main import build
from src.models import PlaylistChannel, Programme
from src.validate import ValidationError


class BuildSafetyTests(unittest.TestCase):
    def test_absent_rchannel_grid_is_pending_and_recovers_automatically(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'config').mkdir()
            (root / 'output').mkdir()
            config = {'channels': {
                key: {'enabled': True, 'playlist_name': key, 'expected_tvg_id': key,
                      'source': 'rchannel', 'source_options': {'source_channel_id': number,
                      'source_title': key}, 'display_name_en': key, 'display_name_ja': key}
                for key, number in [('missing', 35), ('available', 47)]}}
            (root / 'config/channels.yaml').write_text(json.dumps(config))
            playlist = [PlaylistChannel(name=key, tvg_id=key, url='https://example.org/' + key)
                        for key in config['channels']]
            now = datetime.now(ZoneInfo('Asia/Tokyo'))
            def entries(channel_id):
                return [Programme(channel_id=channel_id,
                                  start=now + timedelta(hours=index) - timedelta(minutes=1),
                                  stop=now + timedelta(hours=index + 1) - timedelta(minutes=1),
                                  title_ja='', title_en=f'Show {index}') for index in range(3)]
            def source(fetch):
                return SimpleNamespace(name='R Channel', fetch=fetch)
            missing = source(lambda **_: (_ for _ in ()).throw(ChannelAbsentFromGrid('exact ID absent')))
            available = source(lambda **_: entries('available'))
            recovered = source(lambda **_: entries('missing'))
            args = argparse.Namespace(channel=None, playlist='live.m3u', inventory_playlist=None,
                                      days=2, description_chars=48, output='output/epg.xml')
            with patch('src.main.ROOT', root), patch('src.main.load_playlist', return_value=playlist), \
                 patch('src.main.RChannelSource', side_effect=[missing, available, recovered, available]), \
                 patch('src.main.TranslationEngine'):
                result = build(args)
                self.assertEqual({'missing': 'exact ID absent'}, result['unavailable_channels'])
                inventory = json.loads((root / 'config/channel_status.json').read_text())
                self.assertEqual({'pending': 1, 'enabled': 1}, inventory['totals'])
                self.assertEqual({'available'}, set(result['per_channel']))
                result = build(args)
                self.assertEqual({}, result['unavailable_channels'])
                inventory = json.loads((root / 'config/channel_status.json').read_text())
                self.assertEqual({'enabled': 2}, inventory['totals'])
                self.assertEqual({'missing', 'available'}, set(result['per_channel']))

    def test_invalid_schedule_preserves_previous_feed_and_pending_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'config').mkdir()
            (root / 'output').mkdir()
            output = root / 'output/epg.xml'
            output.write_text('previous validated feed')
            config = {'channels': {'test': {'enabled': True, 'playlist_name': 'Test',
                      'expected_tvg_id': 'exact', 'source': 'bangumi', 'source_options': {},
                      'display_name_en': 'Test', 'display_name_ja': 'テスト'}}}
            (root / 'config/channels.yaml').write_text(json.dumps(config))
            old = datetime.now(timezone.utc) - timedelta(days=3)
            programmes = [Programme(channel_id='exact', start=old, stop=old + timedelta(hours=1),
                                    title_ja='ニュース', title_en='News')]
            args = argparse.Namespace(channel=None, playlist='https://example.org/live.m3u',
                                      days=1, description_chars=48, output='output/epg.xml')
            with patch('src.main.ROOT', root), patch('src.main.load_playlist', return_value=[
                PlaylistChannel(name='Test', tvg_id='exact', url='')
            ]), patch('src.main.BangumiSource') as source, patch('src.main.TranslationEngine'):
                source.return_value.name = 'Live source'
                source.return_value.fetch.return_value = programmes
                with self.assertRaises(ValidationError):
                    build(args)
            self.assertEqual('previous validated feed', output.read_text())
            inventory = json.loads((root / 'config/channel_status.json').read_text())
            self.assertEqual({'pending': 1}, inventory['totals'])
