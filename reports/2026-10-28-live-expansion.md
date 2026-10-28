# 2026-10-28 nightly live EPG review

The confirmed-live playlist has 53 channels. No new EPG mapping passed current/future source validation in this batch. The validated 48-hour build has 29 active channels and 1,863 current/future programmes. The remaining 24 live channels have no usable EPG coverage. No dead or unpublished upstream channel was changed.

## Selected batch: 12 live gaps

| Live identity | Finding |
|---|---|
| `rch_100` 囲碁・将棋ライト (R) | Previously enabled, but Rakuten's dated public grid omitted source channel 100 for October 27–30. Its historical source mapping and exact `tvg-id` remain configured; active generation is disabled pending renewed source validation. The live playlist's English-first name is recorded as an alias. |
| `rch_65` キッズ | Absent from Rakuten's current dated grid; no matching timed row. |
| `rch_37` エンタメ～テレDEEP | Absent from Rakuten's current dated grid; no matching timed row. |
| `rch_98` セクシーエンタメチャンネル | Absent from Rakuten's current dated grid; no matching timed row. |
| `rch_40` 刺激ストロング | Absent from Rakuten's current dated grid; no matching timed row. |
| `rch_42` 映画（年齢制限あり） | Absent from Rakuten's current dated grid; no matching timed row. |
| `fastch_v2_busns` ビジネス・プレミアム | Fast TV identifies the service, but no public dated programme feed was established. |
| `fastch_v2_entns` エンタメニュース | Fast TV identifies the service, but no public dated programme feed was established. |
| `fastch_v2_bgolf` GOLF LIFE | Fast TV identifies the service, but no public dated programme feed was established. |
| `fastch_v2_samri` 時代劇TV | Fast TV identifies this FAST service. The conventional 時代劇専門チャンネル guide is not evidence of the FAST schedule. |
| `fastch_v2_comdy` LeminoTV | Fast TV identifies this FAST service. Lemino on-demand data does not establish the FAST transmission times. |
| `fastch_v2_asdrm` エンタメ・アジア | The broadcaster publishes current weekly schedules, but only as images. No reliable nightly extraction and validation path was established. |

The five unconfigured R Channel feeds were checked against [Rakuten's dated public grid](https://backendapi.channel.rakuten.co.jp/platform/content/programs?date=2026-10-28&platform=WEB). The FAST identities were checked against [Fast TV's channel catalogue](https://fastv.jp/channel/) and [viewing guide](https://fastv.jp/howto/). The [エンタメ・アジア Free broadcaster page](https://entameasia.jp/article/news/20250603010303.html) links current weekly schedule images. A third-party XMLTV snapshot with matching FAST IDs was last updated in May 2026, so it was not treated as current schedule evidence.

## Validation

- `python3 -m unittest discover -v`: 77 tests passed.
- Required `--days 2` live-playlist build: passed after excluding `rch_100` from active generation; 1,863 current/future programmes, latest programme ends 2026-10-31 02:56 JST. The initial build failed because the live playlist name for `rch_100` had changed; with its alias pinned, the build then failed because Rakuten omitted channel 100. No stale schedule was published.
- English-first metadata: 1,255 bilingual titles and 1,162 bilingual descriptions. Source-language fallback remained available.
- The historical `rch_100` mapping is retained for future revalidation. No other configured source was removed or disabled.

## Remaining live channels without usable EPG

The 12 examined above, plus: アニマックス FREE, ペットTV, キャンプ・アウトドア, 今日のごはんなに?, 観るたび, 丸ごと九州, ぴあ落語ざんまい, FASHIONPLUS, 囲碁・将棋ライト (FAST), 丸ごと北海道, 東海ロキポ, and 韓流チャンネル. These twelve were not part of this run's selected batch.
