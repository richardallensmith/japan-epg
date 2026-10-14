# 2026-10-14 CS movie, drama, and entertainment expansion

Enabled 17 additional exact live playlist identities on one shared G.GUIDE CS lineup. No channels were grouped or blocked in this batch. All 167 live identities were reconciled: 57 enabled and 110 pending (57 conventional; 53 FAST/Rakuten). FAST remains deferred; completion has not been reached and the automation remains active.

## Enabled batch

| Exact playlist name | Exact tvg-id | Source service ID | Programmes |
|---|---|---|---|
| Toei Channel | `CH.629` | `218` | 28 |
| Eisei Gekijo | `CH.628` | `219` | 26 |
| Neco Channel | `rch_59` | `223` | 27 |
| The Cinema | `CH.631` | `227` | 16 |
| Movie Plus | `CH.632` | `240` | 20 |
| Jidaigeki Senmon | `CH.662` | `292` | 31 |
| Family Gekijyo | `CH.660` | `293` | 23 |
| Home Drama Channel | `CH.661` | `294` | 30 |
| TBS Channel 1 | `CH.616` | `296` | 30 |
| TBS Channel 2 | `CH.617` | `297` | 36 |
| TV Asahi Channel 1 | `CH.611` | `298` | 39 |
| TV Asahi Channel 2 | `CH.612` | `299` | 31 |
| Nittele Plus | `CH.619` | `300` | 39 |
| Channel Ginga | `CH.664` | `305` | 30 |
| Fuji TV ONE | `CH.614` | `307` | 36 |
| Fuji TV TWO | `CH.615` | `308` | 37 |
| Fuji TV NEXT | `CH.613` | `309` | 26 |

## Live validation

- Full saved feed: 2072 programmes across all 57 enabled channels.
- Coverage: 2026-10-14T08:50:00+09:00 through 2026-10-15T23:00:00+09:00 (JST).
- English-title audit: 0 titles retain Japanese characters after metadata cleanup.
- Bilingual titles: 2072; bilingual descriptions: 1881.
- All 59 offline tests passed. Independent saved-XML validation against the freshly downloaded live playlist passed.
- Exact IDs, station labels/positions, event service IDs, current/future coverage, +0900 timestamps, bilingual metadata, duplicate/overlapping intervals, sparse schedules, and placeholder-only schedules checked.
- An independent source audit also passed all 17 CS channels, with 508 current/future programmes at audit time. Counts may change as programmes end or sources update.
- Builds fetch real current listings. Offline fixture rows are exclusively parser/identity regressions; no fixtures or sample data enter the published feed.

## Sources and implementation

[G.GUIDE CS listings](https://bangumi.org/epg/cs) supplies this entire batch. Each source service number and full channel name was cross-checked against [SKY PerfecTV’s official channel list](https://www.skyperfectv.co.jp/program/schedule/basic/?shrink=channel). Existing channels continue to use [NHK’s official timetable](https://www.nhk.jp/timetable/) and the G.GUIDE Tokyo, Osaka, and BS lineups.

Added the replaceable CS lineup endpoint to the existing G.GUIDE adapter. All 17 mappings pin exact playlist names and IDs, source labels including visible channel numbers, lineup positions, and event service IDs. Tests cover swapped TBS, TV Asahi, and Fuji rows even when their truncated labels are ambiguous.

The source returns HTTP 404 for yesterday’s CS page after the broadcast boundary. Only an expired previous date’s 404 may be skipped after 05:00 JST. Before that boundary, or for any current/future date, it remains fatal. HTTP 403, 429, server failures, malformed/empty data, and mapping drift remain fatal. Complete feed validation remains required before atomic replacement.

Reviewed recurring-title mappings use [Fuji’s Sazae-san spelling](https://www.fujitv.com/animation/sazae-san/) and [Toei’s Kamen Rider Gavv spelling](https://www.kamen-rider-official.com/series/gavv/). CS dubbing/premiere flags are rendered as English title labels; technical audio symbols are excluded from English translation input. Japanese originals, English-first XMLTV ordering, translation caching, and manual overrides are preserved. No default contact email is sent to translation providers.

## Publication

Publication is gated on the full test suite and all enabled live channels passing validation. The resulting main commit, GitHub Pages workflow, public XML validation, and artifact comparison are recorded in automation memory and the completion response after deployment.
