# TriWorld — Hermes documentation router

This file tells Hermes where to find information. It is not a greenfield
bootstrap prompt and does not reset the current implementation phase.

## Continue an existing session

Always begin with:

1. `docs/CURRENT_HANDOFF.md`
2. `docs/hints/HERMES_VERIFICATION_RULES.md`
3. current Git HEAD and working-tree status

Continue only from the milestone recorded in the handoff. If the handoff is
stale or conflicts with Git/runtime evidence, report the conflict before making
changes.

## Read documentation progressively

Load only what the current task needs:

- Architecture and long-term product definition:
  `HERMES_TRIWORLD_MASTER_PROMPT_2026.md`
- Practical implementation traps:
  `docs/hints/HERMES_EXECUTION_HINTS.md`
- Research process and primary sources:
  `docs/resources/README.md`
- Operations, gates, and risks:
  `docs/operations/`
- Contracts and ADRs:
  `packages/contracts/` and `docs/adr/`
- Current implementation inventory:
  `docs/implementation-status.md`

The master prompt contains historical greenfield and Phase 0/1 instructions.
Those sections apply only when explicitly requested for a new repository. They
must not be interpreted as the next action in this existing repository.

## Before editing

```powershell
Set-Location -LiteralPath 'C:\TriWorld'
git status --short --branch
git rev-parse HEAD
```

Preserve dirty and untracked user files. Do not expose secret values, clear
BeamNG caches, overwrite installed mods, terminate BeamNG, or manually patch a
generated ZIP unless the user explicitly authorizes that exact action.

## Evidence discipline

Separate these states:

- implemented
- unit tested
- statically validated
- stock compared
- integration tested
- runtime verified
- visually inspected
- not yet proven

Passing unit/static tests does not prove BeamNG compatibility. A changed ZIP
must have a changed SHA-256 and must be treated as a new artifact.

## Updating the continuation checkpoint

Before handing work to another session, update `docs/CURRENT_HANDOFF.md` with:

- exact HEAD and branch;
- dirty/untracked files;
- immutable artifact paths and SHA-256;
- commands actually executed;
- proven and unproven results;
- current blocker;
- files that must not be modified;
- one next falsifiable action.

Do not place a one-time task prompt in `.hermes.md` or this file.
