# 2026-11-02 nightly live EPG review

The confirmed-live playlist contains 54 channels. Twelve uncovered live identities were reviewed. Bloomberg TV+ gained a validated mapping; 24 live channels remain uncovered. Existing mappings for absent or dead upstream streams were preserved. No dead or unpublished channel mapping was changed.

## Selected live batch

| Exact `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_70` | Bloomberg TV+ | Added. Rakuten's official dated grid identified channel 70, its exact playlist stream URL, and 35 current/future English programme entries in the 48-hour build. |
| `rch_100` | 囲碁・将棋ライト (R) | Rakuten's dated grid omitted this exact channel November 2–4; its disabled historical mapping was retained. |
| `rch_65` | キッズ | Omitted from the same dated grid; no current timed row. |
| `rch_37` | エンタメ～テレDEEP | Omitted from the same dated grid; no current timed row. |
| `rch_98` | セクシーエンタメチャンネル | Omitted from the same dated grid; no current timed row. |
| `rch_40` | 刺激ストロング | Omitted from the same dated grid; no current timed row. |
| `rch_42` | 映画（年齢制限あり） | Omitted from the same dated grid; no current timed row. |
| `fastch_v2_busns` | ビジネス・プレミアム | No public dated programme grid for this exact FAST feed was established. |
| `fastch_v2_entns` | エンタメニュース | No public current timed grid for this FAST feed was established. |
| `fastch_v2_bgolf` | GOLF LIFE | Fast TV's public channel page describes the service but has no dated programme grid. |
| `fastch_v2_samri` | 時代劇TV | The conventional broadcaster guide does not establish this separate FAST feed's times. |
| `fastch_v2_comdy` | LeminoTV | The public channel page and on-demand catalogue do not establish this FAST feed's transmission times. |

Evidence: [Rakuten official dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-02&platform=WEB), checked through November 4 Japan time; [Fast TV channel catalogue](https://fastv.jp/channel/) and [viewing guide](https://fastv.jp/howto/). Fast TV says its app has a programme guide, but its public pages do not supply dated entries tied to these exact playlist IDs. Bloomberg's source title is `[英語]ﾌﾞﾙｰﾑﾊﾞｰｸﾞTV＋`; its source channel ID and manifest URL were independently checked against `rch_70` in the live playlist. The pinned November 2 fixture preserves real source entries and checks English metadata and stream identity.

## Validation

- `python3 -m unittest discover -v`: 79 tests passed.
- Required 48-hour live-playlist build: passed with 2,044 programmes across 30 active live channels; 35 current/future Bloomberg entries. The latest programme ends November 5 at 02:45 JST.
- 1,301 bilingual titles and 1,203 bilingual descriptions; source-language fallback remains available.
- Refreshed `output/epg.xml`, `cache/translations.json`, and `config/channel_status.json`.

## Remaining live gaps

All 24 uncovered identities remain: `rch_100`, `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `fastch_v2_busns`, `fastch_v2_entns`, `fastch_v2_bgolf`, `fastch_v2_samri`, `fastch_v2_comdy`, `fastch_v2_asdrm`, `fastch_v2_kids`, `fastch_v2_pett1`, `fastch_v2_camng`, `fastch_v2_travl`, `fastch_v2_recip`, `fastch_v2_news1`, `fastch_v2_jpthp`, `fastch_v2_snyon`, `fastch_v2_goshogi`, `fastch_v2_hokkaido`, `fastch_v2_tokai`, and `fastch_v2_krdrm`. The latter 13 FAST feeds retain the source findings from the [October 29 review](2026-10-29-live-expansion.md) and the [November 1 review](2026-11-01-live-expansion.md).
