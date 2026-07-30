# TriWorld Current Handoff

**Purpose:** authoritative continuation checkpoint. Replace stale facts; do not
append a progress diary.

**Updated:** 2026-07-30
**Repository:** `C:\TriWorld`
**Branch:** `audit-and-evidence`
**Implementation checkpoint:** the commit containing this file; verify with
`git rev-parse HEAD`.

## Current objective

Complete the Phase 2 synthetic BeamNG canary as a trustworthy minimum runtime
foundation before advancing to real OSM/DEM/SUMO map generation.

Current gate:

`B1.2 ORDINARY DAE ROAD MATERIAL — IMPLEMENTED AND STATICALLY VALIDATED — RUNTIME FAILED`

Do not restart Phase 0/1 or repeat closed B2/B1.1 experiments. Do not start
Phase 3 until the B1.2 candidate is runtime checked and the Phase 2 changes are
reviewed and committed.

## Working-tree state

The restored Phase 2 recovery source, tests, and universal documentation are
committed together in the checkpoint containing this file.

After the checkpoint verification run, generated/unrelated workspace items
remained outside the commit: a modified tracked `.pyc`, local helper scripts,
and `scratch/`. Inspect `git status --short --branch` before any work. Do not
stage generated, scratch, cache, or unrelated files blindly.

## Last runtime-proven baseline

Artifact:

`C:\TriWorld\artifacts\material_recovery_b11b.zip`

SHA-256:

`17e3b6f7eccfa3893fd57495e2ea8b16d693ef1a310134f3ab08fc42c2146004`

Pinned runtime:

`BeamNG.drive 0.38.6.0.19963`

Observed runtime evidence for this exact artifact:

- level discovered and loaded;
- scene hierarchy deserialized without errors;
- daylight/environment active;
- vehicle spawned at `(0, 250, 0.5)`;
- terrain, physical road and vehicle vertically aligned;
- vehicle supported and driveable;
- terrain rendered with detailed asphalt;
- `Missing Terrain texture`: 0;
- `WARNING_MATERIAL`: 0;
- invalid material-wrapper errors: 0;
- terrain collision resolved without ground-model fallback.

Remaining visual defect in this baseline: the Collada/TSStatic road strip used an
unresolved white material. That defect is the isolated B1.2 scope.

The currently installed mod was still this B1.1b artifact at the last inspection;
its installed SHA-256 matched the value above.

## B1.2 E1 candidate and runtime result

Artifact:

`C:\TriWorld\artifacts\material_recovery_b12_fix.zip`

SHA-256:

`8e93c389c6f9c5432cfd0f71392c7232bccdf90950845296c7e4ac5820975840`

Implemented B1.2 change:

- Collada geometry binds material symbol `triworld_road_asphalt`;
- a separate ordinary BeamNG `Material` with matching `mapTo` is emitted under
  `art/shapes/roads/main.materials.json`;
- terrain layers remain `TerrainMaterial` objects and are not reused as ordinary
  mesh materials;
- the validator rejects missing, mismatched, or terrain-class DAE bindings.

Fresh verification performed from the current working tree:

```text
.venv\Scripts\python.exe -m pytest tests -q
159 passed, 4 pre-existing datetime.utcnow deprecation warnings

validate_zip_structure(artifacts/material_recovery_b12_fix.zip)
24/24 checks passed
```

This proves implementation, unit tests, and static package validation.

The exact E1 artifact above was runtime tested. Result: **FAILED** — the road
rendered BeamNG's orange `NO MATERIAL` diagnostic surface. Geometry, terrain,
spawn, daylight and alignment still worked. A fresh
`temp/levels/synthetic_canary/art/shapes/roads/straight_road.cdae` was generated
during the run, disproving reuse of the legacy `test_level` compiled shape as
the E1 cause.

Preserved E1 log:

`C:\TriWorld\artifacts\evidence\beamng_b12_e1_20260730_220439.log`

The runtime-proven B1.1b baseline `17e3b6f7...` is restored and installed.

## Closed recovery findings that must not regress

- BeamNG 0.38.6 split scene hierarchy uses nested `items.level.json` files and
  explicit `__parent`; serialized `SimGroupEnd` objects are invalid.
- Selector metadata uses `title`, `authors`, `previews`, and valid spawn metadata.
- `SpawnSphere.position` and `rotationMatrix` require numeric arrays for the
  proven canary.
- `.ter` v9 height samples use unsigned local heights; world offset belongs in
  the TerrainBlock transform.
- For the proven v9 target, the binary layout has height map, layer map, then the
  material table; no extra `layerTextureMap` block.
- Material count is `u32`; each material-name length is `u8`.
- Terrain materials require a flat material dictionary,
  `TerrainMaterialTextureSet`, matching `TerrainMaterial.internalName`, and the
  TerrainBlock `materialTextureSet` reference.
- A valid `ScatterSky` plus `TimeOfDay` configuration is required for usable
  daylight.
- Static validation previously accepted runtime-invalid packages. Preserve the
  adversarial regression fixtures added for every discovered defect.

## Not yet proven

- B1.2 ordinary DAE material renders correctly in BeamNG 0.38.6.
- Full Phase 2 save/reload behavior.
- AI route query/traffic behavior; a DecalRoad loading without errors is not
  sufficient proof.
- Real-world OSM/DEM/SUMO generation and Italy-level quality.

## Preserve

- The immutable B1.1b runtime-proven ZIP and its runtime log/evidence.
- The B1.2 candidate under its exact hash.
- Unrelated dirty work and `scratch/` until ownership is reviewed.
- Stock BeamNG content as read-only evidence; never copy it into distributable
  TriWorld artifacts.

## Next falsifiable action

Determine ordinary Material discovery/binding for TSStatic meshes. Prefer a
verified runtime registry query for `triworld_road_asphalt` with a working stock
Material as positive control. If that is unavailable, create one deterministic
candidate from the restored recovery source that changes exactly one Material
schema variable relative to E1. Do not combine `colorMap`, primitive type, XML
ordering, or UV changes in one experiment.

Artifacts produced from the quarantined detached `52a5dfb` checkout are invalid
and must never be used as candidates.

Important source/baseline distinction: checkpoint source already contains
`colorMap`, `triangles`, changed COLLADA ordering, and changed UV generation.
It is therefore not the byte-equivalent E1 source. Do not propose “add
colorMap” against the checkpoint; the field already exists. A valid E2 isolation
must first prove, using literal machine output, that its generated DAE is
byte-identical to E1 and that `colorMap` is the only functional artifact change.
