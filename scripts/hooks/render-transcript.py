#!/usr/bin/env python3
"""Render a Claude Code transcript JSONL into a readable, timestamped markdown log.

Usage: render-transcript.py <transcript.jsonl>   # writes markdown to stdout

Captures the full audit trail — every user prompt and everything the assistant
did (its text, its reasoning, the tools it called, and the tool results) — with
ISO timestamps, so the operator can always go back and see exactly what happened
in a session. The raw JSONL is copied alongside this file as the lossless record;
this renderer is the human-readable view.
"""

import json
import sys


def _ts(entry):
    return entry.get("timestamp") or ""


def _short(text, n=4000):
    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    text = text.strip()
    return text if len(text) <= n else text[:n] + " …[truncated]"


def _render_content(content, out):
    """Append rendered lines for a message's content (str or block list)."""
    if isinstance(content, str):
        if content.strip():
            out.append(_short(content))
        return
    if not isinstance(content, list):
        return
    for b in content:
        if not isinstance(b, dict):
            continue
        bt = b.get("type")
        if bt == "text":
            out.append(_short(b.get("text", "")))
        elif bt == "thinking":
            out.append("> 🧠 _thinking_: " + _short(b.get("thinking", ""), 2000))
        elif bt == "tool_use":
            inp = b.get("input") or {}
            out.append("> 🔧 **tool:** `%s`  \n> ```json\n> %s\n> ```"
                       % (b.get("name", "?"),
                          _short(json.dumps(inp, ensure_ascii=False), 1500)))
        elif bt == "tool_result":
            c = b.get("content")
            if isinstance(c, list):
                c = " ".join(x.get("text", "") for x in c
                             if isinstance(x, dict) and x.get("type") == "text")
            out.append("> 📤 _tool result_: " + _short(c or "", 1500))


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: render-transcript.py <transcript.jsonl>\n")
        return 2
    path = argv[1]
    lines = ["# Session transcript", ""]
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                etype = entry.get("type")
                if etype not in ("user", "assistant"):
                    continue
                msg = entry.get("message") or {}
                role = msg.get("role") or etype
                body = []
                _render_content(msg.get("content"), body)
                body = [b for b in body if b and b.strip()]
                if not body:
                    continue
                label = "🧑 USER" if role == "user" else "🤖 ASSISTANT"
                lines.append("## [%s] %s" % (_ts(entry), label))
                lines.append("")
                lines.extend(body)
                lines.append("")
    except OSError as exc:
        sys.stderr.write("render-transcript: %s\n" % exc)
        return 1
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
