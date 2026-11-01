# 2026-11-01 nightly live EPG review

The confirmed-live playlist contains 53 channels. Twelve uncovered live identities were reviewed. No new mapping was enabled: none had current/future timed listings validated for its exact feed. The 29 existing active live mappings and all historical mappings were preserved. No dead or unpublished channel mapping was changed.

## Selected live batch

| Exact `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_100` | 囲碁・将棋ライト (R) | Rakuten's dated grid omitted this exact channel November 1–4. Its disabled historical mapping was retained for revalidation if listings return. |
| `rch_65` | キッズ | Absent from the same dated grid. |
| `rch_37` | エンタメ～テレDEEP | Absent from the same dated grid. |
| `rch_98` | セクシーエンタメチャンネル | Absent from the same dated grid. |
| `rch_40` | 刺激ストロング | Absent from the same dated grid. |
| `rch_42` | 映画（年齢制限あり） | Absent from the same dated grid. |
| `fastch_v2_busns` | ビジネス・プレミアム | Fast TV identifies the service, but its public pages offer no dated programme grid for the exact feed. |
| `fastch_v2_entns` | エンタメニュース | No current timed public grid for this FAST feed was established. |
| `fastch_v2_bgolf` | GOLF LIFE | No current timed public grid for this FAST feed was established. |
| `fastch_v2_samri` | 時代劇TV | Its separate FAST transmission times cannot be established from the conventional broadcaster's schedule. |
| `fastch_v2_comdy` | LeminoTV | On-demand listings do not establish this FAST feed's transmission times. |
| `fastch_v2_asdrm` | エンタメ・アジア | The provider posts current weekly schedule images; no reliable programme-level nightly extraction and validation was established. |

Evidence: [Rakuten official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-01&platform=WEB), checked through November 4 Japan time; [Fast TV channel catalogue](https://fastv.jp/channel/) and [viewing guide](https://fastv.jp/howto/); [エンタメ・アジア Free provider schedule](https://entameasia.jp/article/news/20250603010303.html). Fast TV says its app includes a guide, but a public dated source tied to these exact playlist IDs was not established. The upstream merged XMLTV was last modified August 13, 2026, so it was not used as current schedule evidence.

## Validation

- `python3 -m unittest discover -v`: 78 tests passed.
- Required 48-hour live-playlist build: passed with 1,997 current/future programmes across 29 active live channels. Latest programme ends November 4 at 03:35 JST.
- 1,284 bilingual titles and 1,177 bilingual descriptions; source-language fallback remains available.
- Refreshed `output/epg.xml`, `cache/translations.json`, and `config/channel_status.json`. No source adapter, mapping, or fixture changed.

## Remaining live gaps

All 24 uncovered identities remain: `rch_100`, `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `fastch_v2_busns`, `fastch_v2_entns`, `fastch_v2_bgolf`, `fastch_v2_samri`, `fastch_v2_comdy`, `fastch_v2_asdrm`, `fastch_v2_kids`, `fastch_v2_pett1`, `fastch_v2_camng`, `fastch_v2_travl`, `fastch_v2_recip`, `fastch_v2_news1`, `fastch_v2_jpthp`, `fastch_v2_snyon`, `fastch_v2_goshogi`, `fastch_v2_hokkaido`, `fastch_v2_tokai`, and `fastch_v2_krdrm`. The latter 12 FAST feeds retain the source findings from the [October 29 review](2026-10-29-live-expansion.md).
