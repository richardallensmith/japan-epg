# 2026-11-09 nightly live EPG review

The confirmed-live playlist has 52 channels. Its five uncovered identities were examined against Rakuten's official dated programme grid for November 9–12. None has a current or future timed row for its exact `tvg-id` and stream URL, so no EPG mapping was enabled. The 47 mapped live channels and all historical mappings were preserved. No dead or unpublished channel was touched.

## Examined and unchanged

| Exact `tvg-id` | Live channel | Finding |
|---|---|---|
| `rch_65` | キッズ | No ID 65 grid row. The same-name row is ID 128 with a different stream URL. |
| `rch_37` | エンタメ～テレDEEP | No ID 37 grid row. The same-name row is ID 130 with a different stream URL. |
| `rch_98` | セクシーエンタメチャンネル | No ID 98 grid row. The same-name row is ID 125 with a different stream URL. |
| `rch_40` | 刺激ストロング | No ID 40 grid row. The same-name row is ID 123 with a different stream URL. |
| `rch_100` | 囲碁・将棋ライト (R) | No ID 100 grid row. The same-name row is ID 133 with a different stream URL. Its historical exact-ID mapping remains configured and disabled pending a current schedule. |

[Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-09&platform=WEB) returned status 200 and 57 channel records on each of November 9–12. The five same-name records have valid programmes for their own streams, but their IDs and manifest URLs differ from the five live playlist streams. Their schedules were not copied across identities.

## Validation

- `python3 -m unittest discover -v`: 84 tests passed.
- Required `--days 2` live-playlist build with the full upstream inventory used only for reconciliation: passed. It generated 4,324 programmes on 47 live channels, including 4,297 current/future entries. The latest programme ends November 12 at 03:20:45 JST. The XML contains 47 channel records and 4,324 programme records.
- Live channels newly covered: none.
- Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_100`.
- Dead or unpublished channels touched: none.
- Files changed: `config/channel_status.json`, `cache/translations.json`, `output/epg.xml`, and this report. No mapping or adapter was changed.
