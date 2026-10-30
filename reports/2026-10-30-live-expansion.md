# 2026-10-30 nightly live EPG review

The confirmed-live playlist has 53 channels. A batch of 12 uncovered live identities was reviewed. None had a validated current/future timed source, so no new mapping was enabled. All 29 existing active live mappings remain enabled; no dead or unpublished mapping was changed.

## Selected live batch

| Exact live `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_100` | 囲碁・将棋ライト (R) | Rakuten's official dated grid omitted this ID for October 30–November 2. Its historical mapping remains configured and disabled pending source recovery. |
| `rch_65` | キッズ | Absent from the same dated grid; no current timed row. |
| `rch_37` | エンタメ～テレDEEP | Absent from the same dated grid; no current timed row. |
| `rch_98` | セクシーエンタメチャンネル | Absent from the same dated grid; no current timed row. |
| `rch_40` | 刺激ストロング | Absent from the same dated grid; no current timed row. |
| `rch_42` | 映画（年齢制限あり） | Absent from the same dated grid; no current timed row. |
| `fastch_v2_busns` | ビジネス・プレミアム | Fast TV's public catalogue describes the channel, but has no dated grid. |
| `fastch_v2_entns` | エンタメニュース | No public current timed grid for this separate FAST feed was established. |
| `fastch_v2_bgolf` | GOLF LIFE | No public current timed grid for this separate FAST feed was established. |
| `fastch_v2_samri` | 時代劇TV | The conventional broadcaster schedule does not establish this FAST feed's transmission times. |
| `fastch_v2_comdy` | LeminoTV | Lemino's on-demand catalogue does not establish this FAST feed's transmission times. |
| `fastch_v2_asdrm` | エンタメ・アジア | The broadcaster has current weekly schedules, but publishes them as images. No reliable nightly extraction with programme-level validation was established. |

Sources: [Rakuten dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-10-30&platform=WEB), [Fast TV channel catalogue](https://fastv.jp/channel/), [Fast TV viewing guide](https://fastv.jp/howto/), and [エンタメ・アジアFree weekly guide](https://entameasia.jp/article/news/20250603010303.html). The Rakuten API was checked through November 2, Japan time. No access-control restrictions were bypassed.

## Existing live source repair

The first production build failed because Rakuten's Reuters 60 (`rch_120`) grid contained a one-hour overlap on November 1: *Reuters Evening News* was listed 00:00–03:00 and *Reuters Morning News* 02:00–04:00 JST. The R Channel adapter now omits both conflicting entries for Reuters 60 and retains the uncontested source entries. It does not invent or alter times. A regression test covers this behavior; material overlaps on other R Channel feeds still fail validation.

## Validation

- `python3 -m unittest discover -v`: 78 tests passed.
- Required two-day build with the live playlist active and the full upstream playlist used for reconciliation: passed; 1,849 programmes across 29 active live channels, including 1,848 current/future entries. Latest programme ends November 2 at 02:00 JST.
- Reuters 60 retained 27 uncontested current/future entries after the two conflicting source entries were omitted.
- 1,250 bilingual titles and 1,141 bilingual descriptions; source-language fallback remains available.
- Refreshed `output/epg.xml`, `cache/translations.json`, and `config/channel_status.json`. No channel was added, removed, or disabled by this run.

## Remaining live gaps

All 24 uncovered live identities remain: `rch_100`, `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `fastch_v2_busns`, `fastch_v2_entns`, `fastch_v2_bgolf`, `fastch_v2_samri`, `fastch_v2_comdy`, `fastch_v2_asdrm`, `fastch_v2_kids`, `fastch_v2_pett1`, `fastch_v2_camng`, `fastch_v2_travl`, `fastch_v2_recip`, `fastch_v2_news1`, `fastch_v2_jpthp`, `fastch_v2_snyon`, `fastch_v2_goshogi`, `fastch_v2_hokkaido`, `fastch_v2_tokai`, and `fastch_v2_krdrm`. The latter 12 FAST feeds retain the findings in the [October 29 review](2026-10-29-live-expansion.md).
