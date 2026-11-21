# 2026-11-21 nightly live EPG review

The confirmed-live playlist contains 50 channels. Five lacked current validated programme coverage. All five were checked independently against Rakuten's official dated programme grid for November 20–25. The API returned status 200 and 57 channel records on every checked date, but omitted all five exact live IDs. No EPG mapping was added or changed. Historical mappings, including those for streams no longer in the live playlist, were preserved.

## Live candidates examined and unchanged

| Live `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title record 128 has a different manifest URL. |
| `rch_35` | パチンコ・パチスロ | Exact ID absent; same-title record 134 has a different manifest URL. Existing exact-ID mapping remains enabled for automatic recovery. |
| `rch_86` | ワンニャンチャンネル | Exact ID absent; same-title record 137 has a different manifest URL. Existing exact-ID mapping remains enabled for automatic recovery. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title record 130 has a different manifest URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; same-title record 133 has a different manifest URL. Historical exact-ID mapping remains disabled pending valid listings. |

Source: [Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-21&platform=WEB). The [public channel catalogue](https://channel.rakuten.co.jp/service/) describes the services but does not provide a current timed guide tied to these exact streams. Distinct IDs and manifest URLs do not establish that the replacement schedules describe the confirmed-live streams.

## Validation and changes

- `python3 -m unittest discover -v`: 87 tests passed.
- Required `--days 2` build using `output/japan-live.m3u` for active generation and the full upstream playlist for inventory reconciliation: passed. It produced 4,107 programmes across 45 validated live channels, including 4,093 current/future entries. Latest stop: November 24 at 02:55:43 JST. The exact-ID sources for `rch_35` and `rch_86` were unavailable and omitted from this feed; their mappings remain configured for recovery.
- Newly covered live channels: none. Remaining live channels without current validated EPG coverage: `rch_65`, `rch_35`, `rch_86`, `rch_37`, `rch_100`.
- Dead or unpublished channels touched: none.
- Files changed: `config/channel_status.json` (current reconciliation, validation, and deferral evidence), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report. No mapping, adapter, fixture, test, or override changed.
- Source concern: Rakuten's current grid has replacement records with the same names but different IDs and manifest URLs. These cannot be mapped by name alone.
