# 2026-11-03 nightly live EPG review

The confirmed-live playlist contains 54 channels: 30 have enabled mappings and 24 remain uncovered. Twelve uncovered live identities were examined. None had a source that could produce validated current/future programme entries without guessing, so no mapping was enabled. Existing mappings for currently absent upstream streams were preserved. No dead or unpublished channel mapping was changed.

## Selected live batch

| Exact `tvg-id` | Channel | Finding |
|---|---|---|
| `rch_65` | キッズ | Omitted from R Channel's dated grid on November 2–5; no current timed rows for this exact stream. |
| `rch_37` | エンタメ～テレDEEP | Omitted from the same dated grid. |
| `rch_98` | セクシーエンタメチャンネル | Omitted from the same dated grid. |
| `rch_40` | 刺激ストロング | Omitted from the same dated grid. |
| `rch_42` | 映画（年齢制限あり） | Omitted from the same dated grid. |
| `rch_100` | 囲碁・将棋ライト (R) | Omitted from the same dated grid; its disabled historical mapping remains in place. |
| `fastch_v2_busns` | ビジネス・プレミアム (FAST) | Fast TV describes the channel but publishes no current dated grid on its public channel page. |
| `fastch_v2_entns` | エンタメニュース (FAST) | No current timed public grid tied to this FAST feed was established. |
| `fastch_v2_bgolf` | GOLF LIFE (FAST) | The public channel page identifies the separate FAST service but provides no current dated entries. |
| `fastch_v2_samri` | 時代劇TV (FAST) | Fast TV identifies the separate stream; the conventional broadcaster schedule does not establish its transmission times. |
| `fastch_v2_comdy` | LeminoTV (FAST) | Public channel information and on-demand titles do not establish this linear feed's programme times. |
| `fastch_v2_asdrm` | エンタメ・アジア (FAST) | The provider posts current and next-week schedules as images, but no dependable machine-readable timed feed for automatic daily validation was established. |

Sources checked: [R Channel dated grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-11-03&platform=WEB), [Fast TV channel catalogue](https://fastv.jp/channel/), [Fast TV viewing guide](https://fastv.jp/howto/), and [エンタメ・アジア Free weekly schedule](https://entameasia.jp/article/news/20250603010303.html). R Channel's grid returned 57 channel rows each day from November 2 through 5, but none for the six exact IDs above. Fast TV's app offers a programme guide, yet the public pages checked did not provide reliably parseable current/future rows for the selected feeds.

## Validation

- `python3 -m unittest discover -v`: 79 tests passed.
- Required 48-hour live-playlist build: passed with 1,988 programmes across 30 active live channels (1,986 current/future). The latest programme ends November 6 at 02:00 JST.
- 1,296 bilingual titles and 1,202 bilingual descriptions. The build refreshed `output/epg.xml`, `cache/translations.json`, and `config/channel_status.json`.

## Remaining live gaps

All 24 uncovered identities remain: `rch_100`, `rch_65`, `rch_37`, `rch_98`, `rch_40`, `rch_42`, `fastch_v2_busns`, `fastch_v2_entns`, `fastch_v2_bgolf`, `fastch_v2_samri`, `fastch_v2_comdy`, `fastch_v2_asdrm`, `fastch_v2_kids`, `fastch_v2_pett1`, `fastch_v2_camng`, `fastch_v2_travl`, `fastch_v2_recip`, `fastch_v2_news1`, `fastch_v2_jpthp`, `fastch_v2_snyon`, `fastch_v2_goshogi`, `fastch_v2_hokkaido`, `fastch_v2_tokai`, and `fastch_v2_krdrm`.
