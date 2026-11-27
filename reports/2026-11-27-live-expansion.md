# 2026-11-27 nightly live EPG review

The confirmed-live playlist contains 50 channels. All seven without validated current programme coverage were checked against [Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-27&platform=WEB) for November 26–30. The grid returned 57 channel records per day but omitted each exact live `rch_` ID. Same-title records have different IDs and manifest URLs, so their timed programmes cannot be assigned to the confirmed-live streams. No new mapping was supported. Existing mappings remain available for recovery.

## Live candidates examined and unchanged

| Live `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title record 128 has a different manifest URL. |
| `rch_34` | ムビドラTV | Exact ID absent; same-title record 138 has a different manifest URL. Existing exact-ID mapping remains enabled. |
| `rch_74` | 麻雀 | Exact ID absent; same-title record 139 has a different manifest URL. Existing exact-ID mapping remains enabled. |
| `rch_35` | パチンコ・パチスロ | Exact ID absent; same-title record 134 has a different manifest URL. Existing exact-ID mapping remains enabled. |
| `rch_86` | ワンニャンチャンネル | Exact ID absent; same-title record 137 has a different manifest URL. Existing exact-ID mapping remains enabled. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title record 130 has a different manifest URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; same-title record 133 has a different manifest URL. Historical exact-ID mapping remains disabled pending valid listings. |

No trustworthy timed source was established for these exact live streams.

## Validation and changes

- `python3 -m unittest discover -v`: 87 tests passed.
- Required `--days 2` build using `output/japan-live.m3u` for active generation and the full upstream playlist for inventory reconciliation: passed. It produced 4,002 programmes across 43 validated live channels, including 3,986 current/future entries. Latest stop: November 30 at 02:21:38 JST. Four enabled mappings with absent exact-ID sources were omitted from the feed and marked pending for this run.
- Newly covered live channels: none. Remaining live channels without validated EPG coverage: `rch_65`, `rch_34`, `rch_74`, `rch_35`, `rch_86`, `rch_37`, `rch_100`.
- Dead or unpublished channel mappings touched: none.
- Files changed: `config/channel_status.json` (current reconciliation and source evidence), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report. No mapping, adapter, fixture, test, or override changed.
- Source concern: Rakuten publishes same-name replacement records with different IDs and manifest URLs; exact stream equivalence remains unproven.
