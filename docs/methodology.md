# agentware Methodology — Rationale & Examples (Human Reference)

> **NOT agent-loaded.** This document is the human-facing companion to
> [`AGENTS.md`](../AGENTS.md). `AGENTS.md` is the single, canonical, always-loaded
> methodology that agents follow; it is written in the Deterministic Steering
> Format (DSF) so a small model can follow it without ambiguity. All the "why",
> the worked examples, the narrative, and the hedged guidance live **here** so
> they never cost tokens on an agent spawn.
>
> If a rule and this rationale ever disagree, **the rule in `AGENTS.md` wins.**

---

## Why a steering-only repo?

agentware separates the **framework** (steering) from the **memory** (knowledge):

- The repo holds only generic, shareable steering: methodology, agents, skills,
  the loop runner, the deterministic toolkit, and multi-runtime config stubs.
- The knowledge base — the operator's profile, projects, learnings, and configs —
  lives in an EXTERNAL directory chosen at onboarding.

This split means the same clone works for anyone, can be pushed publicly, and
never risks committing personal data. The knowledge dir is resolved at runtime
(env var → `~/.agentware/config.env`), and the config file is gitignored.

### One canonical source of truth for behaviour

Behavioural rules live in `AGENTS.md` once, in DSF:

- Claude Code auto-loads `CLAUDE.md`, which imports `@AGENTS.md` and the
  `steering/` files. So the canonical methodology is always in context, loaded
  from one place, on every session (interactive and headless `claude -p`).
- The subagents in `.claude/agents/` carry **only** role identity, the first-run
  gate, path-discovery, and iteration mechanics in their system prompt — then
  defer to `AGENTS.md` for everything else.
- Operator-specific context is injected each session by the `SessionStart` hook
  (`scripts/hooks/session-start.sh`), which emits the external `MAIN.md` as
  `additionalContext`. This keeps personalized context always-on without
  committing it to the repo.

### Claude Code loader facts that drove the design

1. `CLAUDE.md` at the repo root is auto-loaded as project memory on every session.
2. Claude Code does **not** auto-load `AGENTS.md`; `CLAUDE.md` pulls it in with the
   `@AGENTS.md` import (imports inline the target file at load, up to ~5 hops).
   Keeping `AGENTS.md` as the canonical file preserves multi-runtime portability —
   the bridge stubs (`.cursorrules`, etc.) point other tools at it directly.
3. `@`-import lines are bare paths, not markdown bullets, so the DSF linter does
   not treat them as rules.
4. Headless `claude -p` still loads `CLAUDE.md` and fires `.claude/settings.json`
   hooks, so the loop's per-iteration spawns get the same always-on context and
   the same `SessionStart` injection as an interactive session.

This is why `CLAUDE.md` imports `@AGENTS.md` rather than duplicating it, and why
the `SessionStart` hook (not a per-agent field) injects the external `MAIN.md`.

---

## The execution loop — the "why"

`PLAN → EXECUTE → VERIFY → NEXT → REPEAT → COMPLETE`, stated once in `AGENTS.md`:

- **PLAN** — Persisting a plan of verifiable subtasks is what lets work survive
  across the context-reset boundary between iterations. The plan is the carry-over.
- **EXECUTE** — The deliverable is working code/config/infra, not documentation.
- **VERIFY** — Use the project's *own* build/test/health commands. agentware is
  cloud- and language-agnostic; whatever the project ships is the source of truth.
- **NEXT / REPEAT** — One logically-complete task per iteration; size is irrelevant.
- **COMPLETE** — A task is done only when every acceptance criterion is verified.

### Why "never mark complete unless it IS complete"

The most common autonomous-agent failure is declaring victory on partial work.
The rule is strict because a false "complete" compounds: the next iteration
trusts the marker and builds on a broken foundation.

---

## Anti-patterns — worked rationale

### Over-documentation
The knowledge base is **memory**, not the deliverable. Document **after** the
work is verified, not before. Creating entries for things that don't exist yet or
updating `MAIN.md`/`index.json` as a first step is looking productive while
producing nothing.

### Over-engineering
A simple script usually beats an orchestration layer. Get one thing working
end-to-end before adding infrastructure. If the user already picked an option,
implement it — don't re-litigate with three new options.

### Terminal misuse
Multi-line content via `cat`/heredoc/`echo` is fragile. Use the `write` tool for files.

### Git discipline
The user owns git. Agents don't run `git commit`/`push`/`status`/`diff` unless
asked. The single exception is the one-time `git init` + first commit during onboarding.

---

## Determinism & the toolkit

Structured data (the knowledge `index.json`, `FEATURES.md`, learning files) is
mutated **only** through `scripts/agentware`. The LLM decides *what* to record;
the toolkit guarantees *how* — valid JSON, bidirectionally-consistent tag map, no
duplicate ids/paths, sorted order, all paths relative to the knowledge dir. If
the LLM and the toolkit ever disagree about structured data, the toolkit wins.

### Why the steering DSF linter

`scripts/agentware steering lint` enforces that every always-loaded steering
rule (a markdown bullet) opens with an allowed directive verb
(MUST/NEVER/ALWAYS/RUN/ASK/STOP/READ/IF), carries a stable rule ID like
`R-KB-01`, and contains no hedge words (should/try/consider/...). The combined
size of always-loaded steering must stay within a 15,000-character budget. This
keeps the always-on layer unambiguous and cheap. The loop runs the linter as a
pre- and post-hook so steering can never silently drift out of format.

---

## Verification gates — the "why"

- **UI / web-app changes**: a green unit test does not prove the rendered UI is
  correct. The Playwright gate (shallow / with-api / deep) catches the gap
  between "compiles" and "works in a browser". with-api asserts the request
  payload, response status, and body.
- **Backend / API changes**: hit the real endpoint against the local service.
  Read-after-write for mutations proves the change actually landed.

These are non-negotiable because they are the cheapest place to catch the most
expensive failures.

---

## Self-improvement (the learning loop) — rationale

Discoveries are marked inline in the worklog as `> LEARNED: <one-liner>` so they
are never lost mid-task. At task end they are classified:

- **Project-specific fact / one-off fix** → a learning file (automatic).
- **Reusable procedure (≥2 steps)** → a skill candidate (ask before promoting).
- **Always-true rule** → a steering edit (always ask; a bad rule loads on every spawn).

`scripts/agentware worklog scan` enforces this mechanically: an unpromoted
`LEARNED:` marker fails the loop's post-hook, guaranteeing zero knowledge loss.

---

## Conventions

- Naming: `{project}-{resource}-v{version}` (e.g. `fooapp-postgres-v1`), or adopt
  the project's existing scheme.
- Relative paths inside repo files; resolve the external knowledge dir at runtime.
- Record what was built in the knowledge base for the next session.

---

## See also

- [`AGENTS.md`](../AGENTS.md) — the canonical, always-loaded methodology (DSF).
- [`docs/loop.md`](loop.md) — the 3-phase loop and plan format.
- The external knowledge dir's `index.json` — query it with `scripts/agentware query`.
