# 2026-11-25 nightly live EPG review

The confirmed-live playlist contains 50 channels. Seven lack validated current programme coverage. Rakuten's official dated grid returned 57 channel records on each checked date from November 24 through 28, but omitted all seven exact live IDs. Same-title records use different IDs and manifest URLs, so their schedules cannot be assigned to the live streams. No new mapping was supported; historical mappings remain available for recovery.

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

Source: [Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-25&platform=WEB), checked for November 24–28. No trustworthy timed source was established for these exact live streams.

## Validation and changes

- `python3 -m unittest discover -v`: 87 tests passed.
- Required `--days 2` build using `output/japan-live.m3u` for active generation and the full upstream playlist for inventory reconciliation: passed. It produced 3,956 programmes across 43 validated live channels, including 3,952 current/future entries. Latest stop: November 28 at 05:18:44 JST. The four enabled mappings with absent exact-ID sources were omitted from the feed and marked pending for this run.
- Newly covered live channels: none. Remaining live channels without validated EPG coverage: `rch_65`, `rch_34`, `rch_74`, `rch_35`, `rch_86`, `rch_37`, `rch_100`.
- Dead or unpublished channel mappings touched: none.
- Files changed: `config/channel_status.json` (current reconciliation and evidence), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report. No mapping, adapter, fixture, test, or override changed.
- Source concern: Rakuten publishes same-name replacement records with different IDs and manifest URLs; exact stream equivalence remains unproven.
