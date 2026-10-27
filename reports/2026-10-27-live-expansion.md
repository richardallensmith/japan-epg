# Live EPG expansion — 2026-10-27

## Added and validated

The 12-channel batch uses [R Channel's dated programme grid](https://channel.rakuten.co.jp/schedule). Each mapping is pinned to the exact live-playlist `tvg-id`, R Channel numeric ID and source title. At build time, the grid's stream URL must equal the live-playlist stream URL. The source yielded current and future entries for every channel in the 48-hour build.

| Live channel | `tvg-id` | Programme entries |
|---|---|---:|
| 日テレNEWS | `rch_47` | 54 |
| FNNプライムオンライン | `rch_108` | 54 |
| MBSニュース | `rch_115` | 54 |
| 日テレNEWSセレクト | `rch_101` | 54 |
| 共同通信News | `rch_56` | 18 |
| NewsWorld | `rch_103` | 107 |
| オリコンニュース | `rch_54` | 18 |
| Euronews | `rch_90` | 170 |
| Reuters 60 | `rch_120` | 29 |
| NTV Pro Wrestling | `rch_97` | 29 |
| ムビドラTV | `rch_34` | 31 |
| 手塚プロダクションTV | `rch_73` | 119 |

The adapter trims only one-second overlaps between adjacent source rows, which occur in the three entertainment schedules. Larger overlaps fail. NewsWorld, Euronews and Reuters 60 use source English metadata; Japanese services retain source Japanese plus translated English where available. The public platform JSON endpoint is not a documented long-term API, so the adapter fails closed if its structure or channel identity changes.

## Validation

- `python3 -m unittest discover -v`: 75 tests passed.
- `python3 -m src.main --days 2 --playlist output/japan-live.m3u --inventory-playlist https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u`: passed; 18 active channels, 1,348 current/future entries. Feed range: 2026-10-27 14:00 JST to 2026-10-29 21:25:30 JST.
- The full upstream playlist was used only for inventory reconciliation. Historical channel mappings were retained; no dead or unpublished channel mapping was changed.

## Examined and left unchanged

The batch cap was reached with 12 successful channels. Twelve other live R Channel feeds already have a matching ID and stream URL in the current official grid, but were not mapped or validated in this run: that’s 70s, that’s 80s, that’s 90s00s, that’s Rock, 麻雀, パチンコ・パチスロ, ぷれいば！, ワンニャンチャンネル, 九州・沖縄　街ネタ, QVC, GSTV, and 囲碁・将棋ライト (R). The Rakuten QVC and GSTV feeds remain distinct from their CS versions. These 12 are candidates for the next batch, subject to their own current listing validation.

Five live Rakuten playlist IDs did not match a channel ID in the current R Channel grid: キッズ, エンタメ～テレDEEP, セクシーエンタメチャンネル, 刺激ストロング, and 映画（年齢制限あり）. The grid has some similarly named services with different IDs or streams, so these require separate identity review.

The 18 Fast TV feeds remain uncovered. [Fast TV's channel directory](https://fastv.jp/channel/) identifies the services but does not provide a machine-readable dated programme grid there. [エンタメ・アジア Free publishes a weekly schedule image](https://entameasia.jp/article/news/20250603010303.html), but image extraction is unsuitable for an unattended nightly adapter. No schedule was invented or borrowed from a parent channel.

## Remaining confirmed-live gaps

35 channels: 12 R Channel feeds with matching grid identity awaiting a later batch, 5 Rakuten identities needing investigation, and 18 Fast TV feeds without a reliable automated dated guide established here.
