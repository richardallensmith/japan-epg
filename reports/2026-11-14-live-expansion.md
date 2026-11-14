# 2026-11-14 nightly live EPG review

The confirmed-live playlist contains 53 channels. All six live channels without an enabled, validated EPG mapping were examined. None had a trustworthy current/future schedule for its exact stream, so no new mapping was enabled. Existing mappings, including the disabled historical `rch_100` mapping and mappings for dead or unpublished streams, were preserved.

## Live candidates examined and unchanged

| Live `tvg-id` | Channel | Official grid finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title record 128 has a different manifest URL. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title record 130 has a different manifest URL. |
| `rch_98` | セクシーエンタメチャンネル | Exact ID absent; same-title record 125 has a different manifest URL. |
| `rch_40` | 刺激ストロング | Exact ID absent; same-title record 123 has a different manifest URL. |
| `rch_42` | 映画（年齢制限あり） | Exact ID absent; same-title record 122 has a different manifest URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; same-title record 133 has a different manifest URL. Its historical exact-ID mapping remains configured but disabled. |

[Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-14&platform=WEB) returned 57 channel records on each of November 13–17. None contained an exact record for these six live IDs. The differently identified records carry timed programmes for different stream URLs; those programmes were not assigned to the live playlist streams. `config/channel_status.json` records the refreshed source evidence.

## Validation and changes

- `python3 -m unittest discover -v`: 85 tests passed.
- Required `--days 2` build using `output/japan-live.m3u` for active generation and the full upstream playlist for inventory reconciliation: passed. It produced 4,367 programmes across 47 mapped live channels, including 4,344 current/future entries. Every mapped live channel has at least nine current/future entries. Latest programme stop: November 17 at 02:08:08 JST.
- Newly covered live channels: none. Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `rch_100`.
- Dead or unpublished channels touched: none. No channel mapping, source adapter, fixture, test, or override changed.
- Files changed: `config/channel_status.json` (fresh validation and deferral evidence), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report.
- Source concern: Rakuten's guide lists related-title services under different IDs and manifest URLs. Schedule equivalence for the six live streams is unproven.
