# Japan EPG

An English-first XMLTV generator for Japanese IPTV players. The initial vertical slice covers **NHK G Tokyo / NHK総合1・東京** and preserves the original Japanese metadata alongside translated English metadata.

The playlist remains the authority for channel identity. The generator refuses to write a feed if the live playlist's NHK G ID differs from the configured, reviewed value.

## Current channel

| Playlist name | Exact `tvg-id` | Schedule service |
|---|---|---|
| NHK G | `NHK東京・総合_jp` | NHK Tokyo area `130`, service `g1` |

Playlist: <https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u>

Primary listings source: NHK's official public timetable JSON, the same `api.nhk.jp/r8` endpoint used by <https://www.nhk.jp/timetable/>. The adapter is isolated in `src/fetch/nhk.py` so another source can be added without changing normalization, translation, XML generation, or validation.

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

NHK broadcast days cross midnight, so the source adapter fetches the overlapping previous/current/next broadcast dates and then retains only current/upcoming entries in the requested window.

## Translation policy

Translation is layered in this order:

1. Manual exact overrides in `config/translation_overrides.yaml`.
2. Established recurring-title mappings in `config/title_overrides.yaml`.
3. Deterministic rules for recurring structures such as Grand Sumo basho/day labels, serial drama digests, regional news, episode numbers, and special/finale markers.
4. Cached machine translation for variable subtitles, uncatalogued titles, genres, and concise description summaries.

The full Japanese title and full Japanese description from NHK are always retained. The English description is intentionally a concise translated summary (48 Japanese characters by default) to keep the no-key first-run translation volume reasonable. Increase `--description-chars` when using a higher-quota setup.

The default fallback provider is the public MyMemory API. Results are stored in `cache/translations.json`, making future refreshes stable and reducing external requests. Set `MYMEMORY_EMAIL` to an email accepted by that provider for its identified-user quota. Text sent for a cache miss is shared with that provider; replace `MyMemoryProvider` or pre-fill manual overrides if that is undesirable.

Do not silently map a mistranslated proper name in code. Add a reviewed title/description override so future rebuilds remain deterministic.

## XMLTV compatibility and validation

The output uses timezone-aware XMLTV timestamps such as `20260926190000 +0900`. They remain in Japan time; TiviMate and Sparkle convert them for display.

Validation fails on:

- a missing or mismatched playlist channel ID;
- zero programme entries or zero current/future entries;
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

## Expansion

Add channel records under `config/channels.yaml`, then implement or reuse a `ScheduleSource` adapter. The design is ready for NHK E, NHK BS, NTV, TV Asahi, TBS, TV Tokyo, and Fuji TV, but they are deliberately not enabled until NHK G has been observed in the target players.
