# TriWorld Implementation Status

This is a durable capability and verification inventory. It is not a chat log or
task prompt. The current execution authority is
[`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).

**Repository:** `C:\TriWorld`
**Branch:** `audit-and-evidence`
**Pinned BeamNG target:** `0.38.6.0.19963`

## Evidence vocabulary

The meanings of `implemented`, `unit tested`, `statically validated`,
`integration tested`, `runtime verified`, `visually inspected`, and
`not yet proven` come exclusively from
[`HERMES_VERIFICATION_RULES.md`](hints/HERMES_VERIFICATION_RULES.md).

Verification is scoped to an exact artifact and environment. A later source
change does not inherit an earlier artifact's runtime status.

## Current phase

Phase 2 synthetic BeamNG canary recovery.

- Last runtime-proven baseline: B1.1b terrain/material recovery.
- Newest candidate: B1.2 ordinary DAE road-material recovery.
- B1.2 state: implemented and statically validated; E1 runtime failed with
  BeamNG's orange `NO MATERIAL` surface.
- Phase 3 real-world generation: not started and gated on Phase 2 closure.

Exact hashes, dirty files, commands, blockers and the next action are maintained
only in `CURRENT_HANDOFF.md`.

## Capability matrix

| Capability | Implementation | Strongest current evidence | Remaining gate |
|---|---|---|---|
| Pydantic contracts and deterministic foundations | Implemented | Unit tested | Evolve with each pipeline contract |
| SQLite job queue | Implemented | Unit tested | End-to-end recovery/load testing |
| OSM source resolver/parser foundation | Implemented | Unit tested | Real acquisition and topology pipeline |
| DEM resolver foundation | Implemented | Unit tested | Real source, CRS, void and quality gates |
| Provenance records | Implemented | Unit tested | Full release manifest and license audit |
| Spatial helpers | Implemented | Unit tested | End-to-end projected-area tests |
| Deterministic ZIP packaging | Implemented | Unit/static tested | Reproducible full-map builds |
| BeamNG level discovery metadata | Implemented | Runtime verified in Phase 2 baseline | Preserve across generator evolution |
| Nested BeamNG scene hierarchy | Implemented | Runtime verified in Phase 2 baseline | Save/reload and larger scenes |
| SpawnSphere placement | Implemented | Runtime and visually verified | Multiple spawn policies |
| `.ter` v9 serialization | Implemented for pinned target | Runtime verified in Phase 2 baseline | Non-flat real terrain and broader fixtures |
| Terrain height alignment/collision | Implemented for canary | Runtime and visually verified | Slopes, edges and real terrain |
| Terrain material table and texture set | Implemented | Runtime and visually verified in B1.1b | Multiple real land-cover layers |
| Environment/daylight | Implemented for canary | Runtime and visually verified | Weather/time presets and visual QA |
| TSStatic Collada road geometry | Implemented | Geometry/collision baseline runtime verified | B1.2 material runtime gate, then complex roads |
| Ordinary DAE road material binding | Implemented in B1.2 candidate | Unit/static validated; E1 runtime failed with `NO MATERIAL` | Prove Material discovery and DAE-to-`mapTo` binding |
| DecalRoad alignment | Implemented for canary | Static and runtime-load evidence | AI route query and traffic behavior |
| Static BeamNG ZIP validator | Implemented | 24 checks on current B1.2 candidate plus adversarial tests | Keep independent from generator assumptions |
| Runtime evidence workflow | Partially implemented/manual | Repeated controlled canary experiments | Automate evidence capture safely |
| Real terrain/OSM/SUMO compiler | Foundation only | Not yet proven | Phase 3+ implementation |
| One-click application and production UI | Not complete | Not yet proven | Later product phases |
| Italy-quality generated level | Not complete | Not yet proven | Full product acceptance suite |

## Phase 2 proven runtime foundation

The pinned BeamNG runtime has demonstrated, on preserved canary artifacts:

- level discovery and loading;
- valid split scene hierarchy without `SimGroupEnd`;
- deterministic spawn at `(0, 250, 0.5)`;
- terrain/road/spawn vertical alignment;
- vehicle support and drivability;
- daylight and environment creation;
- `.ter` v9 material-name parsing;
- terrain textures without magenta or missing-texture errors;
- terrain ground model without `WARNING_MATERIAL` fallback.

These facts do not prove AI traffic, save/reload, complex geometry, or real-world
map generation.

B1.2 E1 additionally proved that the TSStatic geometry imports and produces a
fresh compiled `.cdae`, while its ordinary Material remains unresolved. This
narrows the open gate without closing it.

## Required non-regression gates

Every BeamNG package change must retain:

- one safe level root and portable paths;
- valid selector metadata and previews;
- deterministic timestamps and package identity;
- valid LDJSON and nested parent hierarchy;
- no runtime-invalid `SimGroupEnd`;
- asset-reference and case checks;
- strict `.ter` structure and exact material-table parsing;
- terrain texture-set/internal-name linkage;
- separation of `TerrainMaterial` and ordinary mesh `Material`;
- DAE symbol-to-`mapTo` resolution;
- physical-road, AI-road and spawn alignment;
- daylight object constraints;
- negative fixtures proving malformed variants fail.

Static gates remain necessary but insufficient. Claims about loading, rendering,
collision, AI, save/reload, or driving require the corresponding runtime gate.

## Phase transition policy

A phase closes only when:

1. its acceptance criteria are written and unchanged during evaluation;
2. implementation and adversarial regression tests pass;
3. a deterministic artifact is preserved with SHA-256;
4. static/integration gates pass;
5. required pinned-runtime and visual gates pass;
6. logs and evidence are preserved;
7. handoff, this inventory, ADRs and operations documents are updated;
8. the focused diff is reviewed and committed when authorized.

When all implementation phases are complete, this document becomes a release
capability matrix. Maintenance work must continue to use the same evidence
discipline rather than restarting the original greenfield plan.
