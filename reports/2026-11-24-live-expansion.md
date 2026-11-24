# 2026-11-24 nightly live EPG review

The confirmed-live playlist contains 50 channels. Seven lack validated current programme coverage. Rakuten's official dated grid returned 57 channel records on each checked date from November 23 through 27, but omitted all seven exact live IDs. Similar-name records used different source IDs and manifest URLs. No new EPG mapping was supported by the available evidence; historical mappings remain in place. The production build revealed that two previously validated live mappings, `rch_34` and `rch_74`, have also lost their exact-ID listings.

## Live candidates examined and unchanged

| Live `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title record 128 has a different manifest URL. |
| `rch_34` | ムビドラTV | Exact ID absent; same-title record 138 has a different manifest URL. Existing exact-ID mapping stays enabled for recovery. |
| `rch_74` | 麻雀 | Exact ID absent; same-title record 139 has a different manifest URL. Existing exact-ID mapping stays enabled for recovery. |
| `rch_35` | パチンコ・パチスロ | Exact ID absent; same-title record 134 has a different manifest URL. Existing exact-ID mapping stays enabled for recovery. |
| `rch_86` | ワンニャンチャンネル | Exact ID absent; same-title record 137 has a different manifest URL. Existing exact-ID mapping stays enabled for recovery. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title record 130 has a different manifest URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; same-title record 133 has a different manifest URL. Historical exact-ID mapping remains disabled pending valid listings. |

Source: [Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-24&platform=WEB), checked for November 23–27. The differing identities and manifest URLs do not support assigning replacement schedules by name. No timed source was established for these exact live streams.

## Validation and changes

- `python3 -m unittest discover -v`: 87 tests passed.
- Required `--days 2` build using `output/japan-live.m3u` for active generation and the full upstream playlist for inventory reconciliation: passed. It produced 4,017 programmes across 43 validated live channels, including 3,998 current/future entries. Latest stop: November 27 at 02:15:14 JST. Exact-ID sources for `rch_34`, `rch_74`, `rch_35`, and `rch_86` were unavailable and omitted from the feed, while their mappings remain enabled for recovery.
- Newly covered live channels: none. Remaining live channels without validated EPG coverage: `rch_65`, `rch_34`, `rch_74`, `rch_35`, `rch_86`, `rch_37`, `rch_100`.
- Dead or unpublished channel mappings touched: none.
- Files changed: `config/channel_status.json` (current reconciliation and validation), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report. No mapping, adapter, fixture, test, or override changed.
- Source concern: Rakuten publishes same-name replacement records with different IDs and manifest URLs; exact stream equivalence is unproven.
