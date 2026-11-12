# 2026-11-12 nightly live EPG review

The confirmed-live playlist contains 53 channels. Six lack an enabled, validated EPG mapping. Rakuten's official dated programme grid returned status 200 and 57 channel records on each of November 12–16. None of the six exact live `tvg-id` values appeared. Similarly named guide records use different IDs and manifest URLs, so their timed programmes cannot be assigned to these streams. No mapping was enabled or removed; historical mappings remain intact.

## Examined and unchanged

| Live `tvg-id` | Channel | Official grid finding |
|---|---|---|
| `rch_65` | キッズ | Exact ID absent; same-title ID 128 uses a different stream URL. |
| `rch_37` | エンタメ～テレDEEP | Exact ID absent; same-title ID 130 uses a different stream URL. |
| `rch_98` | セクシーエンタメチャンネル | Exact ID absent; same-title ID 125 uses a different stream URL. |
| `rch_40` | 刺激ストロング | Exact ID absent; same-title ID 123 uses a different stream URL. A conventional broadcaster schedule does not establish the Rakuten stream's timing. |
| `rch_42` | 映画（年齢制限あり） | Exact ID absent; same-title ID 122 uses a different stream URL. |
| `rch_100` | 囲碁・将棋ライト (R) | Exact ID absent; same-title ID 133 uses a different stream URL. Its disabled historical exact-ID mapping remains configured. |

The [official Rakuten grid for November 12](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-12&platform=WEB) and its November 13–16 dates were checked against each live playlist URL. All six are deferred until a trustworthy current/future guide for their exact streams is available.

## Validation and changes

- `python3 -m unittest discover -v`: 85 tests passed.
- Required `--days 2` live-playlist build with the full upstream playlist used only for reconciliation: passed. It produced 4,280 programmes on 47 mapped live channels, including 4,269 current/future entries. Every mapped live channel has current/future data. The latest programme ends November 15 at 02:05:01 JST.
- Newly covered live channels: none. Remaining uncovered live IDs: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `rch_100`.
- Dead or unpublished channels touched: none. No mapping, source adapter, fixture, test, or override was changed.
- Files changed: `config/channel_status.json` (fresh validation and deferral evidence), `cache/translations.json` (build cache), `output/epg.xml` (validated feed), and this report.
