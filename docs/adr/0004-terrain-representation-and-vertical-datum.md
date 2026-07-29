# ADR 0004: Terrain Representation and Vertical Datum

**Status:** Accepted
**Date:** 2026-07-29

## Context
Terrain data comes from DEM sources with varying vertical datums (ellipsoidal, orthometric/EGM96, unknown). Road design requires a consistent vertical reference. BeamNG terrain is a heightfield relative to local origin.

## Decision
**Vertical Datum Handling:**
1. **Record, don't assume:** Every DEM artifact stores its native vertical datum (`ellipsoidal`, `orthometric`, `unknown`). Never silently convert.
2. **MapFrame declares:** `verticalDatum: { name: "provider-native", normalization: "recorded-not-assumed" }`
3. **CivilRoadIR works in:** Local ENU Z (metres above MapFrame anchor). Anchor Z = 0 at MapFrame origin.
4. **DEM → Local Z:** 
   - If datum known: apply geoid model (EGM96/EGM2008) to convert to orthometric, then to local ENU via MapFrame anchor
   - If datum unknown: treat as-is, flag warning, use for macro terrain only
5. **Road-first formation:** Final terrain = DEM + road formation deltas (cut/fill). Road elevation is authoritative.

**TerrainIR Layers:**
- `originalDem` — raw provider data, native CRS, native vertical datum
- `nodataMask` — boolean mask
- `normalizedDem` — reprojected to MapFrame projected CRS, Z in local ENU (if datum known)
- `formationTarget` — CivilRoadIR formation surface (carriageway + shoulders + slopes)
- `cutFillDelta` — formationTarget - normalizedDem (positive = fill, negative = cut)
- `finalDem` — normalizedDem + blended cutFillDelta
- `materialMasks` — land cover, road surface, shoulder, slope, water
- `transform` — MapFrame projection info for round-trip

**Quantization for .ter:**
- Heightmap: 16-bit unsigned, quantized with explicit `zOffset` and `maxHeight`
- Layer map: 8-bit (max 254 materials, 255 = hole)
- Quantization error tracked: max/RMS reported in validation

**BeamNG TerrainBlock:**
- `terrainFile` → `.ter`
- `squareSize` = MapFrame extent / heightmap resolution
- `position` = MapFrame local origin (0,0,0)
- `maxHeight` = quantization maxHeight

## Alternatives
- Assume all DEMs are EGM96 → Rejected: Terrarium is ellipsoidal, others vary
- Force conversion to orthometric → Rejected: Geoid model adds dependency, error
- Use DEM directly as final terrain → Rejected: Roads would float/sink

## Consequences
- Explicit datum tracking throughout pipeline
- Geoid model needed for orthometric conversion (EGM2008 2.5' grid ~100MB)
- Road formation may create steep slopes at map boundary
- Quantization must not break road/terrain clearance

## Evidence
- Master prompt §6.2: "verticalDatum: { name: provider-native, normalization: recorded-not-assumed }"
- Master prompt §12: "Road-first terrain formation", "Finálna cesta je autoritatívna. Terén sa prispôsobuje navrhovanej ceste"

## Revisit Trigger
- If high-res geoid model becomes available as Python wheel
- If BeamNG adds geoid-aware terrain
- If vertical datum mismatch causes >1mology issues