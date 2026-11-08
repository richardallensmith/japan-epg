# 2026-11-08 nightly live EPG expansion

The confirmed-live playlist has 52 channels. Forty-seven have enabled mappings with current programme data. All five uncovered live identities were examined; none has a validated schedule for its exact stream. No new mapping was enabled, and no dead or unpublished upstream mapping was changed.

## Examined and unchanged

| Exact `tvg-id` | Live channel | Source finding |
|---|---|---|
| `rch_65` | キッズ | Absent from Rakuten's dated grid November 8–11. The same-name grid record is ID 128 with a different stream URL. |
| `rch_37` | エンタメ～テレDEEP | Absent from the dated grid. The same-name grid record is ID 130 with a different stream URL. |
| `rch_98` | セクシーエンタメチャンネル | Absent from the dated grid. The same-name grid record is ID 125 with a different stream URL. |
| `rch_40` | 刺激ストロング | Absent from the dated grid. The same-name grid record is ID 123 with a different stream URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Absent from the dated grid. The same-name grid record is ID 133 with a different stream URL. Its historical exact-ID mapping remains configured and disabled pending a valid current schedule. |

[Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-08&platform=WEB) returned status 200 with 57 records on each of November 8–11. It supplied no timed entries for the five exact IDs. The same-name records use distinct playlist URLs, so they cannot establish schedule identity for the live streams. The five identities remain pending rather than receiving speculative programme data.

## Validation

- `python3 -m unittest discover -v`: 84 tests passed.
- Required `--days 2` live-playlist build with full upstream inventory reconciliation: passed. It generated 4,322 programmes on 47 live channels, including 4,302 current/future entries. Latest programme ends November 11 at 02:10 JST.
- Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_100`.
- Files changed: `config/channel_status.json`, `cache/translations.json`, `output/epg.xml`, and this report.

No dead or unpublished channels were touched. The next run should recheck an official dated source and enable one of these channels only when its exact identity and current/future entries validate.
