#!/usr/bin/env bash
set -euo pipefail

MAIN_REPO="${MAIN_REPO:-/home/ras/projects/japan-epg}"
WORKTREE="${WORKTREE:-/home/ras/.local/share/japan-epg-health}"
BRANCH="${BRANCH:-health-automation}"
STATE_DIR="${STATE_DIR:-/home/ras/.local/state/japan-epg-health}"

mkdir -p "$STATE_DIR"
mkdir -p "$(dirname "$WORKTREE")"

STAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
LOG="$STATE_DIR/$STAMP.log"
LOCK="$STATE_DIR/run.lock"

exec > >(tee -a "$LOG") 2>&1

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "Another Japan EPG health check is already running; exiting."
  exit 0
fi

echo "=== Japan EPG stream health run ==="
echo "Started: $(date)"
echo "Main repo: $MAIN_REPO"
echo "Worktree: $WORKTREE"

if [[ ! -d "$MAIN_REPO/.git" ]]; then
  echo "ERROR: repository not found at $MAIN_REPO"
  exit 1
fi

cd "$MAIN_REPO"
git fetch origin main

if [[ ! -d "$WORKTREE/.git" && ! -f "$WORKTREE/.git" ]]; then
  echo "Creating health automation worktree..."
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git worktree add "$WORKTREE" "$BRANCH"
  else
    git worktree add -b "$BRANCH" "$WORKTREE" origin/main
  fi
fi

cd "$WORKTREE"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: health worktree has uncommitted changes; refusing to overwrite them."
  git status --short
  exit 2
fi

git fetch origin main
git rebase origin/main

echo "Running authoritative stream health check..."
python3 -m src.stream_health

echo "Running stream-health unit tests..."
python3 -m unittest discover -s tests -p 'test_stream_health.py' -v

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No health-state changes to publish."
  exit 0
fi

echo "Changed files:"
git status --short

# Only the authoritative health-state outputs should be changed by this job.
unexpected="$(git status --porcelain | awk '{print $2}' | grep -Ev '^(config/stream_health.json|output/japan-live.m3u|output/stream-health.md)$' || true)"
if [[ -n "$unexpected" ]]; then
  echo "ERROR: unexpected files changed:"
  echo "$unexpected"
  exit 3
fi

git add config/stream_health.json output/japan-live.m3u output/stream-health.md
git commit -m "Update IPTV stream health $STAMP"

echo "Refreshing origin/main before publish..."
git fetch origin main
git rebase origin/main

# A rebase can change context; ensure the health outputs and tests still validate.
python3 -m unittest discover -s tests -p 'test_stream_health.py' -v

echo "Pushing validated health state to main..."
git push origin HEAD:main

LOCAL_SHA="$(git rev-parse HEAD)"
git fetch origin main
REMOTE_SHA="$(git rev-parse origin/main)"

if [[ "$LOCAL_SHA" != "$REMOTE_SHA" ]]; then
  echo "ERROR: remote main does not match pushed health commit."
  echo "Local:  $LOCAL_SHA"
  echo "Remote: $REMOTE_SHA"
  exit 4
fi

echo "SUCCESS: health state published."
echo "Commit: $LOCAL_SHA"
echo "Finished: $(date)"
echo "Log: $LOG"
