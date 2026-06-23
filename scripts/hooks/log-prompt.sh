#!/bin/bash
# UserPromptSubmit hook — durably record EVERY user prompt so nothing is ever
# lost. Appends to the EXTERNAL knowledge base (logs/prompts.log) when one is
# configured, else falls back to a repo-local log (pre-onboarding only). Writes
# nothing to stdout, so no extra context is injected.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

KDIR="$("$REPO_ROOT/scripts/aw-knowledge-dir" 2>/dev/null || true)"
if [[ -n "$KDIR" ]]; then LOG_DIR="$KDIR/logs"; else LOG_DIR="$REPO_ROOT/.agentware-logs"; fi
mkdir -p "$LOG_DIR"

input="$(cat)"
sid=""; prompt=""; cwd=""
if command -v jq >/dev/null 2>&1; then
  sid="$(printf '%s' "$input" | jq -r '.session_id // "unknown"' 2>/dev/null)"
  prompt="$(printf '%s' "$input" | jq -r '.prompt // empty' 2>/dev/null)"
  cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)"
fi

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  printf '[%s] [session %s] [cwd %s]\n' "$ts" "$sid" "$cwd"
  printf '%s\n\n' "$prompt"
} >> "$LOG_DIR/prompts.log"
exit 0
