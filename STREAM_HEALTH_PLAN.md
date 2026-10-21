# Stream Health Monitoring Plan

## Purpose

Build a reliable health-checking and playlist-filtering system for the Japan IPTV playlist used by this project.

The system will periodically test every upstream channel from:

`https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u`

It will publish a cleaned playlist containing channels that are currently considered usable, while preserving health history for failed channels so they can be restored automatically if they recover.

The health checker will run primarily on `mozi`. GitHub Actions will provide a secondary backup signal, but GitHub-hosted checks will not initially be authoritative for removing channels.

## Goals

- Detect dead IPTV streams automatically.
- Avoid removing channels because of short-lived provider or network failures.
- Preserve the upstream playlist's channel order and metadata for channels that remain active.
- Restore channels automatically when they recover.
- Detect newly added upstream channels and admit them only after a successful probe.
- Keep health-state history even for channels that are no longer published.
- Publish a stable cleaned M3U that can eventually be used directly by TiviMate and Sparkle.
- Keep the EPG generator aligned with the cleaned playlist.
- Provide a human-readable health summary and machine-readable state.
- Fail safely during large provider outages or checker/network failures.

## Non-goals for v1

- Measuring stream quality.
- Scoring bitrate, buffering, latency, continuity errors, or video quality.
- Distinguishing degraded streams from healthy streams.
- Automatically repairing or replacing dead stream URLs.
- Treating GitHub-hosted probes as authoritative for removals before their behavior is validated.
- Permanently deleting health history for dead or upstream-removed channels.

## Authority and data flow

Primary authority:

1. Upstream M3U provides the current channel inventory and stream URLs.
2. mozi probes the streams.
3. Persistent health state records results over time.
4. The playlist filter applies the rules below.
5. A cleaned playlist is generated.
6. Validated changes are committed and pushed to GitHub.
7. GitHub Pages publishes the cleaned playlist.
8. The EPG project uses the cleaned playlist for active-channel inventory while continuing to reconcile against upstream for newly added channels.

Conceptual flow:

```text
upstream M3U
    |
    v
mozi stream probe
    |
    v
stream_health.json
    |
    +--> health report
    |
    v
playlist filter
    |
    v
output/japan-live.m3u
    |
    v
GitHub Pages
```

## Health-check schedule

Primary checker:

- Host: `mozi`
- Scheduler: systemd user timer
- Frequency: every 6 hours
- Timer should be persistent across reboot.
- Runs should use a small randomized delay to avoid always hitting the upstream provider at the same second.

Secondary checker:

- GitHub Actions may run the same or a reduced probe set.
- Initially, GitHub results are informational only.
- GitHub must not increment authoritative removal counters or remove channels until datacenter-IP behavior has been validated against mozi results.

## Probe definition

Use `ffprobe` as the primary media-level test.

A channel passes when `ffprobe` detects at least one valid media stream of either type:

- audio, or
- video.

A stream does not need to contain both.

A simple HTTP 200 response is not sufficient evidence that a channel works.

Recommended initial probe behavior:

- per-channel media observation window: approximately 10-15 seconds
- hard per-channel timeout: approximately 20 seconds
- no indefinite retries
- capture stderr/error reason for failed probes
- use a normal, non-abusive User-Agent where applicable
- do not attempt authentication bypass, geo-bypass, DRM bypass, or access-control circumvention

## Health states

The machine-readable state should distinguish at least:

- `new`: discovered upstream but has not yet passed a probe
- `healthy`: currently publishable
- `suspect`: has recent failures but has not crossed the removal threshold
- `removed`: excluded from the cleaned playlist because of consecutive failures
- `upstream_removed`: no longer present in the source playlist, retained only for history

These states are operational labels. v1 does not attempt to characterize quality beyond working/dead.

## Failure and recovery policy

### Existing healthy channels

- 1 consecutive failed check: remain published
- 2 consecutive failed checks: mark `suspect`, remain published
- 3-5 consecutive failed checks: remain `suspect`, remain published
- 6 consecutive failed checks: mark `removed` and exclude from cleaned playlist

