# ADR 0005: BeamNG Target and Road Architect Boundary

**Status:** Accepted
**Date:** 2026-07-29

## Context
BeamNG has two road systems: the legacy `DecalRoad` (AI, spline-based) and the newer `MeshRoad` (physical mesh with collision). Road Architect is an editor tool that can bake roads. We must define what TriWorld generates and the Road Architect boundary.

## Decision
**Primary Output (Portable Runtime):**
- **Physical Road:** `TSStatic` + DAE mesh chunks (render + collision)
- **AI Road:** `DecalRoad` (single centerline per logical corridor, positive drivability)
- **Visual Decals:** Additional `DecalRoad` for edge lines, center lines (drivability = 0)
- **Terrain:** `TerrainBlock` + `.ter` + `.terrain.json`
- **Materials:** `main.materials.json` with map-prefixed names
- **Spawn:** `Spawnpoints/items.level.json` with validated transform
- **Environment:** `Environment/items.level.json` (lighting, sky, ground models)

**Road Architect (Studio/Extended Path):**
- Session file (`.json`) exported alongside portable output
- **Not required** for portable map to function
- **Adapter per BeamNG version:** `packages/beamng_target/road_architect/adapters/beamng_<version>.py`
- Adapter declares capabilities: `supportsSessionLoad`, `supportsAutomatedBake`, `supportsSaveReloadProof`
- Automated bake only enabled after canary proves: load session → finalize → save → reload → verify persistence
- Portable fallback always remains functional

**DecalRoad Width Semantics:**
- TriWorld contract: nodes are `[x, y, z, halfWidth]`
- BeamNG serializer MUST canary-test exact version: does 4th parameter expect full width or half width?
- Conversion applied explicitly with version stamp
- Never assume based on field name or legacy behavior

**MeshRoad Usage:**
- Only for bridges/ramps where `TSStatic` DAE cannot achieve required geometry
- Each node: 8 numbers (pos.x, pos.y, pos.z, width, depth, normal.x, normal.y, normal.z) per BeamNG contract
- AI `DecalRoad` remains separate

**Terrain Block:**
- Binary `.ter` format per BeamNG version (validated by golden test vs World Editor save)
- Companion `.terrain.json` for metadata only
- Quantization: track min/max, zOffset, maxHeight, report RMS/max error

**Validation Gates:**
1. Structural audit (ZIP auditor)
2. BeamNG staging validator (info.json, LDJSON, .ter, materials, DAE refs, AI invariants)
3. Runtime QA (clean profile load → spawn → drive → save/reload)

## Alternatives
- Generate only Road Architect session → Rejected: Not portable, requires editor, not runtime
- Use only MeshRoad → Rejected: No AI, collision issues, not how Italy works
- Skip Road Architect entirely → Rejected: Studio path needs it for Italy-quality junctions

## Consequences
- Dual road representation (physical mesh + AI spline) maintained
- Version-pinned adapters for Road Architect
- Canary test required for every BeamNG version upgrade
- Portable map always works without Road Architect

## Evidence
- Master prompt §14: "Moderná štruktúra ZIP", "Cesty", "AI cesta"
- Master prompt §18: "Road Architect... Povinné rozhranie", "Automatizovaný bake"

## Revisit Trigger
- BeamNG version change (re-run canary)
- Road Architect API stabilization
- MeshRoad gains AI capability