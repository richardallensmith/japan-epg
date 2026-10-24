#!/usr/bin/env bash
set -euo pipefail

MAIN_REPO="${MAIN_REPO:-/home/ras/projects/japan-epg}"
WORKTREE="${WORKTREE:-/home/ras/.local/share/japan-epg-nightly}"
STATE_DIR="${STATE_DIR:-/home/ras/.local/state/japan-epg-expand}"
CODEX="${CODEX:-/home/ras/.nvm/versions/node/v22.23.3/bin/codex}"
BRANCH="${BRANCH:-nightly-expansion}"
PROMPT_FILE="${PROMPT_FILE:-$MAIN_REPO/prompts/nightly-epg-expansion.md}"

mkdir -p "$STATE_DIR" "$(dirname "$WORKTREE")"

STAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
LOG="$STATE_DIR/$STAMP.log"
FINAL="$STATE_DIR/$STAMP-final.txt"
LOCK="$STATE_DIR/run.lock"

exec > >(tee -a "$LOG") 2>&1

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "Another Japan EPG expansion run is already active; exiting."
  exit 0
fi

echo "=== Japan EPG nightly expansion ==="
echo "Started: $(date)"

if [[ ! -d "$MAIN_REPO/.git" ]]; then
  echo "ERROR: main repository not found at $MAIN_REPO"
  exit 1
fi
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: expansion prompt not found at $PROMPT_FILE"
  exit 1
fi

cd "$MAIN_REPO"
git fetch origin main

if [[ ! -d "$WORKTREE/.git" && ! -f "$WORKTREE/.git" ]]; then
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git worktree add "$WORKTREE" "$BRANCH"
  else
    git worktree add -b "$BRANCH" "$WORKTREE" origin/main
  fi
fi

cd "$WORKTREE"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: nightly worktree has uncommitted changes; refusing to overwrite them."
  git status --short
  exit 2
fi

git fetch origin main
git rebase origin/main

PROMPT="$(cat "$PROMPT_FILE")"

echo "Starting Codex expansion run..."
set +e
timeout --signal=TERM --kill-after=30s 90m   "$CODEX" exec   -C "$WORKTREE"   -m gpt-6-sol   -c 'model_reasoning_effort="medium"'   --dangerously-bypass-approvals-and-sandbox   -o "$FINAL"   "$PROMPT"
RC=$?
set -e

if [[ $RC -eq 124 || $RC -eq 137 ]]; then
  echo "ERROR: Codex exceeded the 90-minute limit."
  exit $RC
elif [[ $RC -ne 0 ]]; then
  echo "ERROR: Codex exited with status $RC."
  exit $RC
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No repository changes were produced."
  exit 0
fi

echo "Running full validation before commit..."
python -m unittest discover -v
python -m src.main   --days 2   --playlist output/japan-live.m3u   --inventory-playlist https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u

git add -A
git commit -m "Expand live-channel EPG coverage $STAMP"

git fetch origin main
git rebase origin/main

echo "Re-running validation after rebase..."
python -m unittest discover -v
python -m src.main   --days 2   --playlist output/japan-live.m3u   --inventory-playlist https://skinred78.github.io/jp-iptv-epg/jp-playlist.m3u

git push origin HEAD:main

LOCAL_SHA="$(git rev-parse HEAD)"
git fetch origin main
REMOTE_SHA="$(git rev-parse origin/main)"

if [[ "$LOCAL_SHA" != "$REMOTE_SHA" ]]; then
  echo "ERROR: remote main does not match pushed commit."
  echo "Local:  $LOCAL_SHA"
  echo "Remote: $REMOTE_SHA"
  exit 3
fi

echo "SUCCESS: validated live-channel EPG expansion pushed to main."
echo "Commit: $LOCAL_SHA"
echo "Finished: $(date)"
echo "Final Codex report: $FINAL"
echo "Full log: $LOG"
