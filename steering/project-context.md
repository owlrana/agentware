# Project Context

> Generic placeholder — ships in the clone and contains NO operator data. The
> real operator profile, environment, and active projects live in the EXTERNAL
> knowledge base and are injected on every agent spawn by the bootstrap hook
> (it prints the knowledge MAIN.md). No behavioural rules here — those live in
> `AGENTS.md`.

This is an agentware workspace: a clone-and-go AI context + task-execution
framework. The repo holds only generic steering; the operator's knowledge base
lives in an external directory chosen at onboarding.

## Where to look

| Need | Location |
|------|----------|
| Resolve the knowledge dir | `scripts/agentware config --knowledge-dir-only` |
| Active work | the knowledge dir's `MAIN.md` |
| Per-project context | the knowledge dir's `projects/` |
| Accumulated gotchas | the knowledge dir's `learnings/` |
| Feature plans / worklogs | `<knowledge-dir>/work/` (external) |
| Session logs (prompts + transcripts) | `<knowledge-dir>/logs/` (external) |
| Canonical methodology | `AGENTS.md` (in this package) |

> agentware owns its own codebase: any change to it is just another agentware
> task — write `<knowledge-dir>/work/<YYMMDD-feature>/plan.md` and run `./agentware.sh <feature>`.
