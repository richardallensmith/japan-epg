# 2026-10-12 conventional satellite expansion

Enabled 14 additional exact playlist identities using G.GUIDE's shared BS lineup. No channels were grouped or blocked in this batch. The live inventory contains 167 entries: 40 enabled and 127 pending (74 conventional; 53 FAST/Rakuten). FAST work remains deferred. Every live identity is recorded in `config/channel_status.json`; configuration alone does not count as enabled.

## Enabled batch

| Exact playlist name | Exact tvg-id | Source service ID | Programmes |
|---|---|---|---|
| BS 10 | `BS10_jp` | `200` | 36 |
| JCOM BS | `J-COM-BS_jp` | `260` | 39 |
| BS Yoshimoto | `BSよしもと_jp` | `265` | 43 |
| WOWOW Prime | `CH.621` | `191` | 32 |
| WOWOW Live | `CH.622` | `192` | 20 |
| WOWOW Cinema | `CH.623` | `193` | 15 |
| BS 10 Premium | `CH.625` | `201` | 17 |
| WOWOW Plus | `CH.630` | `252` | 15 |
| Fishing Vision | `rch_46` | `251` | 33 |
| Green Channel | `CH.688` | `234` | 32 |
| JSport 1 | `CH.603` | `242` | 18 |
| JSport 2 | `CH.604` | `243` | 19 |
| JSport 3 | `CH.606` | `244` | 19 |
| JSport 4 | `CH.605` | `245` | 15 |

## Live validation

- Full feed: 1593 programmes across all 40 enabled channels.
- Coverage: 2026-10-12T17:30:00+09:00 through 2026-10-14T04:30:00+09:00.
- Bilingual titles: 1593; bilingual descriptions: 1406.
- All 51 offline tests passed. Independent saved-XML validation against the live playlist passed.
- Exact channel IDs, source service IDs, station positions, current/future coverage, +0900 timestamps, bilingual metadata, duplicates, overlaps, sparse schedules, and placeholder-only schedules checked.
- Output was generated solely from real current source listings. No fixture or sample schedules were used.

## Sources and implementation

New batch: [G.GUIDE BS listings](https://bangumi.org/epg/bs). Official [WOWOW timetable](https://www.wowow.co.jp/schedule/) and [J SPORTS programme guide](https://www.jsports.co.jp/program_guide/) were considered; the shared public G.GUIDE listings provide the practical reusable source. The existing 26 channels continue to use the [NHK official public timetable](https://www.nhk.jp/timetable/) and G.GUIDE Tokyo/Osaka/BS adapters.

Each new mapping pins both a station label/line and its source service ID, protecting truncated or ambiguous station names. Reviewed recurring translations cover Off Air, Information, and Programme Guide. Translation caching and manual overrides remain in place.

Fixed the scheduled build's null MyMemory response crash, added bounded retries for transient Google transport/server failures, and retained rate-limit failover. Validation now runs before atomic replacement of the existing feed. The workflow sends a contact email only when the owner has deliberately configured the optional secret; no default contact address is sent.

Publication is gated on full validation. The deployment workflow and direct public-feed verification are recorded in this run's automation memory and completion response after the commit is pushed.
