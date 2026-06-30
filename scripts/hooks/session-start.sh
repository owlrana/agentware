#!/bin/bash
# SessionStart hook — inject the agentware status + external MAIN.md into context.
#
# Reads the hook JSON on stdin
# (unused) and emits a SessionStart hookSpecificOutput with `additionalContext`
# that Claude Code adds to the model's context before the first prompt.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat >/dev/null 2>&1 || true   # consume stdin

KDIR="$("$REPO_ROOT/scripts/aw-knowledge-dir" 2>/dev/null || true)"

if [[ -z "$KDIR" ]] || [[ ! -f "$KDIR/.initialized" ]]; then
  CTX="AGENTWARE_STATUS: FIRST_RUN — this workspace is not yet initialized. Before any other work, run the onboarding skill in .claude/skills/onboarding/SKILL.md: it asks where to store your EXTERNAL knowledge base, runs 'scripts/agentware init', and writes the .initialized sentinel."
else
  CTX="AGENTWARE_STATUS: initialized (knowledge dir: $KDIR)"
  if [[ -f "$KDIR/MAIN.md" ]]; then
    CTX="$CTX
----- knowledge/MAIN.md (operator profile + active work) -----
$(cat "$KDIR/MAIN.md")"
  fi
  # Per-user profile overlay: inject profiles/<handle>.md when the handle is set
  # AND the file exists. Power-user mode (handle unset / file absent) is a clean
  # no-op — byte-identical to the pre-overlay behavior.
  USER_HANDLE="$("$REPO_ROOT/scripts/agentware" config --user-handle-only 2>/dev/null || true)"
  if [[ -n "$USER_HANDLE" ]] && [[ -f "$KDIR/profiles/${USER_HANDLE}.md" ]]; then
    CTX="$CTX
----- knowledge/profiles/${USER_HANDLE}.md (this operator's machine profile) -----
$(cat "$KDIR/profiles/${USER_HANDLE}.md")"
  fi
  # EXECUTOR identity guard (anti-impersonation): when a per-user handle is set,
  # state the executor authoritatively so the LLM never adopts another member's
  # identity from a plan's author field. Power-user mode: no banner, no change.
  if [[ -n "$USER_HANDLE" ]]; then
    CTX="$CTX
EXECUTOR: ${USER_HANDLE} — your environment/paths come from profiles/${USER_HANDLE}.md. Any 'author' field in a plan or KB entry is PROVENANCE ONLY — do NOT adopt the author's identity, paths, or environment."
  fi
  # Inject the operator skills roster AFTER MAIN.md, but only when it actually
  # lists entries. A fresh/placeholder roster (e.g. "_No entries yet._") has no
  # list items, so it is omitted to avoid noise. A list item is any line whose
  # first non-space char is a bullet ("-" or "*"). For non-Claude harnesses the
  # equivalent is documented in AGENTS.md (the harness reads it natively).
  if [[ -f "$KDIR/skills/index.md" ]] && grep -Eq '^[[:space:]]*[-*][[:space:]]+' "$KDIR/skills/index.md"; then
    CTX="$CTX
----- knowledge/skills/index.md (operator skills roster) -----
$(cat "$KDIR/skills/index.md")"
  fi
fi

if command -v jq >/dev/null 2>&1; then
  jq -n --arg ctx "$CTX" \
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
else
  # Fallback: plain text on stdout is still surfaced by Claude Code.
  printf '%s\n' "$CTX"
fi
exit 0