At a six-hour cadence, six failures represents approximately 36 hours without a successful probe.

Any successful check before removal:

- reset consecutive failures to 0
- return state to `healthy`

### Removed channels

Continue probing removed channels.

Require:

- 2 consecutive successful checks

before restoring the channel to the cleaned playlist.

A failed check during recovery resets the consecutive-success counter.

### Newly discovered upstream channels

A new upstream channel:

- is added to health state immediately
- is not published immediately
- requires 1 successful probe before becoming `healthy`
- after its first success, it can appear in the cleaned playlist

### Channels removed from the upstream playlist

If a channel disappears from the upstream M3U:

- remove it from the cleaned playlist immediately
- retain its historical health record
- mark it `upstream_removed`
- if the same channel later reappears upstream, treat it as a reappearing channel and require at least one fresh successful probe before publication

## Mass-failure safeguard

One bad checker run must not purge a large fraction of the playlist.

Before updating authoritative consecutive-failure counters, calculate the failure rate among channels that were previously healthy or suspect.

Initial safeguard:

- if more than 30% of previously active channels fail in the same run, classify the run as a probable systemic failure
- do not increment failure counters from that run
- do not remove any channels
- preserve individual diagnostic results for review
- report the run as `suppressed_mass_failure`

This threshold should be configurable.

The checker should also suppress removal-counter updates when:

- DNS is broadly failing
- the host has no internet connectivity
- the upstream playlist cannot be fetched
- `ffprobe` is unavailable or broken
- another clear local/systemic checker failure is detected

## Persistent state

Recommended file:

`config/stream_health.json`

Each channel record should retain enough information to make decisions across runs.

Suggested schema:

```json
{
  "version": 1,
  "updated_at": "2026-10-21T00:00:00Z",
  "source_playlist": "https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u",
  "last_run": {
    "started_at": "2026-10-21T00:00:00Z",
    "completed_at": "2026-10-21T00:05:00Z",
    "status": "ok",
    "checked": 167,
    "passed": 150,
    "failed": 17,
    "suppressed": false
  },
  "channels": {
    "stable-channel-key": {
      "tvg_id": "example.jp",
      "name": "Example",
      "url": "https://example.invalid/live.m3u8",
      "state": "healthy",
      "present_upstream": true,
      "first_seen_at": "2026-10-21T00:00:00Z",
      "last_seen_upstream_at": "2026-10-21T00:00:00Z",
      "last_checked_at": "2026-10-21T00:00:00Z",
      "last_success_at": "2026-10-21T00:00:00Z",
      "last_failure_at": null,
      "consecutive_failures": 0,
      "consecutive_successes": 5,
      "last_result": "pass",
      "last_error": null
    }
  }
}
```

The implementation should choose a stable channel key that survives ordinary metadata changes. Prefer exact `tvg-id` where unique and reliable. If `tvg-id` is absent or duplicated, use a deterministic fallback and document it.

Do not key solely on stream URL because URLs may change while the channel identity remains the same.

## Cleaned playlist

Recommended generated output:

`output/japan-live.m3u`

Published URL target:

`https://richardallensmith.github.io/japan-epg/japan-live.m3u`

For every published channel, preserve upstream data as faithfully as possible:

- channel order
- display name
- `tvg-id`
- `tvg-name`
- `tvg-logo`
- group title
- stream URL
- other M3U attributes already present

Do not rewrite metadata unnecessarily.

The cleaned playlist should contain:

- `healthy` channels
- `suspect` channels that have not reached the removal threshold

It should exclude:

- `new` channels that have not yet passed
- `removed` channels
- `upstream_removed` channels

## EPG integration

The EPG generator should continue to reconcile against the upstream playlist so newly added channels can be discovered.

For active production generation:

- use the cleaned playlist as the source of currently publishable channel inventory
- keep exact `tvg-id` validation
- do not silently remap an EPG channel to a different stream
- do not delete historical EPG configuration merely because a stream is temporarily removed

A stream-health failure and an EPG-source failure are separate conditions and should remain separate in project state.

## Human-readable reporting

Generate a summary after each authoritative mozi run.

