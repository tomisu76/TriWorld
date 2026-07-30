# Phase 1: Contracts and Deterministic Infrastructure

> **ARCHIVED HISTORICAL PLAN**
>
> This checklist describes the original Phase 1 planning state. It is not the
> current work queue. New sessions must use `docs/CURRENT_HANDOFF.md` and
> `docs/implementation-status.md`; do not resume unchecked items from this file.

## Packages Structure

```
packages/
├── contracts/          # Pydantic v2 data contracts (MapFrame, WorldIR, RoadNetworkIR, etc.)
├── compiler/           # Pipeline stages
│   ├── acquisition/    # OSM/DEM fetchers with cache
│   ├── spatial/        # MapFrame, CRS transforms, reprojection
│   ├── topology/       # OSM → RoadNetworkIR, SUMO adapter
│   ├── civil/          # CivilRoadIR (horizontal, vertical, cross-sections, junctions)
│   ├── terrain/        # Road-first terrain formation
│   ├── mesh/           # MeshIR, chunking, DAE serializer
│   ├── decoration/     # Markings, props, vegetation
│   └── validation/     # IR validators, mesh/terrain validators
├── sumo_adapter/       # SUMO netconvert wrapper, .net.xml parser, mapping
├── beamng_target/      # BeamNG serializer (TSStatic, DecalRoad, TerrainBlock, ZIP)
├── beamng_runtime_qa/  # Clean profile launch, drive test, evidence collection
├── blender_qa/         # Headless Blender audit
└── asset_registry/     # Asset registry, placement rules
```

## Phase 1 Goals (Contracts & Infrastructure)
- [x] Pydantic schemas: MapCompilationRequest, MapFrame, RoadNetworkIR
- [ ] CivilRoadIR, TerrainIR, MeshIR, BeamNGTargetIR
- [ ] Job queue (SQLite) with state machine
- [ ] Workspace layout (artifacts/jobs/<jobId>/...)
- [ ] Deterministic hashing & canonicalization
- [ ] Unit + property tests for contracts

## Next Steps
1. Complete remaining IR schemas (CivilRoadIR, TerrainIR, MeshIR, BeamNGTargetIR)
2. Create job queue with SQLite persistence
3. Implement job workspace structure
4. Add canonical JSON serialization with deterministic ordering
5. Write property-based tests for coordinate transforms
