# Japan EPG

An English-first XMLTV generator for Japanese IPTV players. The current feed covers 17 major terrestrial and BS services, preserving the original Japanese metadata alongside translated English metadata.

The playlist remains the authority for channel identity. The generator refuses to write a feed if any live playlist ID differs from its configured, reviewed value.

## Current channels

| Playlist name | Exact `tvg-id` | Schedule service |
|---|---|---|
| NHK G | `NHK東京・総合_jp` | NHK Tokyo area `130`, service `g1` |
| NHK E | `NHK東京・教育_jp` | NHK Tokyo area `130`, service `e1` |
| NHK BS | `NHK・BS_jp` | NHK Tokyo area `130`, service `s1` |
| NTV | `日本テレビ_jp` | G.GUIDE Tokyo, station `日テレ1` |
| TV Asahi | `テレビ朝日_jp` | G.GUIDE Tokyo, station `テレビ朝日` |
| TBS | `TBS_jp` | G.GUIDE Tokyo, station `TBS1` |
| TV Tokyo | `テレ東_jp` | G.GUIDE Tokyo, station `テレ東` |
| Fuji TV | `フジテレビ_jp` | G.GUIDE Tokyo, station `フジテレビ` |
| TOKYO MX1 | `TOKYO・MX_jp` | G.GUIDE Tokyo, guarded line 8 |
| TOKYO MX2 | `TOKYO・MX2_jp` | G.GUIDE Tokyo, guarded line 9 |
| BS NTV | `BS日テレ_jp` | G.GUIDE BS, station `BS日テレ` |
| BS Asahi | `BS朝日_jp` | G.GUIDE BS, station `BS朝日1` |
| BS-TBS | `BS-TBS_jp` | G.GUIDE BS, station `BS-TBS` |
| BS TV Tokyo | `BSテレ東_jp` | G.GUIDE BS, station `ＢＳテレ東` |
| BS Fuji | `BSフジ_jp` | G.GUIDE BS, station `BSフジ・181` |
| BS11 | `BS11-イレブン_jp` | G.GUIDE BS, guarded line 12 |
| BS12 TwellV | `BS12トゥエルビ_jp` | G.GUIDE BS, guarded line 13 |

Playlist: <https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u>

NHK listings come from NHK's official public timetable JSON, the same `api.nhk.jp/r8` endpoint used by <https://www.nhk.jp/timetable/>. Commercial listings come from G.GUIDE's broadcaster-supplied [Tokyo terrestrial](https://bangumi.org/epg/td) and [BS](https://bangumi.org/epg/bs) schedules. Each adapter is isolated under `src/fetch/`, so a source can be replaced without changing playlist matching, normalization, translation, XML generation, or validation.

## Generate and validate

Python 3.11 or newer is required. There are no third-party runtime dependencies.

```bash
python3 -m unittest discover -v
python3 -m src.main
```

The second command downloads the current playlist and official schedule, translates cache misses, writes `output/epg.xml` atomically, and validates the result. A failed fetch, empty schedule, translation failure, ID mismatch, or validation failure exits nonzero. It never substitutes fixture or sample programmes.

Useful options:

```bash
python3 -m src.main --days 1 --description-chars 48 --output output/epg.xml
```

Build only selected configured channels by repeating `--channel`:

```bash
python3 -m src.main --channel nhk_g_tokyo --channel nhk_e_tokyo
```

NHK broadcast days cross midnight, so the source adapter fetches the overlapping previous/current/next broadcast dates and then retains only current/upcoming entries in the requested window.

## Translation policy

Translation is layered in this order:

1. Manual exact overrides in `config/translation_overrides.yaml`.
2. Established recurring-title mappings in `config/title_overrides.yaml`.
3. Deterministic rules for recurring structures such as Grand Sumo basho/day labels, serial drama digests, regional news, episode numbers, and special/finale markers.
4. Cached machine translation for variable subtitles, uncatalogued titles, genres, and concise description summaries.

The full Japanese title and full Japanese description from NHK are always retained. The English description is intentionally a concise translated summary (48 Japanese characters by default) to keep the no-key first-run translation volume reasonable. Increase `--description-chars` when using a higher-quota setup.

The fallback layer is a replaceable provider chain using Google Translate's public endpoint and MyMemory. Results are stored in `cache/translations.json`, making future refreshes stable and reducing external requests. The workflow identifies the public project with the repository owner's GitHub no-reply address for MyMemory's documented higher quota; set a `MYMEMORY_EMAIL` repository secret to override it. Text sent for a cache miss is shared with the provider; replace the providers or pre-fill manual overrides if that is undesirable.

Do not silently map a mistranslated proper name in code. Add a reviewed title/description override so future rebuilds remain deterministic.

## XMLTV compatibility and validation

The output uses timezone-aware XMLTV timestamps such as `20260926190000 +0900`. They remain in Japan time; TiviMate and Sparkle convert them for display.

Validation fails on:

- a missing or mismatched playlist channel ID;
- zero programme entries or zero current/future entries for any configured channel;
- malformed timestamps or a stop time not after its start;
- duplicate channels or programmes;
- programmes assigned to another channel;
- missing bilingual titles;
- a feed whose last programme is suspiciously near/past the current time.

Japanese and English titles are emitted for every programme. Both descriptions are emitted whenever the source has a description. XML is built with the standard library XML writer, which escapes titles and descriptions safely.

## Structure

```text
config/                 channel and translation policy
src/fetch/              replaceable schedule adapters
src/playlist.py         M3U parsing and identity matching
src/normalize.py        ordering and duplicate prevention
src/translate.py        mappings, rules, MT, and cache
src/xmltv.py            XMLTV serialization
src/validate.py         fail-closed feed checks
src/main.py             end-to-end command
cache/translations.json stable translation cache
output/epg.xml          generated feed
tests/                  offline unit tests
.github/workflows/      prepared six-hour refresh workflow
```

## Published GitHub Pages feed

The player-ready feed is published at:

```text
https://richardallensmith.github.io/japan-epg/epg.xml
```

Repository: <https://github.com/richardallensmith/japan-epg>

`.github/workflows/update-epg.yml` runs tests, fetches current listings, validates the XML, and republishes the feed every six hours. GitHub Pages uses enforced HTTPS. The deploy job remains gated by the repository variable below so publication can be paused without deleting the workflow:

```text
ENABLE_PAGES_PUBLISH=true
```

Use the published `epg.xml` URL directly as an EPG source in TiviMate or Sparkle.

## Further expansion

Add channel records under `config/channels.yaml`, then implement or reuse a schedule adapter under `src/fetch/`. Keep each playlist ID pinned and covered by an offline fixture test before enabling the channel.

FAST channels are intentionally deferred until the major terrestrial, BS, and conventional specialty services are complete.
