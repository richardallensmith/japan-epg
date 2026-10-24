# Nightly Japan EPG Expansion

Work autonomously in the `japan-epg` repository.

## Primary goal

Add reliable EPG coverage for channels that are currently confirmed live but do not yet have usable programme data.

The authoritative live-channel inventory is:

`output/japan-live.m3u`

The full upstream inventory remains:

`https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u`

Existing EPG mappings for channels that are currently dead or removed must be preserved. Do not delete or disable them merely because the stream is not presently in `japan-live.m3u`; if those streams recover, their existing EPG mappings should become usable again automatically.

## Selection order for each nightly run

1. Read `output/japan-live.m3u`.
2. Read `config/channels.yaml`, `config/channel_status.json`, and the existing source adapters.
3. Identify confirmed-live channels that do not currently have an enabled, validated EPG mapping.
4. Select up to 5 of those uncovered live channels for work.
5. Prefer candidates where a trustworthy schedule source can be established with reasonable effort.
6. Prefer conventional broadcaster schedules and official or established guide sources over brittle scraping.
7. If a live channel is a FAST/streaming channel with no trustworthy public schedule, leave it unchanged and record why rather than inventing programme data.
8. Only after all reasonable confirmed-live gaps are covered or explicitly deferred should the run spend time expanding EPG mappings for currently dead/unpublished upstream channels.

## Mapping rules

- Do not guess channel equivalence.
- Do not infer that a parent channel, regional variant, subchannel, 4K feed, FAST feed, or similarly named service shares another channel's schedule without source evidence.
- Preserve exact playlist identity and `tvg-id` semantics.
- Preserve existing mappings unless there is clear evidence they are wrong.
- Do not remove historical mappings because a stream is currently dead.
- Do not fabricate programme titles, descriptions, genres, or times.
- English-first bilingual metadata remains the target when translation is available.
- Translation failure must not block publishing current schedule data; source Japanese is acceptable fallback text.
- Never attempt access-control circumvention.

## Production validation

The production EPG uses the confirmed-live playlist for active schedule generation and the full upstream playlist only for inventory reconciliation.

Validate with:

```bash
python -m unittest discover -v
python -m src.main \
  --days 2 \
  --playlist output/japan-live.m3u \
  --inventory-playlist https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u
```

A channel must not be marked complete unless its current schedule source is actually producing valid current/future programme entries.

## Required updates

For each successfully added channel, update all project files required by existing conventions, which may include:

- `config/channels.yaml`
- `config/channel_status.json`
- source adapters
- fixtures
- tests
- title/translation overrides
- documentation or validation reports

Do not leave partial experiments or speculative mappings in the working tree.

## End-of-run report

Summarize:

- live channels successfully given EPG coverage
- live candidates examined but left unchanged, with reason
- any dead/unpublished channels touched, if any
- test result
- 48-hour live-playlist build result
- files changed
- source/mapping concerns
- remaining live channels without EPG coverage

Do not push or publish directly. Leave only complete, validated changes in the working tree for the wrapper to commit and publish safely.
