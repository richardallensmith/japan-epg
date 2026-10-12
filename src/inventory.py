"""Reconcile every live playlist identity without inventing or silently dropping IDs."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from .models import PlaylistChannel

STATUSES = {'pending', 'enabled', 'grouped', 'blocked'}


def reconcile(channels: list[PlaylistChannel], configs: dict, previous: dict | None = None) -> dict:
    previous = previous or {}
    identities = [(c.name, c.tvg_id) for c in channels]
    if len(identities) != len(set(identities)) or any(not tvg for _, tvg in identities):
        raise ValueError('Live playlist has duplicate identities or missing tvg-id values')
    old = {(r['playlist_name'], r['tvg_id']): r for r in previous.get('channels', [])}
    configured = {(c['playlist_name'], c['expected_tvg_id']): key for key, c in configs.items()}
    records = []
    for channel in channels:
        identity = (channel.name, channel.tvg_id)
        record = dict(old.get(identity, {}))
        record.update(playlist_name=channel.name, tvg_id=channel.tvg_id, group=channel.group_title,
                      phase='fast' if channel.group_title in {'FAST', 'ラクテンTV'} and not channel.name.endswith('(CS)') else 'conventional',
                      present=True, config_key=configured.get(identity))
        record.setdefault('status', 'pending')
        record.setdefault('reason', 'Awaiting source research and current-listing validation.')
        if record['status'] not in STATUSES:
            raise ValueError(f"Unknown inventory status: {record['status']}")
        key = record['config_key']
        if record['status'] == 'enabled' and (not key or not configs[key].get('enabled', True)):
            record.update(status='pending', reason='Enabled configuration removed or disabled; review required.')
        if record['status'] == 'enabled' and key and (
            record.get('source') != configs[key]['source'] or
            record.get('source_options') != configs[key]['source_options']
        ):
            record.update(status='pending', reason='Source mapping changed; current listings need validation.')
        if record['status'] in {'blocked', 'grouped'} and not record.get('evidence'):
            raise ValueError('Blocked/grouped channels require source evidence and a documented reason')
        if record['status'] == 'blocked' and key and configs[key].get('enabled', True):
            raise ValueError(f"Blocked channel {channel.name!r} must remain disabled")
        records.append(record)
    live = set(identities)
    removed = [dict(r, present=False) for identity, r in old.items() if identity not in live]
    return {'version': 1, 'playlist_url': previous.get('playlist_url'),
            'reconciled_at': datetime.now(timezone.utc).isoformat(),
            'identity_sha256': hashlib.sha256(json.dumps(identities, ensure_ascii=False).encode()).hexdigest(),
            'totals': dict(Counter(r['status'] for r in records)), 'channels': records + removed}


def mark_validated(inventory: dict, configs: dict, result: dict) -> None:
    for record in inventory['channels']:
        key = record.get('config_key')
        if record['present'] and key and record['tvg_id'] in result['per_channel']:
            config = configs[key]
            record.update(status='enabled', reason='Exact playlist identity and current source listings validated.',
                          source=config['source'], source_options=deepcopy(config['source_options']),
                          validated_at=datetime.now(timezone.utc).isoformat(),
                          validation=result['per_channel'][record['tvg_id']])
    inventory['totals'] = dict(Counter(r['status'] for r in inventory['channels'] if r['present']))


def save(inventory: dict, path: Path) -> None:
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(inventory, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    temp.replace(path)