Recommended output:

`output/stream-health.md`

Include:

- run timestamp
- total upstream channels
- checked
- working
- suspect
- removed
- upstream-removed
- newly discovered
- newly activated
- newly removed
- newly restored
- suppressed/systemic-run status
- channels whose status changed
- concise failure reasons for current suspect/removed channels

Local logs should retain more detailed per-channel diagnostics than the public report.

## Local logging

Recommended state/log directory:

`~/.local/state/japan-epg-health/`

Retain:

- timestamped run logs
- ffprobe failures
- system-level errors
- final run summary

Avoid logging credentials, cookies, tokens, or other secrets.

## Git behavior

Authoritative successful mozi runs may update:

- `config/stream_health.json`
- `output/japan-live.m3u`
- `output/stream-health.md`
- related generated state required by the implementation

Before push:

1. fetch current `origin/main`
2. confirm local integration is clean
3. safely rebase/fast-forward
4. regenerate outputs if needed
5. validate playlist and state
6. push without force
7. verify remote SHA after push

If the repository has diverged unexpectedly, leave the result local and log the reason rather than forcing a push.

## GitHub backup behavior

Initial GitHub role:

- periodically perform secondary stream probes
- record/report results separately from authoritative mozi state
- compare GitHub and mozi behavior
- alert or make divergence visible

GitHub must not initially:

- increment authoritative failure counters
- remove channels
- override mozi health state

After enough comparison data exists, the project can decide whether GitHub should become a failover authority if mozi has not reported for an extended period.

A possible future failover rule is:

- if mozi has not completed a health run for 12-18 hours
- and GitHub probe behavior has been validated
- GitHub may temporarily generate a candidate health result

This is deferred from v1.

## Configuration

Thresholds should live in configuration rather than being hard-coded.

Recommended initial values:

```yaml
health_check:
  interval_hours: 6
  probe_seconds: 15
  timeout_seconds: 20
  suspect_after_failures: 2
  remove_after_failures: 6
  restore_after_successes: 2
  new_channel_successes_required: 1
  mass_failure_threshold: 0.30
```

Exact file placement can follow the repository's existing configuration conventions.

## Safety rules

The implementation must:

- never remove a channel after a single failure
- never advance failure counters during a suppressed systemic-failure run
- never force-push
- never permanently delete health history merely because a channel is dead
- never treat a simple HTTP response as proof of playable media
- never assume GitHub-runner failures equal residential playback failures
- never modify upstream playlist content
- never fabricate channel identity or map one stream to another
- never attempt access-control or DRM circumvention

## Implementation phases

### Phase 1: Inspect

- [ ] Review current upstream M3U structure.
- [ ] Count channel entries and identify URL/protocol types.
- [ ] Identify missing/duplicate `tvg-id` values.
- [ ] Confirm `ffprobe` availability/version on mozi.
- [ ] Review current repository layout and playlist parser.
- [ ] Review GitHub Pages artifact/publish workflow.
- [ ] Decide exact locations for health configuration and generated outputs.
- [ ] Benchmark a representative probe sample.
- [ ] Estimate full-playlist runtime and safe concurrency.

### Phase 2: Core health checker

- [ ] Add M3U inventory parsing suitable for health checks.
- [ ] Implement stable channel identity.
- [ ] Implement ffprobe-based audio-or-video success test.
- [ ] Implement per-channel timeout.
- [ ] Implement persistent health-state loading/saving.
- [ ] Implement new/healthy/suspect/removed/upstream_removed states.
- [ ] Implement consecutive-failure logic.
- [ ] Implement recovery logic.
- [ ] Implement new-channel admission logic.
- [ ] Implement upstream-removal logic.
- [ ] Implement mass-failure suppression.
- [ ] Implement local/systemic checker-failure detection.
- [ ] Add deterministic unit tests.

### Phase 3: Playlist generation

- [ ] Generate `output/japan-live.m3u`.
- [ ] Preserve upstream channel order.
- [ ] Preserve metadata and stream URLs exactly.
- [ ] Exclude only channels disallowed by health state.
- [ ] Validate generated M3U structure.
- [ ] Add tests for filtering and metadata preservation.
- [ ] Add a human-readable health report.

