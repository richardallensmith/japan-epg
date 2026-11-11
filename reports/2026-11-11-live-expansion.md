# 2026-11-11 nightly live EPG review

The confirmed-live playlist has 53 channels. Six live identities lack a validated enabled mapping. Rakuten's official dated programme grid was checked for November 10–15 (57 records on each date). None of the six exact IDs appeared. Alternative records with related names use different IDs and manifest URLs, so their programme data cannot be assigned to these live streams. No live mapping was enabled and no historical mapping was removed or disabled.

## Examined and unchanged

| Exact `tvg-id` | Live channel | Grid finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title ID 128 has a different stream URL. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title ID 130 has a different stream URL. |
| `rch_98` | セクシーエンタメチャンネル | Exact ID absent; same-title ID 125 has a different stream URL. |
| `rch_40` | 刺激ストロング | Exact ID absent; same-title ID 123 has a different stream URL. The [broadcaster schedule](https://shigeki-strong.jp/schedule_list) does not establish that the Rakuten stream follows its conventional broadcast schedule. |
| `rch_42` | 映画（年齢制限あり） | Exact ID absent; same-title ID 122 has a different stream URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; source-title ID 133 has a different stream URL. Historical disabled exact-ID configuration retained. |

[Rakuten's official dated grid for November 11](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-11&platform=WEB) supplied timed programmes for its alternative streams. No current/future timed programme was validated for any of the six exact live streams.

## Validation

- `python3 -m unittest discover -v`: 85 tests passed.
- Required `python3 -m src.main --days 2 --playlist output/japan-live.m3u --inventory-playlist https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u` build: passed. It generated 4,283 programmes on 47 mapped live channels, including 4,256 current/future entries. The latest programme ends November 14 at 04:41:33 JST. The XML contains 47 channel records and 4,283 programme records.
- Live channels newly covered: none.
- Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `rch_100`.
- Dead or unpublished channels touched: none.
- Mapping or adapter changes: none.
- Files changed: `config/channel_status.json`, `cache/translations.json`, `output/epg.xml`, and this report.
