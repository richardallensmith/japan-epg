import json
import unittest
from pathlib import Path

from src.inventory import reconcile, mark_validated
from src.models import PlaylistChannel
from src.playlist import find_channel

ROOT = Path(__file__).resolve().parents[1]
BATCH = {
    'BS 10': 'BS10_jp', 'JCOM BS': 'J-COM-BS_jp', 'BS Yoshimoto': 'BSよしもと_jp',
    'WOWOW Prime': 'CH.621', 'WOWOW Live': 'CH.622', 'WOWOW Cinema': 'CH.623',
    'BS 10 Premium': 'CH.625', 'WOWOW Plus': 'CH.630', 'Fishing Vision': 'rch_46',
    'Green Channel': 'CH.688', 'JSport 1': 'CH.603', 'JSport 2': 'CH.604',
    'JSport 3': 'CH.606', 'JSport 4': 'CH.605',
}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        rows = json.loads((ROOT / 'tests/fixtures/playlist_identities.json').read_text())
        self.playlist = [PlaylistChannel(name=r['playlist_name'], tvg_id=r['tvg_id'],
                                         group_title=r['group'], url='') for r in rows]
        self.configs = json.loads((ROOT / 'config/channels.yaml').read_text())['channels']

    def test_exact_batch_ids_and_source_guards(self):
        for name, tvg in BATCH.items():
            with self.subTest(name=name):
                self.assertEqual(tvg, find_channel(self.playlist, name=name).tvg_id)
                configs = [c for c in self.configs.values() if c['playlist_name'] == name]
                self.assertEqual(1, len(configs))
                self.assertEqual(tvg, configs[0]['expected_tvg_id'])
                self.assertEqual('bs', configs[0]['source_options']['lineup'])
                self.assertTrue(configs[0]['source_options']['station_id'])

    def test_every_identity_is_accounted_for_and_fast_deferred(self):
        inventory = reconcile(self.playlist, self.configs)
        self.assertEqual(167, len(inventory['channels']))
        self.assertEqual({'pending': 167}, inventory['totals'])
        self.assertTrue(all(r['status'] == 'pending' for r in inventory['channels'] if r['phase'] == 'fast'))

    def test_id_change_is_pending_and_removed_identity_retained(self):
        original = reconcile(self.playlist, self.configs)
        record = original['channels'][0]
        record.update(status='blocked', reason='Both sources unavailable', evidence=['https://example.org'])
        changed = [PlaylistChannel(name=self.playlist[0].name, tvg_id='changed', url='')] + self.playlist[1:]
        inventory = reconcile(changed, self.configs, original)
        self.assertEqual('pending', inventory['channels'][0]['status'])
        self.assertFalse(inventory['channels'][-1]['present'])
        self.assertEqual('blocked', inventory['channels'][-1]['status'])

    def test_blocked_requires_evidence(self):
        inventory = reconcile(self.playlist, self.configs)
        inventory['channels'][0]['status'] = 'blocked'
        with self.assertRaises(ValueError):
            reconcile(self.playlist, self.configs, inventory)

    def test_configured_does_not_mean_validated(self):
        inventory = reconcile(self.playlist, self.configs)
        mark_validated(inventory, self.configs, {'per_channel': {'CH.603': {'programmes': 10}}})
        self.assertEqual(1, inventory['totals']['enabled'])
        self.assertEqual(166, inventory['totals']['pending'])

class InventoryGuardTests(unittest.TestCase):
    setUp = InventoryTests.setUp

    def test_mapping_change_requires_revalidation(self):
        inventory = reconcile(self.playlist, self.configs)
        mark_validated(inventory, self.configs, {'per_channel': {'CH.603': {'programmes': 10}}})
        self.configs['jsports1']['source_options']['station_id'] = 'different'
        updated = reconcile(self.playlist, self.configs, inventory)
        row = next(r for r in updated['channels'] if r['tvg_id'] == 'CH.603')
        self.assertEqual('pending', row['status'])

    def test_blocked_channel_cannot_be_enabled(self):
        inventory = reconcile(self.playlist, self.configs)
        row = next(r for r in inventory['channels'] if r['tvg_id'] == 'CH.603')
        row.update(status='blocked', evidence=['https://example.org/unavailable'])
        with self.assertRaisesRegex(ValueError, 'must remain disabled'):
            reconcile(self.playlist, self.configs, inventory)
