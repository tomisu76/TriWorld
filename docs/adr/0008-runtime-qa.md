# ADR 0008: Runtime QA

**Status:** Accepted
**Date:** 2026-07-29

## Context
The ultimate validation is loading the generated map in BeamNG and driving it. We must define the runtime QA gates.

## Decision
**Clean Test Protocol:**
1. Build release ZIP
2. Record ZIP SHA256
3. Remove/unpack any working level from BeamNG user paths
4. Disable other mods
5. Install only this ZIP
6. Verify installed hash matches
7. Launch exact BeamNG version
8. Load level
9. Capture log from clean timestamp

**Mandatory Checks:**
- Level appears in menu
- Level loads without error
- Terrain visible
- Materials render (no pink/missing)
- Daylight works
- Spawn correct (on road, oriented, no fall)
- Vehicle doesn't fall through
- Road collision continuous
- No invisible terrain collision through road
- Main route drivable
- At least one junction
- At least one slope
- At least one curve/banked section (if exists)
- AI path query works
- AI drives reference route (if AI declared)
- Save/reload doesn't change level
- Log has no critical missing asset/JSON/Lua/collision errors

**Evidence Artifacts (`artifacts/runtime/<build-id>/`):**
- `environment.json` — BeamNG version, OS, GPU, mods
- `installed-zip.sha256`
- `beamng.log` (full)
- `runtime-report.json` (structured results)
- `route.geojson` (driven path)
- `screenshots/` — spawn, road, junction, terrain
- `video-or-telemetry/` — if capture works

**Runtime QA Status:**
```json
{
  "beamngVersion": "0.38.6.0.19963",
  "zipSha256": "...",
  "listed": true,
  "loaded": true,
  "spawned": true,
  "drivenDistanceM": 1200,
  "fellThrough": false,
  "aiRoutePassed": true,
  "criticalLogErrors": [],
  "status": "passed"
}
```

**UI Automation:** If Windows capture fails for D3D window, use BeamNG screenshot mechanism or other version-verified method. Never accept blank screenshot.

**Gate:** Release/publish requires `runtimeVerified`. Download after static QA may be allowed but labeled `runtime-unverified`.

## Alternatives
- Trust static validation only → Rejected: Too many runtime-only failure modes
- Manual testing only → Rejected: Not reproducible, doesn't scale

## Consequences
- Requires BeamNG installation on test machine
- Self-hosted Windows runner likely needed for CI
- Runtime gate is final authority

## Evidence
- Master prompt §24: "BeamNG runtime QA — Toto je posledná autorita."

## Revisit Trigger
- BeamNG version upgrade (re-run canary)
- New failure mode discovered in runtime