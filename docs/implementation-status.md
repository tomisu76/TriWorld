# TriWorld Implementation Status

This document is a component inventory. The session continuation authority is
`docs/CURRENT_HANDOFF.md`.

**Repository:** `C:\TriWorld`

**Branch:** `audit-and-evidence`

**Last verified HEAD:** `52a5dfbc11594677058083ed79bd0991985d8890`
**Runtime target:** BeamNG.drive `0.38.6.0.19963`

## Current phase

Phase 2 synthetic BeamNG canary recovery:

`IMPLEMENTATION IN PROGRESS — RUNTIME FAILURE`

The generator, serializers, static validator, and tests are implemented.
Static checks passed at the committed checkpoint, but BeamNG rejected the level
with:

`Expanded mission file is invalid: "" from "levels/test_level"`

Therefore the canary is not runtime verified and the validator has a coverage
gap around BeamNG split scene LDJSON structure.

## Implemented at HEAD 52a5dfb

- Pydantic contracts and deterministic infrastructure.
- SQLite job queue and deterministic source resolver foundations.
- Synthetic canary generator.
- Experimental BeamNG `.ter` v9 and DAE serializers.
- Deterministic ZIP packaging.
- Static ZIP validator and negative fixtures.
- SpawnSphere/SpawnSphereMarker canary objects.
- Straight physical road and AI DecalRoad alignment.
- Material and stock dependency checks.

## Verification state

### Unit tested

- 96 tests were reported passing at commit time.
- Re-run the suite before making a new completion claim.

### Statically validated

- 20 static checks were reported passing at commit time.
- This result does not prove BeamNG scene loading.
- The validator accepted an artifact later rejected by BeamNG, so scene graph
  checks require correction.

### Runtime verified

No.

### Runtime failure evidence

- BeamNG `0.38.6.0.19963`.
- Active and rotated logs contain the `levels/test_level` expanded mission
  error.
- The level ZIP mounts but the mission does not load.

### Not yet proven

- Valid split scene hierarchy.
- Terrain binary load and rendering.
- Spawn.
- Physical collision and full-road drive.
- Materials.
- AI navigation.
- Save/reload persistence.
- Clean BeamNG log.

## Known evidence integrity issue

Ignored/manual artifacts were modified after commit and received different
hashes. They must not be treated as committed output. Preserve each tested ZIP
with its SHA-256 and never edit it in place.

## Current investigation boundary

Read-only investigation only until approval:

- compare the exact installed failing ZIP with BeamNG 0.38.6 stock and a small
  engine-saved golden;
- classify differences as proven requirements, stock conventions, likely
  defects, or hypotheses;
- focus on root MissionGroup, `__parent`, `SimGroupEnd`, persistent identity,
  and split-file hierarchy;
- propose the smallest source-level fix and validator regression tests.

Do not start real OSM/DEM/SUMO Phase 3 work while the synthetic BeamNG target
cannot pass the runtime load gate.

## Next action

Follow `docs/CURRENT_HANDOFF.md`.
