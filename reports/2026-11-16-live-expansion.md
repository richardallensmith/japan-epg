# 2026-11-16 nightly live EPG review

The confirmed-live playlist contains 52 channels. All five live channels without an enabled, validated EPG mapping were examined. No exact stream had a trustworthy current/future schedule, so no mapping was added. Existing mappings for dead or unpublished upstream channels were preserved; none were changed.

## Live candidates examined and unchanged

| Live `tvg-id` | Channel | Official grid finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title record 128 uses a different manifest URL. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title record 130 uses a different manifest URL. |
| `rch_98` | セクシーエンタメチャンネル | Exact ID absent; same-title record 125 uses a different manifest URL. |
| `rch_40` | 刺激ストロング | Exact ID absent; same-title record 123 uses a different manifest URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; same-title record 133 uses a different manifest URL. Its historical exact-ID mapping remains disabled pending valid listings. |

[Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-16&platform=WEB) returned status 200 and 57 records on each of November 16–19. It omitted all five exact live IDs. Related-title records carry timed programmes, but their IDs and manifest URLs differ from the live playlist streams. Assigning those listings to the live IDs would assume an unproven schedule equivalence. The five records remain pending in `config/channel_status.json`.

## Validation and changes

- `python3 -m unittest discover -v`: 85 tests passed.
- Required `--days 2` build using the confirmed-live playlist for generation and the full upstream playlist for reconciliation: passed. It produced 4,441 programmes across 47 mapped live channels, including 4,425 current/future entries. Every mapped channel has at least nine current/future entries. Latest stop: November 19 at 02:14:18 JST.
- Newly covered live channels: none. Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_100`.
- Dead or unpublished channels touched: none. No mapping, source adapter, fixture, test, or override changed.
- Files changed: `config/channel_status.json` (current reconciliation, validation, and deferral evidence), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report.
- Source concern: same-title Rakuten services have distinct IDs and stream URLs; their schedules cannot establish coverage for these five live streams.
