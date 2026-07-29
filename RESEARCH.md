# TriWorld Research & Implementation Plan

Date: 2026-07-29
Version: 1.0.0
Project: TriWorld - One-click BeamNG Map Studio

> Status: initial scaffold. Version numbers and architecture below are planning
> hypotheses until `docs/research/environment-report.md`,
> `docs/research/version-lock.md` and the evidence ledger verify the actual
> environment and current primary sources.

## Purpose
This document tracks the research, dependencies, and architectural decisions for the TriWorld project, aiming to create a deterministic, one-click BeamNG map generator based on geospatial data (OSM, DTM).

## Dependencies & Versions
- Node.js: 22+ (LTS recommended)
- Python: 3.12+ (managed via pixi/conda)
- GDAL: 3.9+
- PROJ: 9.4+
- BeamNG.drive: 0.38.6.0 (target)
- SUMO: 1.27.1

## Legal & Compliance
- OSM ODbL License: Attribution required. No bulk tiles from openstreetmap.org.
- BeamNG EULA: No copyright protected assets redistribution without explicit permission.

## Roadmap
1. Phase 0: Research, ADRs, Contracts
2. Phase 1: Offline Vertical Slice (Deterministic Map-to-ZIP)
3. Phase 2: MapFrame and Source Adapters
4. Phase 3: SUMO Topology
5. Phase 4: Civil Design & Terrain Formation
6. Phase 5: BeamNG Preview Target
7. Phase 6: Road Architect Bake Agent
8. Phase 7: Scenery & Biomes
9. Phase 8: Production UI & QA Dashboard
10. Phase 9: Installer & Release
