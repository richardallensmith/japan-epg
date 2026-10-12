import argparse
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from src.main import build
from src.models import PlaylistChannel, Programme
from src.validate import ValidationError


class BuildSafetyTests(unittest.TestCase):
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
