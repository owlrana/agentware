# @agentware-plan

Create a new feature plan for the loop to execute in this agentware workspace.

## Instructions

1. Read `docs/loop.md` to understand how to create plan and design documents.
2. Read `AGENTS.md` for the project's execution methodology.
3. Read the knowledge base MAIN.md (resolve its dir via
   `scripts/agentware config --knowledge-dir-only`) for current active work.
4. Ask the user for the feature requirements (3–5 targeted questions max).
5. Determine which task types are involved:
   - **infra** — environment / resource provisioning using the project's own
     tooling (no assumed cloud verbs).
   - **code** — code changes in this workspace or a sibling workspace.
   - **config** — configuration changes deployed to running services.
   - **knowledge** — knowledge-base updates (entries, `index.json`, `MAIN.md`).
6. Create a docs directory: `<knowledge-dir>/work/<YYMMDD-feature-name>/`.
7. Write `plan.md` with phases, tasks, and acceptance criteria following the
   format in `docs/loop.md`.
8. Optionally create `design.md` for complex features.
9. Tell the user which folder you created the files in.
10. Suggest the user run `./agentware.sh <feature-name>` to execute the plan, or
    re-run the planner to iterate.

## Task scoping guidelines

- Each task should be **one logical unit** of work.
- Infrastructure tasks: one resource per task.
- Knowledge-base tasks: group related updates (e.g. "Create project entry +
  update `index.json`").
- Cross-workspace code tasks: one coherent change per task.
- Every task MUST have verifiable acceptance criteria expressed in the project's
  own commands.

## Conventions for plan content

- Naming: `{project}-{resource}-v{version}` unless the project documents its own.
- Relative paths inside repo files; resolve the external knowledge dir at runtime.
- Verification: each task lists a concrete check (file exists, test passes,
  command output, etc.).
- Always include a knowledge-base-update task in the final phase.
- Set the promise tag at the top of the plan:
  `<promise>YYMMDD_FEATURE_NAME_COMPLETE</promise>`.
