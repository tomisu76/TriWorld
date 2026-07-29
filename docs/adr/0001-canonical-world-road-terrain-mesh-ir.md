# ADR 0001: Canonical World, Road, Terrain, Mesh IR

**Status:** Accepted
**Date:** 2026-07-29

## Context
TriWorld must transform OSM/DEM data into a drivable BeamNG map. The pipeline involves multiple coordinate systems, data formats, and processing stages. We need a single source of truth for each domain that is versioned, serializable, and independent of any specific tool or format.

## Decision
Define immutable, versioned Intermediate Representations (IRs) as the canonical data contracts:

1. **MapFrame** — CRS, projection, anchor, axis convention, vertical datum
2. **WorldIR** — Container for all domain IRs
3. **RoadNetworkIR** — Topology, geometry, attributes from OSM
4. **CivilRoadIR** — Engineered horizontal/vertical alignment, cross-sections, junctions
5. **TerrainIR** — DEM, formation surface, cut/fill, material masks
6. **MeshIR** — Format-agnostic mesh (positions, normals, UVs, indices, materials, collision, LOD)
7. **BeamNGTargetIR** — BeamNG-specific serialization target (TSStatic, DecalRoad, TerrainBlock, etc.)

Each IR:
- Has a schema version
- Is serializable to JSON (for debugging/audit) and binary (for performance)
- Contains provenance (source hashes, tool versions, timestamps)
- Is validated by independent validators before progressing to next stage

## Alternatives
- Use OSM XML directly throughout → Rejected: OSM is not engineered road data, no vertical alignment, no junction patches
- Use SUMO .net.xml as canonical → Rejected: SUMO is traffic topology, not 3D road geometry
- Use BeamNG items.level.json as canonical → Rejected: BeamNG format is output-only, not editable, version-dependent
- Use OpenDRIVE as canonical → Rejected: Good for road design but not terrain/mesh/assets, overkill for MVP

## Consequences
- More upfront schema design work
- Clear boundaries between pipeline stages
- Enables deterministic rebuilds from any IR stage
- Allows multiple output targets (BeamNG, Blender QA, glTF preview)
- Requires disciplined versioning of IR schemas

## Evidence
- Master prompt §6: "Zdrojom pravdy sú verzované, serializovateľné a nemenné doménové modely"
- Master prompt §6.1–6.7: Detailed IR specifications

## Revisit Trigger
- If any IR schema changes breaking downstream stages
- If new output target requires additional IR fields
- If performance requires binary IR format