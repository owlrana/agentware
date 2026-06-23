#!/bin/bash
# Stop hook — at the end of every assistant turn, persist a COMPLETE record of
# what happened into the EXTERNAL knowledge base:
#   logs/sessions/<session_id>.jsonl  — lossless raw transcript copy
#   logs/sessions/<session_id>.md     — readable, timestamped render
#   logs/activity.log                 — one append-only line per turn
# Falls back to a repo-local log dir only pre-onboarding. No stdout.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

KDIR="$("$REPO_ROOT/scripts/aw-knowledge-dir" 2>/dev/null || true)"
if [[ -n "$KDIR" ]]; then LOG_DIR="$KDIR/logs"; else LOG_DIR="$REPO_ROOT/.agentware-logs"; fi
mkdir -p "$LOG_DIR/sessions"

input="$(cat)"
sid="unknown"; tpath=""
if command -v jq >/dev/null 2>&1; then
  sid="$(printf '%s' "$input" | jq -r '.session_id // "unknown"' 2>/dev/null)"
  tpath="$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null)"
fi

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ -n "$tpath" && -f "$tpath" ]]; then
  # Lossless copy (transcript is append-only, so the latest copy is complete).
  cp -f "$tpath" "$LOG_DIR/sessions/$sid.jsonl" 2>/dev/null || true
  # Readable render (best-effort; the .jsonl is the source of truth).
  if command -v python3 >/dev/null 2>&1; then
    python3 "$SCRIPT_DIR/render-transcript.py" "$tpath" \
      > "$LOG_DIR/sessions/$sid.md" 2>/dev/null || true
  fi
  printf '[%s] [stop] session %s -> sessions/%s.{jsonl,md}\n' "$ts" "$sid" "$sid" \
    >> "$LOG_DIR/activity.log"
else
  printf '[%s] [stop] session %s (no transcript path)\n' "$ts" "$sid" \
    >> "$LOG_DIR/activity.log"
fi
exit 0
