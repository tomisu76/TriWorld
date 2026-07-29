# ADR 0009: Local Job Queue and Recovery

**Status:** Accepted
**Date:** 2026-07-29

## Context
Map generation is a long-running multi-stage pipeline. We need persistence, recovery, and progress tracking.

## Decision
**Job Storage:** SQLite database (`jobs.db`) with tables:
- `jobs` — id, status, request_json, created_at, updated_at, progress, current_stage, error_json
- `job_events` — job_id, stage, timestamp, message, metrics_json
- `job_artifacts` — job_id, path, sha256, bytes, kind

**State Machine (from Master Prompt §7):**
```
queued
→ validating_request
→ resolving_sources
→ fetching_osm
→ fetching_dem
→ normalizing_spatial_data
→ building_road_topology
→ running_sumo
→ designing_civil_roads
→ forming_terrain
→ building_meshes
→ building_visual_layers
→ placing_assets
→ serializing_beamng
→ validating_target
→ packaging
→ auditing_zip
→ ready
```

**Terminal States:** `ready`, `failed`, `cancelled`

**Stage Properties:**
- Stable name
- Percentage weight (for overall progress)
- Start/end timestamps
- SSE/WebSocket event emission
- Structured log entry
- Diagnostic metrics
- Safe cancellation support
- On error: human explanation + technical detail
- Next stage not marked complete without artifact

**Progress Event:**
```json
{
  "jobId": "job_01",
  "stage": "forming_terrain",
  "stageProgress": 0.62,
  "overallProgress": 0.54,
  "message": "Blending road formation into DEM",
  "metrics": {"corridorsDone": 79, "corridorsTotal": 128}
}
```

**Recovery:**
- On restart: resume from last completed stage (artifacts on disk)
- Checkpoint after each stage: all IR artifacts persisted
- Idempotent stages: can re-run safely
- Job workspace: `artifacts/jobs/<job-id>/` with sources/, ir/, staging/, reports/, preview/, logs/, release/

**Cancellation:**
- Cooperative: stage checks cancellation flag at safe points
- On cancel: mark `cancelled`, preserve artifacts for inspection
- Force kill: timeout + process tree termination

## Alternatives
- Redis queue → Rejected: Extra dependency, not needed for local-first
- In-memory only → Rejected: No recovery

## Consequences
- SQLite is simple, embedded, no server
- Stage checkpoints enable resume
- SSE provides live UI updates

## Evidence
- Master prompt §7: "Implementuj perzistentný stavový automat..."

## Revisit Trigger
- If job volume exceeds SQLite capacity
- If distributed workers needed