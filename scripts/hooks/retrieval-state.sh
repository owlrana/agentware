#!/bin/bash
# retrieval-state.sh — PreToolUse hook enforcing the R-RET staged retrieval ladder.
#
# Tracks per-session retrieval state and warns on out-of-order tool calls.
# Ships WARN-ONLY (never blocks); honors AGENTWARE_DISABLE_RETRIEVAL_LINT.
#
# State machine: UNSTARTED -> RECALL_S1 -> RECALL_S2 -> QUERY -> WORK ->
#                GREP_WS -> CODE -> MCP -> WEB
#
# Detection: recall/query/grep are NOT distinct tools — recall/query are
# `scripts/agentware <sub>` invoked via Bash, workspace-grep is Bash grep/rg.
# The hook keys on tool_name + regex over tool_input.command.

set -e

# Kill-switch: disable entirely
if [[ -n "${AGENTWARE_DISABLE_RETRIEVAL_LINT:-}" ]]; then
  exit 0
fi

# Mode: warn (default) or block
MODE="${AGENTWARE_RETRIEVAL_LINT_MODE:-warn}"

# Graceful no-op when toolkit unavailable
if [[ ! -x scripts/agentware ]]; then
  exit 0
fi

# State file (per-session, under logs/ if available)
KDIR="$(scripts/agentware config --knowledge-dir-only 2>/dev/null || true)"
if [[ -z "$KDIR" ]]; then
  exit 0
fi
STATE_DIR="$KDIR/logs/.retrieval-state"
mkdir -p "$STATE_DIR" 2>/dev/null || true
STATE_FILE="$STATE_DIR/current.state"

# Read current state
CURRENT_STATE="UNSTARTED"
if [[ -f "$STATE_FILE" ]]; then
  CURRENT_STATE=$(cat "$STATE_FILE" 2>/dev/null || echo "UNSTARTED")
fi

# Parse tool event from hook input (stdin is JSON with tool_name, tool_input)
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# Classify the tool event into a retrieval stage
classify_event() {
  local name="$1"
  local input="$2"

  # Bash tool with agentware recall -> RECALL_S1 or RECALL_S2
  if [[ "$name" == "Bash" ]] && echo "$input" | grep -q "agentware recall"; then
    if echo "$input" | grep -q "\-\-top-k 10\|\-\-token-budget 3000"; then
      echo "RECALL_S2"
    else
      echo "RECALL_S1"
    fi
    return
  fi

  # Bash tool with agentware query -> QUERY
  if [[ "$name" == "Bash" ]] && echo "$input" | grep -q "agentware query"; then
    echo "QUERY"
    return
  fi

  # Bash tool with agentware recall --scope work -> WORK
  if [[ "$name" == "Bash" ]] && echo "$input" | grep -q "scope work"; then
    echo "WORK"
    return
  fi

  # Grep tool or Bash grep/rg over workspace -> GREP_WS
  if [[ "$name" == "Grep" ]]; then
    echo "GREP_WS"
    return
  fi
  if [[ "$name" == "Bash" ]] && echo "$input" | grep -qE "grep|rg |ripgrep"; then
    if echo "$input" | grep -qE "workspace|src/|/repos?/"; then
      echo "GREP_WS"
      return
    fi
  fi

  # Read tool -> CODE
  if [[ "$name" == "Read" ]]; then
    echo "CODE"
    return
  fi

  # WebFetch/WebSearch -> WEB
  if [[ "$name" == "WebFetch" ]] || [[ "$name" == "WebSearch" ]]; then
    echo "WEB"
    return
  fi

  # MCP tools -> MCP
  if echo "$name" | grep -q "^mcp__"; then
    echo "MCP"
    return
  fi

  echo "OTHER"
}

EVENT=$(classify_event "$TOOL_NAME" "$TOOL_INPUT")

# Skip non-retrieval events
if [[ "$EVENT" == "OTHER" ]]; then
  exit 0
fi

# State transition check
# Hard violations: GREP_WS or WEB while UNSTARTED (grep/web before ANY recall)
check_violation() {
  local state="$1"
  local event="$2"

  if [[ "$state" == "UNSTARTED" ]]; then
    case "$event" in
      GREP_WS|WEB)
        echo "WARN: $event before any recall (state=$state). Run recall first per R-RET-03."
        return 1
        ;;
    esac
  fi
  return 0
}

VIOLATION_MSG=$(check_violation "$CURRENT_STATE" "$EVENT" 2>&1) || true

if [[ -n "$VIOLATION_MSG" ]]; then
  if [[ "$MODE" == "warn" ]]; then
    echo "$VIOLATION_MSG" >&2
    # In warn mode, NEVER block — just warn
  fi
  # In block mode (future): would exit 1 here
fi

# Update state (advance to the new stage)
case "$EVENT" in
  RECALL_S1|RECALL_S2|QUERY|WORK|GREP_WS|CODE|MCP|WEB)
    echo "$EVENT" > "$STATE_FILE"
    ;;
esac

exit 0
