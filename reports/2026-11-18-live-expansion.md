# 2026-11-18 nightly live EPG review

The confirmed-live playlist contains 51 channels. Four live channels lack an enabled, validated EPG mapping; all four were examined. No exact stream had a trustworthy current/future schedule, so no mapping was added. Existing mappings for dead or unpublished upstream channels were preserved and none were changed.

## Live candidates examined and unchanged

| Live `tvg-id` | Channel | Official grid finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; related-title record 128 has a different manifest URL. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; related-title record 130 has a different manifest URL. |
| `rch_42` | 映画（年齢制限あり） | Exact ID absent; related-title record 122 has a different manifest URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; related-title record 133 has a different manifest URL. Its historical exact-ID mapping remains configured but disabled pending valid listings. |

[Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-18&platform=WEB) returned status 200 and 57 records on each date checked, November 18–21. It omitted all four exact live IDs. Related-title records carry timed programmes, but their IDs and manifest URLs differ from the live playlist streams. The four records remain pending in `config/channel_status.json` because the available schedules do not establish stream identity.

## Validation and changes

- `python3 -m unittest discover -v`: 85 tests passed.
- Required `--days 2` build using the confirmed-live playlist for generation and the full upstream playlist for reconciliation: passed. It produced 4,365 programmes across 47 mapped live channels, including 4,339 current/future entries. Latest stop: November 21 at 04:14:41 JST.
- Newly covered live channels: none. Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_42`, `rch_100`.
- Dead or unpublished channels touched: none. No mapping, source adapter, fixture, test, or override changed.
- Files changed: `config/channel_status.json` (current reconciliation, validation, and deferral evidence), `cache/translations.json` (current translation cache), `output/epg.xml` (validated feed), and this report.
- Source concern: related-title Rakuten services have distinct IDs and stream URLs; their schedules cannot establish coverage for these four live streams.
