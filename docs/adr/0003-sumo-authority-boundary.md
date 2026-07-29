# ADR 0003: SUMO Authority Boundary

**Status:** Accepted
**Date:** 2026-07-29

## Context
SUMO is used for road network topology, lane connections, and traffic simulation. We must define exactly what SUMO is authoritative for and what it is NOT.

## Decision
**SUMO IS authoritative for:**
- Lane-level topology (edges, lanes, connections)
- Junction internal structure (internal edges, connections)
- Traffic light logic (if enabled)
- Routing graph for traffic simulation
- Validation of OSM topology (netcheck, routing test)

**SUMO is NOT authoritative for:**
- Final road elevation (CivilRoadIR owns vertical alignment)
- Physical road geometry / mesh (MeshIR owns 3D geometry)
- BeamNG collision mesh (MeshIR + BeamNGTargetIR)
- Terrain formation (TerrainIR)
- Road cross-section design (CivilRoadIR)
- Bridge/tunnel 3D structure (CivilRoadIR + MeshIR)

**Boundary Enforcement:**
- SUMO output (`.net.xml`) parsed into RoadNetworkIR enrichment
- SUMO lane connections → RoadNetworkIR junction connectivity
- SUMO elevation IGNORED (CivilRoadIR computes independent vertical solution)
- SUMO geometry IGNORED for mesh (CivilRoadIR re-resamples horizontal, computes vertical)
- SUMO used as independent topology check only

**Two Config Profiles:**
1. `physical-fidelity.netccfg` — Preserves OSM geometry, no `--geometry.remove`, no `--ramps.guess`
2. `traffic-enriched.netccfg` — Optional, adds TLS, may simplify for routing

**Mapping:**
```
OSM way/node ↔ SUMO edge/lane ↔ RoadNetworkIR corridor ↔ CivilRoadIR corridor ↔ BeamNG AI DecalRoad
```
Mapping stored in build report and debug GeoJSON.

## Alternatives
- Use SUMO elevation directly → Rejected: SUMO elevation is simplistic, not engineered
- Use SUMO geometry for mesh → Rejected: SUMO geometry is 2D centerlines, not 3D road surface
- Skip SUMO entirely → Rejected: Lose independent topology validation and lane connections

## Consequences
- CivilRoadIR must solve vertical alignment independently
- Junction patches built from CivilRoadIR, not SUMO internal edges
- SUMO warnings classified: blocking vs informational

## Evidence
- Master prompt §10: "SUMO — presná zodpovednosť", "SUMO nie je: zdroj finálnej vozovkovej výšky..."

## Revisit Trigger
- If SUMO adds engineered vertical alignment features
- If netconvert geometry output improves significantly
- If we need traffic simulation output as deliverable