# <Skill Title>

> **When to invoke**: <a specific, concrete trigger condition. "When X happens"
> is good. "Sometimes" is bad.>

## Why this skill exists

<Why is this a skill and not a learning? Why does the agent need a written
procedure rather than reasoning from first principles each time?>

## Prerequisites

- <What must be true before running this skill>

## Procedure

### Step 1 — <name>

<Numbered steps with concrete commands and expected output. Specific enough that
a different agent could follow it without re-deriving anything.>

### Step 2 — <name>

...

## Failure handling

<What does the agent do when the procedure fails partway? Mark incomplete? Roll
back? Surface specific evidence to the user?>

## Gotchas

- <Failure mode 1 and how to handle it>

## See also

- <Related skill: `.claude/skills/<other-skill>/SKILL.md`>
- <Related learning in the external knowledge dir: `learnings/<topic>.md`>

---

## Authoring notes (delete this section before finalizing)

A skill earns its place when the procedure has ≥2 steps AND applies across
multiple tasks (not a one-off fix). If your draft fails either, it should be a
learning instead — see `.claude/skills/self-improvement/SKILL.md`.

After writing, wire the skill in:
- Trigger applies on every task of a kind → one-liner in `AGENTS.md`.
- Trigger applies in one situation → add to a related skill's "See also".

Skills live in the repo (generic procedure) and are NOT registered in the
per-operator knowledge index.
