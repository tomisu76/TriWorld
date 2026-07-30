# TriWorld Current Handoff

**Purpose:** authoritative continuation checkpoint for every new Hermes session.

**Updated:** 2026-07-30

**Repository:** `C:\TriWorld`

**Branch:** `audit-and-evidence`

**Implementation baseline:** `52a5dfbc11594677058083ed79bd0991985d8890`
**Instruction checkpoint:** the current Git HEAD containing this file; verify
with `git rev-parse HEAD`.

## Scope of the instruction-flow checkpoint

The instruction-flow repair changes only:

- `.hermes.md`
- `HERMES_START_HERE.md`
- `HERMES_TRIWORLD_MASTER_PROMPT_2026.md`
- `PHASE1_PLAN.md`
- `README.md`
- `docs/implementation-status.md`
- `docs/CURRENT_HANDOFF.md`

No generator, serializer, validator, test, ZIP, BeamNG profile, or installed mod
was changed as part of the instruction-flow repair.

## Current milestone

Phase 2 synthetic BeamNG canary recovery.

Implementation and static validation exist, but the BeamNG runtime gate has
failed. The phase status is:

`IMPLEMENTATION IN PROGRESS — STATIC CHECKS INSUFFICIENT — RUNTIME FAILURE`

Do not start Phase 3 and do not repeat the original greenfield/Phase 0/Phase 1
bootstrap.

## Proven state

- Commit `52a5dfb` contains the Phase 2 recovery implementation and tests.
- The committed test suite reported 96 passing tests at commit time.
- Static validation reported 20 checks passing, but it did not detect the
  runtime-invalid scene graph. Static PASS is therefore not sufficient evidence
  of BeamNG compatibility.
- BeamNG version used for the current runtime investigation:
  `0.38.6.0.19963`.
- Current BeamNG logs contain:
  `Expanded mission file is invalid: "" from "levels/test_level"`.
- The error occurs in both the active `beamng.log` and rotated `beamng.1.log`.
- `levels/test_level/info.json` exists in the installed ZIP. Do not diagnose the
  failure as a missing `info.json` without new contrary evidence.

## Artifact identity

Several post-commit experimental ZIPs were created manually. They are evidence,
not approved generator output:

- `artifacts/canary_phase2_runtime_gate.zip`
- `artifacts/canary_phase2_fixed.zip`
- `artifacts/canary_phase2_fixed2.zip`

At the last read-only inspection, the installed
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\test_level.zip` matched
`canary_phase2_fixed2.zip`:

`A21B2A70E786D73B4F5A2519721811D5AF1A45CC50C4390BB6F78E4C833A0CDA`

Never claim that two ZIPs have the same SHA-256 after their contents changed.
Re-hash artifacts before relying on this checkpoint because ignored artifacts
can change without changing Git.

## Current root-cause investigation

The likely failure area is BeamNG 0.38.6 split scene LDJSON serialization:

- root `main/items.level.json`;
- `MissionGroup` hierarchy;
- `__parent` relationships;
- use of `SimGroupEnd` in split scene files;
- required identity fields such as `persistentId`/`enabled`;
- separation of stock convention from an actual runtime requirement.

Differences from Italy are hypotheses, not automatically defects. Compare with
the exact installed stock version and preferably a small engine-saved golden
level. Identify the smallest structural defect capable of producing the exact
runtime error.

## Do not do

- Do not create `fixed3`, `fixed4`, or other manually patched ZIP variants.
- Do not modify the generator until the read-only root-cause report is
  internally consistent.
- Do not edit Hermes skills as part of TriWorld runtime recovery.
- Do not launch/terminate BeamNG, replace installed mods, clear caches, commit,
  or push without explicit authorization for that action.
- Do not repeat completed static audits or claim runtime success from validator
  results.
- Do not use a direct NVIDIA/Nemotron session for long audits; use
  `route-default` so LiteLLM fallback remains available.

## Next falsifiable action

Complete one focused read-only comparison of the exact installed failing ZIP,
the two current BeamNG logs, stock BeamNG 0.38.6 split scene files, and a small
engine-saved level. Produce:

1. proven runtime requirements;
2. stock conventions only;
3. likely defects;
4. unproven hypotheses;
5. the smallest proposed generator change;
6. validator regression checks that would reject the observed malformed scene.

Stop before implementation and request approval.

## Handoff maintenance rule

The agent that completes or changes this milestone must update this file in the
same focused commit. Replace stale facts; do not append repetitive progress
transcripts.
