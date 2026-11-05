# 2026-11-05 nightly live EPG expansion

The confirmed-live playlist has 54 channels. This run selected 12 uncovered FAST channels and enabled all 12 after exact stream identity checks and current/future schedule validation. The active feed now has 42 mapped live channels and 12 live gaps. No mapping for a dead or unpublished upstream channel was changed or disabled.

## Added live coverage

| Exact `tvg-id` | Channel | Validated programmes (48-hour build) |
|---|---|---:|
| `fastch_v2_busns` | ビジネス・プレミアム (FAST) | 94 |
| `fastch_v2_entns` | エンタメニュース (FAST) | 134 |
| `fastch_v2_bgolf` | GOLF LIFE (FAST) | 136 |
| `fastch_v2_samri` | 時代劇TV (FAST) | 97 |
| `fastch_v2_comdy` | LeminoTV (FAST) | 188 |
| `fastch_v2_asdrm` | エンタメ・アジア (FAST) | 76 |
| `fastch_v2_kids` | アニマックス FREE (FAST) | 121 |
| `fastch_v2_pett1` | ペットTV (FAST) | 280 |
| `fastch_v2_camng` | キャンプ・アウトドア (FAST) | 124 |
| `fastch_v2_travl` | 今日のごはんなに? (FAST) | 146 |
| `fastch_v2_recip` | 観るたび (FAST) | 89 |
| `fastch_v2_news1` | 丸ごと九州 (FAST) | 122 |

Source: [Fast TV's public embedded player](https://fastv.jp/) calls its [channel list](https://fastv-v2.routez.cloud/api/v2/fastv2/api/getChannelList?did=null&app=0FIpP%2BH3RDgE%2BOc5uU7cmA%3D%3D) and per-channel `getWebProgramList/{channel_id}` guide. The adapter pins the source channel ID and name, unwraps the public ad URL where present, and requires the resulting stream URL to equal the exact live playlist URL. Each channel had at least three current/future timed programmes and more than two hours of forward coverage. The source's `no_program_asset` placeholder rows are excluded. Japanese titles and descriptions come from the guide; English enrichment uses the existing translation pipeline.

## Examined and unchanged

The six uncovered R Channel identities `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, and `rch_100` were rechecked in [R Channel's dated grid](https://channel.rakuten.co.jp/schedule) for November 5–8. The grid returned 57 channels each day but none of these six IDs, so no current timed rows could be validated. Their existing status and the disabled historical `rch_100` mapping were preserved. These checks did not expand the selected 12-channel FAST batch.

## Validation and remaining gaps

- `python3 -m unittest discover -v`: 83 tests passed.
- Required `--days 2` live-playlist build with the full upstream inventory for reconciliation: passed; 3,563 programmes across 42 mapped live channels, 3,510 current/future, latest stop November 8 at 02:00 JST. All 12 new channel records are `enabled` with per-channel validation counts in `config/channel_status.json`.
- Remaining live gaps: `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `rch_100`, `fastch_v2_jpthp`, `fastch_v2_snyon`, `fastch_v2_goshogi`, `fastch_v2_hokkaido`, `fastch_v2_tokai`, `fastch_v2_krdrm`. The six remaining FAST feeds appear in the same public player guide and are candidates for the next batch; they were outside this run's 12-channel selection.
- Files changed: `config/channels.yaml`, `config/channel_status.json`, `src/main.py`, `src/fetch/fastv.py`, `tests/test_fastv_source.py`, `tests/fixtures/fastv_busns_rows.json`, `README.md`, this report, `cache/translations.json`, and `output/epg.xml`.

The Fast TV guide is a public player API and may change. The adapter fails on a changed channel identity, stream URL, malformed data, overlap, or insufficient forward coverage rather than substituting a similar conventional or FAST service.
