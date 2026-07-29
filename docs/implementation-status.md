# Implementation Status

## Overview
**Repository:** C:\TriWorld  
**Branch:** audit-and-evidence  
**Commit:** (uncommitted - working tree has new docs/adr/ files)  
**Dirty/Untracked Files Preserved:** All existing user files (.hermes.md, HERMES_START_HERE.md, HERMES_TRIWORLD_MASTER_PROMPT_2026.md, README.md, RESEARCH.md, docs/, fixtures/, packages/, pyproject.toml, test_output.net.xml, tests/)

## Detected Toolchain

| Tool | Version | Status |
|------|---------|--------|
| Python | 3.11.11 (primary), 3.12.8 (available) | ✅ |
| pip | 26.0.1 | ✅ |
| uv | Not in PATH | ❌ |
| Node.js | 24.13.1 | ✅ |
| npm | 11.10.1 | ✅ |
| SUMO | 1.27.1 | ✅ |
| netconvert | 1.27.1 | ✅ |
| GDAL | Not installed | ❌ |
| PROJ | Not installed | ❌ |
| Blender | 3.6.5 (C:\Program Files\Blender Foundation\Blender 3.6) | ⚠️ Old version |
| BeamNG.drive | 0.38.6.0 (build 19963) | ✅ |
| BeamNG User Path | C:\Users\tomisu\AppData\Local\BeamNG\BeamNG.drive\current\ | ✅ |
| Italy Map | Present at content/levels/italy.zip | ✅ |

## Hermes Configuration
- **Web Backend:** Nous subscription (Firecrawl, FAL, OpenAI TTS/Whisper, Browser Use)
- **Delegation:** max_concurrent_children=3, max_spawn_depth=1, orchestrator_enabled=true
- **NotebookLM:** Disabled (no Enterprise project configured)

## Documentation Created (Phase 0)

### Core Docs
- ✅ `docs/implementation-status.md` (this file)
- ✅ `docs/research/environment-report.md`
- ✅ `docs/research/evidence-ledger.md`
- ✅ `docs/research/version-lock.md`
- ✅ `artifacts/environment/environment-report.json`

### ADRs (Architecture Decision Records)
- ✅ `docs/adr/0001-canonical-world-road-terrain-mesh-ir.md`
- ✅ `docs/adr/0002-local-map-frame-and-crs.md`
- ✅ `docs/adr/0003-sumo-authority-boundary.md`
- ✅ `docs/adr/0004-terrain-representation-and-vertical-datum.md`
- ✅ `docs/adr/0005-beamng-target-and-road-architect-boundary.md`
- ✅ `docs/adr/0006-portable-vs-stock-dependent-assets.md`
- ✅ `docs/adr/0007-deterministic-builds-and-provenance.md`
- ✅ `docs/adr/0008-runtime-qa.md`
- ✅ `docs/adr/0009-local-job-queue-and-recovery.md`
- ✅ `docs/adr/0010-security-and-trust-boundaries.md`

### Operations
- ✅ `docs/operations/risk_register.md` (20 risks, top 10 identified)
- ✅ `docs/operations/state_machine.md` (16 stages with weights)
- ✅ `docs/operations/test_matrix.md` (unit, property, synthetic, integration, UI, runtime QA, performance)

## First Vertical-Slice Milestone
**Phase 2: Synthetic Canary BeamNG Level**
- Flat terrain (256×256m)
- One straight road (500m, 7m wide)
- One TSStatic road chunk (DAE)
- One AI DecalRoad
- One spawn point
- One material (asphalt)
- Deterministic ZIP
- **Gate:** Structural audit + Runtime load-and-drive test

## Current Blockers

| Blocker | Severity | Resolution |
|---------|----------|------------|
| GDAL/PROJ not installed | High | Install via conda-forge/Pixi or OSGeo4W |
| Blender 3.6.5 (not 4.5 LTS) | Medium | Install Blender 4.5 LTS, verify Collada |
| uv not installed | Medium | `pip install uv` or use conda |
| No pyproject.toml with dependencies | High | Create full pyproject.toml with all packages |

## Next Concrete Action
1. Install GDAL/PROJ via Pixi/conda-forge environment
2. Install Blender 4.5 LTS
3. Install uv
4. Create complete `pyproject.toml` with all package definitions
5. Run `uv python pin 3.12` and `uv sync --all-groups`
6. Create `packages/contracts` with Pydantic schemas (MapFrame, WorldIR, RoadNetworkIR, etc.)
7. Build synthetic canary (Phase 2)

## Evidence State Summary

| Claim | State |
|-------|-------|
| Python 3.11/3.12 available | ✅ runtime verified |
| Node 24.13.1 available | ✅ runtime verified |
| SUMO 1.27.1 with GDAL support | ✅ runtime verified |
| BeamNG 0.38.6.0.19963 installed | ✅ runtime verified |
| Italy map present | ✅ filesystem verified |
| Blender 3.6.5 installed | ✅ runtime verified (but old) |
| GDAL/PROJ available | ❌ not installed |
| uv available | ❌ not installed |
| DecalRoad width = half vs full | not yet proven |
| .ter binary format exact spec | not yet proven |
| SUMO netOffset sign convention | not yet proven |
| Deterministic ZIP achievable | not yet proven |
| Runtime QA passes | not yet proven |