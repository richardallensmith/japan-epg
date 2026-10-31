# 2026-10-31 nightly live EPG review

The confirmed-live playlist contains 53 channels. Twelve uncovered live identities were reviewed. No new mapping was enabled because no exact current/future timed source was validated. All 29 active live mappings and historical mappings were preserved; no dead or unpublished channel was touched.

## Selected live batch

| Exact `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_100` | 囲碁・将棋ライト (R) | Rakuten's official dated grid omitted this ID on October 31 through November 3; its historical disabled mapping was retained. |
| `rch_65` | キッズ | Absent from the same dated grid. |
| `rch_37` | エンタメ～テレDEEP | Absent from the same dated grid. |
| `rch_98` | セクシーエンタメチャンネル | Absent from the same dated grid. |
| `rch_40` | 刺激ストロング | Absent from the same dated grid. |
| `rch_42` | 映画（年齢制限あり） | Absent from the same dated grid. |
| `fastch_v2_busns` | ビジネス・プレミアム | Fast TV describes the exact service but publishes no dated programme grid on its public channel page. |
| `fastch_v2_entns` | エンタメニュース | No current timed public grid for this FAST feed was established. |
| `fastch_v2_bgolf` | GOLF LIFE | No current timed public grid for this FAST feed was established. |
| `fastch_v2_samri` | 時代劇TV | The conventional broadcaster schedule does not establish the FAST feed's times. |
| `fastch_v2_comdy` | LeminoTV | On-demand listings do not establish the FAST feed's times. |
| `fastch_v2_asdrm` | エンタメ・アジア | Weekly schedule images do not provide a validated nightly timed feed. |

Evidence: [Rakuten official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-10-31&platform=WEB), checked through November 3 Japan time; [Fast TV channel catalogue](https://fastv.jp/channel/) and [viewing guide](https://fastv.jp/howto/). No access-control restrictions were bypassed.

## Validation

- `python3 -m unittest discover -v`: 78 tests passed.
- Required 48-hour live-playlist build: passed with 1,888 programmes across 29 active live channels, 1,885 current/future. Latest programme ends November 3 at 02:50 JST.
- 1,262 bilingual titles and 1,149 bilingual descriptions; Japanese fallback remains available.
- Refreshed `output/epg.xml`, `cache/translations.json`, and `config/channel_status.json`.

## Remaining live gaps

All 24 uncovered identities remain: `rch_100`, `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `fastch_v2_busns`, `fastch_v2_entns`, `fastch_v2_bgolf`, `fastch_v2_samri`, `fastch_v2_comdy`, `fastch_v2_asdrm`, `fastch_v2_kids`, `fastch_v2_pett1`, `fastch_v2_camng`, `fastch_v2_travl`, `fastch_v2_recip`, `fastch_v2_news1`, `fastch_v2_jpthp`, `fastch_v2_snyon`, `fastch_v2_goshogi`, `fastch_v2_hokkaido`, `fastch_v2_tokai`, and `fastch_v2_krdrm`. The latter 12 FAST feeds retain the source findings from the [October 29 review](2026-10-29-live-expansion.md).
