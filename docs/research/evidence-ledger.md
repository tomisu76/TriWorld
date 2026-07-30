# Evidence Ledger

> **PARTIAL HISTORICAL LEDGER.** Entries are valid only for their recorded date,
> source, version, and canary. This file does not override
> `docs/CURRENT_HANDOFF.md` or newer preserved runtime evidence.

## Format
| Claim | Source | Version/Commit | Date Accessed | Evidence Snippet | Confidence | Canary/Test |
|-------|--------|----------------|---------------|------------------|------------|-------------|

## Toolchain Versions
| Tool | Claimed Version | Verified Version | Source |
|------|-----------------|------------------|--------|
| Python | 3.11.11 | 3.11.11 | `python --version` |
| pip | 26.0.1 | 26.0.1 | `pip --version` |
| Node | 24.13.1 | 24.13.1 | `node --version` |
| npm | 11.10.1 | 11.10.1 | `npm --version` |
| SUMO | 1.27.1 | 1.27.1 | `sumo --version` |
| netconvert | 1.27.1 | 1.27.1 | `netconvert --version` |
| BeamNG | 0.38.6.0.19963 | 0.38.6.0.19963 | Local install |
| Blender | Not installed | N/A | `blender --version` failed |
| GDAL | Not installed | N/A | `gdalinfo --version` failed |
| PROJ | Not installed | N/A | `projinfo --version` failed |

## BeamNG Documentation
| Claim | URL | Section | Date Accessed |
|-------|-----|---------|---------------|
| Level creation workflow | https://documentation.beamng.com/modding/levels/level_creation/ | All | 2026-07-29 |
| Level formats (items.level.json) | https://documentation.beamng.com/modding/levels/level_formats/items/ | All | 2026-07-29 |
| Terrain format (.ter) | https://documentation.beamng.com/modding/levels/level_formats/terrain/ | All | 2026-07-29 |
| info.json format | https://documentation.beamng.com/modding/levels/level_formats/info/ | All | 2026-07-29 |
| DecalRoad class | https://documentation.beamng.com/modding/levels/level_classes/decalroad/ | All | 2026-07-29 |
| MeshRoad class | https://documentation.beamng.com/modding/levels/level_classes/meshroad/ | All | 2026-07-29 |
| TSStatic class | https://documentation.beamng.com/modding/levels/level_classes/tsstatic/ | All | 2026-07-29 |
| Materials | https://documentation.beamng.com/modding/file_formats/materials/ | All | 2026-07-29 |
| Road Architect | https://documentation.beamng.com/world_editor/tools/road_architect/ | All | 2026-07-29 |

## SUMO Documentation
| Claim | URL | Section | Date Accessed |
|-------|-----|---------|---------------|
| OSM Import | https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html | All | 2026-07-29 |
| netconvert | https://sumo.dlr.de/docs/netconvert.html | All | 2026-07-29 |
| netcheck.py | https://github.com/eclipse-sumo/sumo/blob/main/tools/net/netcheck.py | All | 2026-07-29 |
| duarouter | https://sumo.dlr.de/docs/Demand/Shortest_or_Optimal_Path_Routing.html | All | 2026-07-29 |

## GIS & Data
| Claim | URL | Section | Date Accessed |
|-------|-----|---------|---------------|
| PROJ axis order | https://proj.org/en/stable/faq.html | Axis order | 2026-07-29 |
| pyproj Transformer | https://pyproj4.github.io/pyproj/stable/api/transformer.html | always_xy=True | 2026-07-29 |
| GDAL warp | https://gdal.org/en/stable/programs/gdalwarp.html | All | 2026-07-29 |
| OSM Attribution | https://osmfoundation.org/wiki/Licence/Attribution_Guidelines | All | 2026-07-29 |
| OSM Tile Policy | https://operations.osmfoundation.org/policies/tiles/ | All | 2026-07-29 |
| Nominatim Policy | https://operations.osmfoundation.org/policies/nominatim/ | All | 2026-07-29 |

## Hermes & Blender
| Claim | URL | Section | Date Accessed |
|-------|-----|---------|---------------|
| Hermes web search | https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search/ | All | 2026-07-29 |
| Hermes delegation | https://hermes-agent.nousresearch.com/docs/guides/delegation-patterns/ | All | 2026-07-29 |
| Blender MCP skill | https://github.com/NousResearch/hermes-agent/blob/v2026.7.20/optional-skills/creative/blender-mcp/SKILL.md | All | 2026-07-29 |
| Blender MCP manifest | https://github.com/NousResearch/hermes-agent/blob/v2026.7.20/optional-mcps/blender/manifest.yaml | All | 2026-07-29 |
| Blender 4.5 I/O | https://docs.blender.org/manual/en/4.5/files/import_export/index.html | Collada | 2026-07-29 |

## NotebookLM
| Claim | URL | Section | Date Accessed |
|-------|-----|---------|---------------|
| NotebookLM overview | https://support.google.com/notebooklm/answer/16164461 | All | 2026-07-29 |
| Sources and limits | https://support.google.com/notebooklm/answer/16215270 | All | 2026-07-29 |
| Enterprise API | https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks | All | 2026-07-29 |

## Open Questions / Not Yet Proven
| Claim | Status | Blocker | Next Action |
|-------|--------|---------|-------------|
| BeamNG .ter binary format exact spec | not yet proven | Need source/canary test | Write .ter reader/writer canary |
| BeamNG items.level.json exact schema | not yet proven | Need source/canary test | Parse Italy level |
| DecalRoad width = full vs half | not yet proven | Need canary test | Create test road, measure |
| SUMO netOffset sign convention | not yet proven | Need round-trip fixture | Write SUMO XY → WGS84 test |
| GDAL Terrarium decode formula | not yet proven | Need to verify | Write decode test |
| Blender Collada export compatibility | not yet proven | Blender not installed | Install Blender 4.5 LTS, test |
| Road Architect session format | not yet proven | Need BeamNG + RA | Scan installed Lua modules |
| Deterministic ZIP byte-for-byte | not yet proven | Need full pipeline | Phase 11 gate |
