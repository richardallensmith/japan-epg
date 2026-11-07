# 2026-11-07 nightly live EPG expansion

The confirmed-live playlist has 52 channels. Five lack an enabled, validated EPG mapping. All five were examined; none could be enabled without inventing a schedule. No dead or unpublished upstream mapping was changed or disabled.

## Examined and unchanged

| Exact `tvg-id` | Live channel | Reason |
|---|---|---|
| `rch_65` | キッズ | Absent from R Channel's dated programme grid on November 7–10. |
| `rch_37` | エンタメ～テレDEEP | Absent from the same grid on all four dates. |
| `rch_98` | セクシーエンタメチャンネル | Absent from the same grid on all four dates. |
| `rch_40` | 刺激ストロング | Absent from the same grid on all four dates. |
| `rch_100` | 囲碁・将棋ライト (R) | Absent from the same grid on all four dates. Its historical exact-ID mapping remains configured and disabled pending a current schedule. |

[Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-07&platform=WEB) returned status 200 and 57 channel records for each of November 7–10, but no record with any of these five IDs. The five live stream identities therefore have no current or future timed entries in the source adapter. Similar conventional and FAST services do not establish a schedule for these exact streams.

## Validation

- `python3 -m unittest discover -v`: 84 tests passed. Six stale assertions were corrected to check the pinned `tvg-name` and `tvg-id` when the live playlist uses an English visible name.
- Required 48-hour live-playlist build with the full upstream inventory for reconciliation: passed; 4,332 programmes across 47 mapped live channels, including 4,309 current/future entries. The latest programme ends November 10 at 02:08 JST. The generated XML contains 47 channel records and 4,332 programme records.
- Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_100`.
- Files changed: `config/channel_status.json`, `tests/test_fastv_source.py`, `cache/translations.json`, `output/epg.xml`, and this report.

No new source mapping was added. The next run should recheck the official dated grid and enable a channel only after its exact ID, title, stream URL, and current/future programme entries validate.
