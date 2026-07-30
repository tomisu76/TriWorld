# TriWorld documentation router

This router is valid for the complete project lifecycle. It explains where
information belongs; it never defines the current phase.

## Start or resume work

Always begin with:

1. `docs/CURRENT_HANDOFF.md`
2. `docs/hints/HERMES_VERIFICATION_RULES.md`
3. current Git HEAD, status, and relevant diff

The handoff is a checkpoint, not unquestionable truth. Reconcile it with Git,
immutable artifact hashes, test output, installed files, and runtime logs before
making consequential changes.

## Authority and document roles

| Need | Authoritative location |
|---|---|
| Current task, blocker, artifact and next action | `docs/CURRENT_HANDOFF.md` |
| Implemented capabilities and verification depth | `docs/implementation-status.md` |
| Evidence vocabulary and truth rules | `docs/hints/HERMES_VERIFICATION_RULES.md` |
| Product goal and long-term architecture | `HERMES_TRIWORLD_MASTER_PROMPT_2026.md` |
| Practical implementation traps | `docs/hints/HERMES_EXECUTION_HINTS.md` |
| ADRs and architectural decisions | `docs/adr/` |
| Operations, gates, risks and test matrix | `docs/operations/` |
| Reusable research playbooks and templates | `docs/resources/` |
| Project-specific research evidence | `docs/research/` |
| Runtime/build evidence | `artifacts/evidence/` and the paths named in the handoff |
| Historical Phase 1 plan | `PHASE1_PLAN.md` |

The master prompt includes original greenfield material. Read only sections
relevant to the current task. Historical plans never override the handoff.

## Task routing

- Research or uncertain external formats: begin with
  `docs/resources/RESEARCH_PLAYBOOK.md` and primary sources.
- BeamNG packaging/runtime: use
  `docs/resources/BEAMNG_RUNTIME_CHECKLIST.md`.
- GIS/DEM/OSM/SUMO work: use the relevant contracts, ADRs, and
  `docs/resources/SUMO_GIS_QA_CHECKLIST.md`.
- Architecture changes: inspect existing ADRs and add or supersede an ADR.
- Release work: inspect operations, risk register, version lock, provenance,
  licenses, reproducibility, and runtime evidence.

Web research, subagents, NotebookLM, Blender, SUMO, and other tools are selected
only when useful to the current task. Their mention in a playbook is not a command
to invoke all of them in every session.

## Before editing

```powershell
Set-Location -LiteralPath 'C:\TriWorld'
git status --short --branch
git rev-parse HEAD
git diff --stat
```

Preserve dirty and untracked user work. Inspect overlapping modifications before
editing. Do not regenerate, install, launch, terminate, clear, commit, or push
merely because an older report describes that action.

## Evidence discipline

Use only the states defined by the verification rules, including:

- implemented;
- unit tested;
- statically validated;
- integration tested;
- runtime verified;
- visually inspected;
- not yet proven.

Always attach scope: exact artifact, SHA-256, target version, environment, command,
and date where relevant. Static PASS is never converted into runtime PASS.

## Maintaining continuity

`docs/CURRENT_HANDOFF.md` must remain short and current. Replace superseded facts
instead of retaining a diary. It must contain:

- goal and current phase/gate;
- exact Git and working-tree state;
- last runtime-proven baseline;
- newest implemented/static candidate, if different;
- commands and results actually observed;
- immutable artifact identities;
- current blocker and unproven claims;
- files or evidence that must be preserved;
- exactly one recommended next falsifiable action.

`docs/implementation-status.md` is not a session log. Update its capability matrix
and verification levels when evidence changes.

When the product is complete, the handoff becomes a release/maintenance
checkpoint rather than restarting the implementation plan.