### Phase 4: EPG integration

- [ ] Separate upstream inventory discovery from active cleaned-playlist inventory.
- [ ] Keep EPG configuration for temporarily dead channels.
- [ ] Ensure active EPG generation is compatible with the cleaned playlist.
- [ ] Preserve exact `tvg-id` validation.
- [ ] Verify 48-hour production feed still builds correctly.
- [ ] Add regression tests.

### Phase 5: mozi automation

- [ ] Create systemd user service.
- [ ] Create six-hour persistent timer.
- [ ] Add small randomized start delay.
- [ ] Set explicit PATH for ffprobe/Python/git.
- [ ] Add stable local log directory.
- [ ] Prevent overlapping runs.
- [ ] Ensure failed runs do not corrupt state.
- [ ] Add safe git fetch/rebase/push behavior.
- [ ] Verify timer survives reboot.
- [ ] Verify one manual run end-to-end before unattended operation.

### Phase 6: GitHub publication

- [ ] Include `japan-live.m3u` in Pages artifact.
- [ ] Include health report if appropriate.
- [ ] Confirm stable public URL.
- [ ] Verify TiviMate can load the cleaned playlist.
- [ ] Verify Sparkle can load the cleaned playlist.
- [ ] Verify EPG mapping remains correct.

### Phase 7: GitHub backup checker

- [ ] Add non-authoritative GitHub Actions health probe.
- [ ] Store/report its results separately.
- [ ] Compare GitHub-runner outcomes with mozi.
- [ ] Identify provider blocks or systematic false negatives.
- [ ] Decide later whether failover authority is safe.

## Acceptance checklist

The project is ready for unattended use when all of the following are true:

- [ ] A valid audio-only stream passes.
- [ ] A valid video-only stream passes.
- [ ] An HTTP-success/no-media stream fails.
- [ ] One transient failure never removes a channel.
- [ ] A channel becomes suspect after 2 consecutive failures.
- [ ] A channel is removed only after 6 consecutive failures.
- [ ] A successful probe before removal resets the failure streak.
- [ ] A removed channel returns after 2 consecutive successes.
- [ ] A new upstream channel requires 1 success before publication.
- [ ] An upstream-removed channel disappears from the cleaned playlist immediately.
- [ ] Historical health state remains available after removal.
- [ ] A mass-failure run does not advance authoritative failure counters.
- [ ] A local-network/checker failure does not advance authoritative failure counters.
- [ ] Channel order is preserved.
- [ ] Channel names, groups, logos, IDs, and URLs are preserved.
- [ ] Generated M3U is valid and loadable.
- [ ] Health state survives process and host restarts.
- [ ] Runs do not overlap.
- [ ] mozi timer runs every six hours.
- [ ] Local diagnostics are sufficient to explain removals.
- [ ] GitHub pushes never use force.
- [ ] Diverged git state fails safely.
- [ ] Cleaned playlist publishes at a stable GitHub Pages URL.
- [ ] TiviMate successfully loads the cleaned playlist.
- [ ] Sparkle successfully loads the cleaned playlist.
- [ ] Existing EPG mappings continue to work.
- [ ] 48-hour EPG generation remains successful.

## Initial operating policy

Until the system has accumulated enough real-world history:

- treat mozi as the only authoritative health checker
- keep the removal threshold at 6 consecutive failures
- keep the mass-failure threshold at 30%
- manually inspect the first channels that cross the removal threshold
- compare a sample of failures against actual playback before fully trusting unattended removals
- keep GitHub backup results informational

Once the system demonstrates low false-positive rates, manual review of routine removals can be reduced or eliminated.

## Deferred improvements

Potential later additions:

- per-channel probe intervals
- provider-specific thresholds
- automatic replacement URL discovery
- degraded-stream diagnostics
- bitrate/continuity monitoring
- public HTML dashboard
- notifications when channels die or recover
- authoritative GitHub failover when mozi is offline
- historical uptime metrics
- provider-level outage detection
