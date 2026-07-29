# Environment Report

**Generated:** 2026-07-29T21:55:00Z
**Repository:** C:\TriWorld
**Branch:** audit-and-evidence
**Commit:** (uncommitted changes)

## Operating System
- **OS:** Microsoft Windows 10 22H2 (v10.0) (build 19045), 64-bit
- **Architecture:** AMD64

## Toolchain Detection

### Python
- **Version:** 3.11.11 (primary), 3.12.8 (available via uv)
- **pip:** 26.0.1 (from Python 3.12)
- **uv:** Not detected in PATH

### Node.js
- **Version:** 24.13.1
- **npm:** 11.10.1
- **corepack:** Available

### SUMO
- **Version:** 1.27.1
- **Build:** Windows-10.0.26100 AMD64 MSVC 19.51.36247.0 Release
- **Features:** FMI Proj GUI FMT Intl SWIG Parquet Eigen GDAL FFmpeg OSG GL2PS JuPedSim
- **SUMO_HOME:** Not set in environment

### BeamNG.drive
- **Version:** 0.38.6.0 (build 19963)
- **Install Root:** C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive
- **User Root:** C:\Users\tomisu\AppData\Local\BeamNG\BeamNG.drive\current\
- **Italy Map:** Present at content/levels/italy.zip (verified by directory listing)

### Blender
- **Version:** Not installed / not in PATH
- **Collada Support:** Unknown

### GDAL/PROJ
- **GDAL:** Not installed
- **PROJ:** Not installed

### Disk Space
- **C: Drive:** Need to check available space

### Memory & CPU
- **RAM:** Need to query
- **Logical CPUs:** Need to query

## Capability Summary
| Tool | Status | Version | Notes |
|------|--------|---------|-------|
| Python | ✅ | 3.11.11 / 3.12.8 | Primary / uv |
| Node.js | ✅ | 24.13.1 | |
| SUMO | ✅ | 1.27.1 | netconvert available |
| BeamNG | ✅ | 0.38.6.0 (19963) | Italy map present |
| Blender | ❌ | — | Not installed |
| GDAL | ❌ | — | Not installed |
| PROJ | ❌ | — | Not installed |

## Blockers for Phase 0
1. **Blender not installed** — Required for Blender QA (Phase 10) and asset authoring
2. **GDAL/PROJ not installed** — Required for DEM processing and CRS transforms
3. **SUMO_HOME not set** — Should be configured for reliable subprocess calls
4. **Python environment** — Need to pin 3.12 and create uv lockfile

## Next Actions
1. Install Blender 4.5 LTS (or latest stable with Collada support)
2. Install GDAL/PROJ via conda-forge or OSGeo4W
3. Set SUMO_HOME environment variable
4. Run `uv python pin 3.12` and `uv sync --all-groups`
5. Run bootstrap.ps1 to validate full toolchain