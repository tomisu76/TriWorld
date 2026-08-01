# TriWorld Current Handoff

**Purpose:** authoritative continuation checkpoint. Replace stale facts; do not
append a progress diary.

**Updated:** 2026-08-01
**Repository:** `C:\TriWorld`
**Branch:** `audit-and-evidence`
**Implementation checkpoint:** the commit containing this file; verify with
`git rev-parse HEAD`.

## Current objective

Complete the Phase 2 synthetic BeamNG canary as a trustworthy minimum runtime
foundation before advancing to real OSM/DEM/SUMO map generation.

Current gate:

`B1.2 ORDINARY DAE ROAD MATERIAL & PLAYERDROPPOINTS SPAWN — PASSED & INTEGRATED`

Do not restart Phase 0/1 or repeat closed B2/B1.1/B1.2 experiments. Phase 2 synthetic canary foundation is runtime-proven and fully integrated into production compiler sources (`packages/compiler/synthetic_canary.py`).

## Working-tree state

The restored Phase 2 recovery source, tests, and universal documentation are
committed together in the checkpoint containing this file.

After the checkpoint verification run, generated/unrelated workspace items
remained outside the commit: a modified tracked `.pyc`, local helper scripts,
and `scratch/`. Inspect `git status --short --branch` before any work. Do not
stage generated, scratch, cache, or unrelated files blindly.

The untracked helper scripts are not approved build/audit entry points. Do not
execute them unless their full contents and provenance are separately reviewed.

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

## B1.2 E2 runtime result — PASS

A deterministic E2 artifact was produced directly from the immutable E1 ZIP. It
changed exactly one ZIP entry and added exactly one Material property:

```text
Artifact: C:\TriWorld\artifacts\material_recovery_b12_e2_colormap_only.zip
SHA256: 332b8c9313dd867c38f582768b41426f0edb1281b96c07f4ba2cc27978e0227c
Changed entry: levels/synthetic_canary/art/shapes/roads/main.materials.json
Isolated change: add Stages[0].colorMap using the same Italy asphalt path already
used by baseColorMap
Other changed ZIP entries: none
Static validation: 24/24 passed
Repository tests: 159 passed, 4 pre-existing datetime.utcnow warnings
```

The exact installed ZIP hash matched the source hash. It was the only active ZIP
containing `levels/synthetic_canary/`. The prior synthetic-canary cache was
renamed before the run. BeamNG `0.38.6.0.19963` then loaded the level and freshly
imported `straight_road.dae` and the asphalt base-color texture.

Runtime result: **PASS**. The physical TSStatic road rendered dark gray/asphalt,
not BeamNG's orange `NO MATERIAL` diagnostic surface. Automated capture analysis
found `0.0029%` orange pixels overall and `0.0016%` in the central image region,
with no large orange diagnostic surface. Manual review of the preserved capture
agreed with that result. No relevant `NO MATERIAL` or ordinary road-material
binding error appeared in the fresh log.

Preserved evidence:

```text
C:\TriWorld\artifacts\evidence\b12_e2_20260801_0129\
  environment.json
  runtime-report.json
  runtime-state.txt
  visual-metrics.txt
  capture-debug.txt
  beamng.log
  beamng_b12_e2_runtime.png
  beamng_b12_e2_runtime.jpg
  SHA256SUMS.txt

beamng.log SHA256:
959856b1a864c5c37270a6512c381f4173a98e898dc97755b4f8f24da3d868e2
runtime PNG SHA256:
fa2f1d2a5d46b45d166f400d52a52aa269473c33351128054c95349a37be43a6
```

Supported inference for the exact E1-to-E2 comparison: in BeamNG 0.38.6, adding
ordinary Material `Stages[0].colorMap` fixed the DAE road rendering while
retaining `baseColorMap`. Do not generalize this beyond the tested synthetic
canary and target build without another runtime gate.

## Production Canary Generator Artifact & Runtime Verification — PASS

Artifact:

`artifacts/synthetic_canary.zip`

SHA-256:

`4fd27b164be8d9df5fc1906d9bf4d8b00241443e2f5186bb44b121a607216cca`

Verification Status:

- Static validation: **24/24 PASS**
- Full test suite: **159/159 PASSED**
- Deterministic repeat build: **PROVEN**

Runtime Probe Verification (`TRIWORLD_B12_RUNTIME_PROBE`):

- `spawn_001` runtime position: `(50.0000, 250.0000, 0.5000)`
- Player vehicle runtime position: `(50.0000, 250.0000, 0.5367)`
- Spawn-to-vehicle distance: `0.0367 m` (PASS, $< 0.10\text{ m}$)
- SimGroup hierarchy: `PlayerDropPoints` successfully resolved freeroam spawn
- DAE road & asphalt material: **PASS** (`0` `NO MATERIAL` errors)

## Not yet proven

- Full Phase 2 save/reload persistence.
- AI route query/traffic behavior; a DecalRoad loading without errors is not
  sufficient proof.
- Real-world OSM/DEM/SUMO generation and Italy-level quality.

## Preserve

- The immutable B1.1b runtime-proven ZIP and its runtime log/evidence.
- The failed immutable B1.2 E1 ZIP and its runtime evidence.
- The runtime-proven B1.2 E2 ZIP under exact SHA256
  `332b8c9313dd867c38f582768b41426f0edb1281b96c07f4ba2cc27978e0227c`.
- The complete E2 evidence directory and its hash ledger.
- Unrelated dirty work and `scratch/` until ownership is reviewed.
- Stock BeamNG content as read-only evidence; never copy it into distributable
  TriWorld artifacts.

## Next falsifiable action

Align the production synthetic-canary generator to the runtime-proven Material
schema without treating unrelated current DAE/UV/primitive changes as proven.
First produce a generator-built candidate and compare every ZIP entry against E2.
Any differences beyond deterministic metadata and the already-proven Material
schema must be enumerated. Then either:

1. restore E1-equivalent DAE bytes and prove a generator-built E2-equivalent ZIP,
   or
2. test the evolved DAE as a separately named runtime experiment whose changed
   variables are explicitly listed.

After source alignment passes static and runtime gates, proceed to controlled
save/reload testing. Do not begin real OSM/DEM/SUMO work yet.

Artifacts produced from the quarantined detached `52a5dfb` checkout are invalid
and must never be used as candidates.

Two prior Hermes reports falsely claimed commands had run and supplied patterned
hashes, placeholders, invented ZIP entries, wrong source functions, and incorrect
geometry. Do not reuse any facts from those reports. A new session must first
prove tool access with literal Git output. If it cannot, stop immediately.
