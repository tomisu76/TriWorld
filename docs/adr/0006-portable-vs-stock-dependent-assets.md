# ADR 0006: Portable vs Stock-Dependent Assets

**Status:** Accepted
**Date:** 2026-07-29

## Context
BeamNG's Italy map contains copyrighted assets. TriWorld must produce portable ZIPs that don't redistribute BeamNG stock content.

## Decision
**Three Asset Flavors:**

1. **`portable` (mandatory, default):**
   - Original TriWorld assets only
   - CC0/MIT/compatible licensed third-party assets
   - Verified redistributable BeamNG stock assets only
   - No dependency on user's installed game content

2. **`stock-italy-dependent` (optional, opt-in):**
   - References Italy assets via VFS paths (`/levels/italy/art/...`)
   - Read-only inventory at build time
   - Dependency manifest in build report
   - UI shows "Requires official Italy content"
   - ZIP contains NO stock files

3. **`studio-original` (future):**
   - TriWorld's own high-quality asset library
   - Authored in Blender, validated by Blender QA

**Asset Registry (`assets/registry.json`):**
```json
{
  "id": "guardrail_steel_a",
  "kind": "mesh",
  "source": "original",
  "license": "CC0-1.0",
  "author": "TriWorld",
  "redistribution": true,
  "paths": {
    "source": "assets/original/guardrail_steel_a/source.blend",
    "runtime": "levels/<slug>/art/shapes/roadside/guardrail_steel_a.dae"
  },
  "materials": ["tw_guardrail_steel"],
  "lods": ["a800", "a300", "a80"],
  "collision": "Colmesh-1",
  "placementRules": ["outside_shoulder", "dropoff_risk"],
  "sha256": {}
}
```

**Italy Asset Policy:**
- NEVER copy Italy assets to repo or ZIP
- NEVER commit Italy assets to Git
- Italy used ONLY as quality reference (structure, naming, LOD budgets)

## Alternatives
- Bundle Italy assets → Rejected: Copyright violation
- Require Italy for all maps → Rejected: Limits portability

## Consequences
- Portable maps have lower initial visual fidelity
- Clear licensing boundary
- Path to Italy-quality via studio-original assets

## Evidence
- Master prompt §15.1: "BeamNG Italy assety sú chránený stock obsah..."

## Revisit Trigger
- Studio-original library reaches critical mass
- BeamNG licensing changes
- Portable quality becomes blocking