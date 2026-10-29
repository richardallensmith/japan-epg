# 2026-10-29 nightly live EPG review

The confirmed-live playlist has 53 channels. The selected batch of 12 uncovered live channels did not yield a validated current/future public schedule, so no new EPG mapping was enabled. The existing 29 active live mappings remain in place. No dead or unpublished channel mapping was touched.

## Selected live batch

| Exact live `tvg-id` | Channel | Why deferred |
|---|---|---|
| `fastch_v2_kids` | アニマックス FREE | Fast TV identifies a separate FAST feed; the conventional Animax guide does not establish its times. |
| `fastch_v2_pett1` | ペットTV | No public dated programme grid for this feed was established. |
| `fastch_v2_camng` | キャンプ・アウトドア | No public dated programme grid for this feed was established. |
| `fastch_v2_travl` | 今日のごはんなに? | No public dated programme grid for this feed was established. |
| `fastch_v2_recip` | 観るたび | No public dated programme grid for this feed was established. |
| `fastch_v2_news1` | 丸ごと九州 | No public dated programme grid for this feed was established. |
| `fastch_v2_jpthp` | ぴあ落語ざんまい | The public on-demand catalogue does not establish FAST transmission times. |
| `fastch_v2_snyon` | FASHIONPLUS | The former FASHION＋ timetable link redirects to the operator site without a current dated grid. |
| `fastch_v2_goshogi` | 囲碁・将棋ライト | The R Channel and conventional schedules cannot establish this separate FAST feed's times. |
| `fastch_v2_hokkaido` | 丸ごと北海道 | Contributing broadcasters' schedules do not establish this curated feed's times. |
| `fastch_v2_tokai` | 東海ロキポ | Contributing broadcasters' schedules do not establish this curated feed's times. |
| `fastch_v2_krdrm` | 韓流チャンネル | No public dated programme grid for this feed was established. |

[Fast TV's channel catalogue](https://fastv.jp/channel/) confirms these distinct services but contains descriptions rather than dated listings. Its [viewing guide](https://fastv.jp/howto/) says the programme guide is available in the app. The old [FASHION＋ timetable URL](https://fast-fashion.tv/now-on-air/) no longer serves a timetable. No app access restrictions were bypassed.

The six uncovered R Channel feeds from the previous batch were rechecked against [Rakuten's official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-10-29&platform=WEB) for October 29 through November 1. IDs `100`, `65`, `37`, `98`, `40`, and `42` were absent on all four dates. The historical `rch_100` mapping remains configured and disabled for active generation pending current schedule validation.

## Validation

- `python3 -m unittest discover -v`: 77 tests passed.
- Required two-day build with `output/japan-live.m3u` active and the full upstream inventory playlist: passed; 1,861 programmes across 29 active live channels, of which 1,860 were current/future at validation. Latest programme ends November 1 at 02:00 JST.
- 1,255 bilingual titles and 1,151 bilingual descriptions; source-language fallback remained available.
- No source adapter, channel mapping, or fixture was changed. The build refreshed `output/epg.xml`, `cache/translations.json`, and the upstream inventory validation data in `config/channel_status.json`. The 12 selected FAST records now document their deferral reasons and evidence.

## Remaining live gaps

All 24 uncovered live channels remain: `rch_100`, `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `fastch_v2_busns`, `fastch_v2_entns`, `fastch_v2_bgolf`, `fastch_v2_samri`, `fastch_v2_comdy`, `fastch_v2_asdrm`, and the 12 FAST IDs in the table above. No speculative schedule was published.
