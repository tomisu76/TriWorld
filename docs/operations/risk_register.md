# Risk Register

| ID | Risk | Probability | Impact | Severity | Owner | Mitigation | Test |
|----|------|-------------|--------|----------|-------|------------|------|
| R01 | OSM Overpass timeout / rate limit | High | High | Critical | Backend | Local cache + multi-endpoint retry with backoff + mirror rotation + buffered AOI | Fetch fixtures offline |
| R02 | DEM source unavailable / low resolution | Medium | High | High | Backend | Multi-source fallback (Terrarium → OpenTopography → user GeoTIFF) + resolution warning | Synthetic DEM fixtures |
| R03 | SUMO netconvert topology errors | Medium | High | High | Backend | Two profiles (physical-fidelity / traffic-enriched) + netcheck + duarouter + headless sim validation | SUMO integration tests |
| R04 | Grade-separated crossing becomes junction | Medium | High | High | Backend | SUMO layer/bridge/tunnel preservation + explicit validation rule | Fixture: bridge_over_road |
| R05 | Road Architect bake fails / unsupported | High | Medium | High | Backend | Version-pinned adapter + capability scanner + portable fallback always works | Canary per BeamNG version |
| R06 | DecalRoad width = full vs half | High | High | Critical | Backend | Canary test per BeamNG version: create road, measure, record conversion | BeamNG canary test |
| R07 | Terrain penetration / floating roads | Medium | High | High | Backend | Road-first formation + atomic blend + penetration/unsupported metrics + thresholds | Terrain fixtures + metrics |
| R08 | Non-deterministic ZIP output | Medium | High | High | Backend | Fixed timestamps, sorted entries, stable float format, hash verification | Determinism test |
| R09 | BeamNG version breaks level format | Medium | High | High | Backend | Pinned BeamNG version + canary test suite + runtime QA gate | Runtime QA |
| R10 | Licensing / redistribution violation | Low | Critical | Critical | Legal | SourceLicenseGate + asset registry + three flavors (portable/stock/studio) | License scan |
| R11 | GDAL/PROJ wheel incompatibility on Windows | Medium | High | High | DevOps | Prefer conda-forge/Pixi env if wheels fail; document chosen variant in ADR | Bootstrap test |
| R12 | Blender Collada export broken | Medium | Medium | Medium | Backend | Capability probe + own DAE serializer primary + Blender QA secondary | Blender QA |
| R13 | Large map OOM / disk full | Low | High | Medium | Backend | Per-profile budgets + disk quota + streaming/chunking | Performance budgets |
| R14 | User cancels mid-build, leaves corrupt state | Medium | Medium | Medium | Backend | Job queue with checkpoints + cooperative cancellation + workspace isolation | Cancel/resume test |
| R15 | Network request SSRF / path traversal | Low | Critical | High | Security | Allowlist domains, no shell=True, zip-slip protection, path containment | Security tests |
| R16 | AI DecalRoad doesn't match physical road | Medium | High | High | Backend | Single authoritative centerline per corridor + junction patches + validation | AI route test |
| R17 | Vertical datum mismatch (ellipsoidal vs orthometric) | Medium | High | High | Backend | Record native datum, never assume, geoid conversion optional + flagged | Terrain fixtures |
| R18 | SUMO version upgrade changes junction model | Low | High | Medium | Backend | Pinned SUMO version + netconvert output diff in nightly | Nightly SUMO test |
| R19 | BeamNG direct launch mechanism changes | Medium | Medium | Medium | Backend | Canary launch test + fallback to manual F11 flow | Launch canary |
| R20 | Asset pipeline quality gap vs Italy | Medium | Medium | Medium | Art | Asset registry + placement rules + LOD budgets + Blender QA | Visual inspection |

## Top 10 Technical Risks
1. **R06** DecalRoad width semantics (canary required per version)
2. **R01** OSM data acquisition reliability
3. **R03/R04** SUMO topology correctness
4. **R07** Terrain/road collision separation
5. **R08** Deterministic builds
6. **R09** BeamNG version compatibility
7. **R05** Road Architect dependency
8. **R11** Windows geospatial toolchain
9. **R17** Vertical datum handling
10. **R16** AI/physical road alignment