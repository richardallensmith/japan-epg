# 2026-11-22 nightly live EPG review

The confirmed-live playlist contains 50 channels. Five lacked validated current programme coverage. Rakuten's official dated grid returned status 200 and 57 channel records on each date from November 21 through 26, but omitted all five exact live IDs. Same-name records used different source IDs and manifest URLs. No EPG mapping was added or changed, and all historical mappings were preserved.

## Live candidates examined and unchanged

| Live `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title record 128 has a different manifest URL. |
| `rch_35` | パチンコ・パチスロ | Exact ID absent; same-title record 134 has a different manifest URL. Existing exact-ID mapping stays enabled for recovery. |
| `rch_86` | ワンニャンチャンネル | Exact ID absent; same-title record 137 has a different manifest URL. Existing exact-ID mapping stays enabled for recovery. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title record 130 has a different manifest URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; same-title record 133 has a different manifest URL. Historical exact-ID mapping remains disabled pending valid listings. |

Source: [Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-22&platform=WEB), checked on November 21–26. The [public channel catalogue](https://channel.rakuten.co.jp/service/) describes the services but does not establish a timed guide for the exact live streams. The differing identities and manifest URLs do not support assigning the replacement schedules by name.

## Validation and changes

- `python3 -m unittest discover -v`: 87 tests passed.
- Required `--days 2` build using `output/japan-live.m3u` for active generation and the full upstream playlist for inventory reconciliation: passed. It produced 4,207 programmes across 45 validated live channels, including 4,199 current/future entries. Latest stop: November 25 at 02:10:34 JST. `rch_35` and `rch_86` were unavailable in the exact-ID source grid and were omitted from the feed, with their mappings retained for recovery.
- Newly covered live channels: none. Remaining live channels without validated EPG coverage: `rch_65`, `rch_35`, `rch_86`, `rch_37`, `rch_100`.
- Dead or unpublished channels touched: none.
- Files changed: `config/channel_status.json` (current reconciliation, validation, and deferral evidence), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report. No mapping, adapter, fixture, test, or override changed.
- Source concern: Rakuten publishes same-name replacement records with different IDs and manifest URLs; exact stream equivalence is unproven.
