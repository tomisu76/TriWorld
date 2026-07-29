# ADR 0007: Deterministic Builds and Provenance

**Status:** Accepted
**Date:** 2026-07-29

## Context
TriWorld must produce byte-identical ZIPs from identical inputs for reproducibility, caching, and auditing.

## Decision
**Build Identity:**
```
buildId = SHA256(canonical_request_json + input_hashes + tool_versions + config_hash)
```

**Canonical Request:** Sorted keys, no whitespace, fixed float formatting (e.g., `.6f`)

**Input Hashes:** SHA256 of every source file (OSM, DEM, config, assets)

**Tool Versions:** Exact versions of Python, SUMO, GDAL, PROJ, Blender, BeamNG

**Config Hash:** Hash of quality profile, road classes, provider configs

**Deterministic ZIP:**
- Entries sorted lexicographically by path (UTF-8)
- Path separators normalized to `/`
- No absolute paths, no `..`, no drive letters, no symlinks
- Timestamps fixed to `1980-01-01 00:00:00` (DOS epoch)
- Permissions: 0o644 files, 0o755 dirs
- Compression: DEFLATE level 6, fixed window bits
- No extra fields, no ZIP64 unless required

**Provenance Manifest (`reports/build-manifest.json`):**
```json
{
  "buildId": "sha256...",
  "compilerVersion": "git-commit-sha",
  "requestHash": "sha256...",
  "inputHashes": {"osm": "...", "dem": "...", "config": "..."},
  "toolVersions": {"python": "3.12.8", "sumo": "1.27.1", "gdal": "3.8.0", "proj": "9.3.0", "beamng": "0.38.6.0.19963"},
  "sourceLicenses": [...],
  "projection": {"crs": "EPSG:32634", "wkt2": "...", "projPipeline": "...", "projVersion": "9.3.0"},
  "sumoCommand": ["netconvert", "-c", "physical-fidelity.netccfg"],
  "seed": 184467,
  "files": [{"path": "levels/xyz/info.json", "sha256": "...", "bytes": 1234}],
  "validationReport": "reports/validation.json"
}
```

**Reproducibility Test:**
```bash
triworld build request.json -o buildA.zip
triworld build request.json -o buildB.zip
sha256sum buildA.zip buildB.zip  # Must be identical
```

## Alternatives
- Use existing reproducible-build tools → Rejected: Prefer explicit control

## Consequences
- Byte-identical rebuilds enable caching, signing, auditing
- Fixed timestamps may confuse some tools (acceptable)

## Evidence
- Master prompt §21: "ZIP builder: zoradí paths lexikograficky..."

## Revisit Trigger
- If ZIP tooling changes
- If new source of non-determinism discovered