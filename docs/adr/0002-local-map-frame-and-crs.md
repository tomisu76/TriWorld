# ADR 0002: Local Map Frame and CRS

**Status:** Accepted
**Date:** 2026-07-29

## Context
TriWorld must handle geospatial data in WGS84 (EPSG:4326) and project it to a local metric coordinate system for engineering calculations and BeamNG export. The choice of projection, anchor point, and coordinate conventions affects all downstream stages.

## Decision
1. **Input CRS:** Always WGS84 (EPSG:4326), coordinates as [longitude, latitude] per GeoJSON and pyproj convention
2. **Projection:** UTM zone matching the map center for areas within a single UTM zone. For cross-zone or polar areas, use Local Azimuthal Equidistant (LAEA) centered on the map anchor.
3. **MapFrame Anchor:** User-selected center point (lat, lon) → projected to (0, 0) in local ENU frame
4. **Local Frame Convention:** 
   - X = East, Y = North, Z = Up
   - Units: metres
   - Right-handed coordinate system
5. **Transform Pipeline:** WGS84 → Projected (UTM/LAEA) → Local (anchor at 0,0)
6. **pyproj Usage:** `Transformer.from_crs(source, target, always_xy=True)` for all transformations
7. **Vertical Datum:** Record provider-native datum (ellipsoidal vs orthometric). Do not silently convert. Normalize to ellipsoidal for internal calculations, record offset to orthometric if known.
8. **Raster Convention:** Row 0 = North, pixel = area (not point)
9. **Provenance:** Store WKT2, PROJ pipeline string, PROJ version in every MapFrame

## Alternatives
- Use Web Mercator (EPSG:3857) globally → Rejected: Distortion too high for engineering
- Use local tangent plane (ENU) directly from WGS84 → Rejected: No standard CRS code, harder to exchange with GIS tools
- Use UTM always → Rejected: Fails at zone boundaries and polar regions

## Consequences
- All spatial data flows through MapFrame
- Round-trip tests mandatory (WGS84 → Local → WGS84)
- Distortion budget per quality profile
- Explicit handling of vertical datum prevents silent elevation errors

## Evidence
- Master prompt §6.2: MapFrame specification with CRS, anchor, axis convention
- PROJ FAQ: Axis order handling (always_xy=True)
- pyproj Transformer documentation

## Revisit Trigger
- If map extent exceeds UTM zone width
- If vertical datum conversion becomes necessary
- If PROJ version upgrade changes behavior