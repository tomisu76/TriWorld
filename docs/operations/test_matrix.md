# Test Matrix

## Unit Tests (packages/*/tests/)

### contracts/
| Test | Description | Status |
|------|-------------|--------|
| test_map_frame_roundtrip | WGS84 → Local → WGS84 within tolerance | pending |
| test_utm_zone_selection | Correct UTM zone for various latitudes | pending |
| test_laea_fallback | LAEA used when crossing UTM zones | pending |
| test_terrarium_decode | Exact formula: R*256 + G + B/256 - 32768 | pending |
| test_osm_tag_parsing | highway, lanes, width, oneway, bridge, tunnel | pending |
| test_width_precedence | explicit > lane_sum > class_default > global | pending |
| test_lane_precedence | lanes > lanes:fwd/back > direction_tags > class | pending |
| test_oneway_minus1 | Geometry reversed when oneway=-1 | pending |
| test_stable_ids | Same input → same IDs regardless of order | pending |
| test_grade_separation | Bridge/tunnel no junction created | pending |

### compiler/spatial/
| Test | Description | Status |
|------|-------------|--------|
| test_dem_reproject | GDAL warp with explicit alignment | pending |
| test_nodata_handling | Nodata preserved through pipeline | pending |
| test_raster_orientation | Row 0 = North convention enforced | pending |

### compiler/topology/
| Test | Description | Status |
|------|-------------|--------|
| test_sumo_physical_fidelity | netconvert with physical-fidelity.netccfg | pending |
| test_sumo_traffic_enriched | netconvert with traffic-enriched.netccfg | pending |
| test_sumo_mapping | OSM way ↔ SUMO edge ↔ corridor mapping | pending |
| test_netcheck_integration | netcheck.py runs, parses output | pending |
| test_duarouter_integration | duarouter runs, produces routes | pending |
| test_headless_sim | sumo headless runs, no teleports | pending |

### compiler/civil/
| Test | Description | Status |
|------|-------------|--------|
| test_horizontal_clean | Dedup, resample, smooth, curvature | pending |
| test_vertical_qp | Constrained QP solves network grades | pending |
| test_junction_equality | Shared junction Z equal within 0.02m | pending |
| test_crossfall | 2% default, crown on 2-way | pending |
| test_superelevation | By design speed + radius, smooth transitions | pending |
| test_bridge_constraint | Bridge deck Z fixed, terrain preserved | pending |
| test_tunnel_exclusion | Tunnel corridors marked unsupported | pending |

### compiler/terrain/
| Test | Description | Status |
|------|-------------|--------|
| test_atomic_formation | Order-independent blend | pending |
| test_cut_fill_slopes | Max side slope respected | pending |
| test_bridge_mask | No formation under bridge | pending |
| test_water_mask | No formation in water | pending |
| test_penetration_metric | Road surface - terrain ≥ -epsilon | pending |
| test_unsupported_metric | No floating lanes > threshold | pending |

### compiler/mesh/
| Test | Description | Status |
|------|-------------|--------|
| test_dae_serializer | Valid Collada, stable XML, float format | pending |
| test_chunking | Seam < 0.002m, shared boundary vertices | pending |
| test_collision_mesh | Simplified, deviation < 0.02m | pending |
| test_lod_bounds | LOD bounds nested correctly | pending |

### beamng_target/
| Test | Description | Status |
|------|-------------|--------|
| test_ter_writer | Binary .ter matches golden file | pending |
| test_terrain_block | terrainFile, squareSize, position, maxHeight | pending |
| test_decalroad_width | halfWidth contract verified by canary | pending |
| test_tsstatic_refs | All DAE refs exist, materials bound | pending |
| test_spawn_transform | On road, oriented, orthogonal matrix | pending |
| test_zip_audit | Structure, hashes, no unsafe paths | pending |
| test_deterministic_zip | Two builds → identical SHA256 | pending |

## Property-Based Tests (Hypothesis)
| Property | Module | Status |
|----------|--------|--------|
| All output numbers finite | all | pending |
| Station monotonic | civil | pending |
| oneway=-1 twice = identity | topology | pending |
| Input permutation = same canonical IR | topology | pending |
| Local → Geo → Local in tolerance | spatial | pending |
| Mesh indices in bounds | mesh | pending |
| Normals ≈ unit length | mesh | pending |
| Formation only in influence mask | terrain | pending |
| No path crosses junction anchor | topology | pending |
| ZIP path never escapes root | packaging | pending |

## Synthetic Fixtures (fixtures/synthetic/)
| Fixture | Features | Expected Result |
|---------|----------|-----------------|
| straight_flat | 1 road, flat DEM | pass |
| s_curve | Horizontal curve | pass |
| steep_hill | Grade > target | conflict/warning |
| crest | Vertical curve | pass |
| sag | Vertical curve | pass |
| banked_curve | Superelevation | pass |
| t_junction | 3-way junction | pass |
| x_junction | 4-way junction | pass |
| skew_junction | Non-orthogonal | pass |
| oneway | One-way road | pass |
| oneway_minus1 | Reversed geometry | pass |
| roundabout | Ring + connections | pass |
| bridge_over_road | Layer separation | pass |
| tunnel_input | Tunnel tag | unsupported |
| duplicate_nodes | OSM duplicates | deduped |
| short_segment | < 1m segment | merged/warning |
| missing_width | No width tag | class default |
| boundary_clip | Road at edge | clipped |
| disconnected_roads | Two isolated roads | two components |
| shared_junction | Multiple roads, same junction | equal Z |

## Integration Tests
| Test | Description | Status |
|------|-------------|--------|
| test_osm_to_beamng | Real OSM bbox → full pipeline → ZIP | pending |
| test_dem_to_ter | Terrarium tiles → .ter → BeamNG load | pending |
| test_sumo_roundtrip | OSM → SUMO → mapping → CivilRoadIR | pending |
| test_zip_rebuild | Cached inputs → rebuild → same ZIP | pending |
| test_cancel_resume | Cancel mid-stage → resume from checkpoint | pending |

## UI Tests (Playwright)
| Test | Description | Status |
|------|-------------|--------|
| test_wizard_location | Click map, enter lat/lon | pending |
| test_wizard_size | Select preset, custom size | pending |
| test_generate_flow | Click Generate, watch stages | pending |
| test_cancel | Cancel mid-build | pending |
| test_retry | Retry from failed stage | pending |
| test_download_lock | Disabled until gates pass | pending |
| test_outage_flow | Provider offline → graceful error | pending |

## Runtime QA (Gate)
| Check | Pass Criteria | Status |
|-------|---------------|--------|
| Level listed | Appears in menu | pending |
| Level loaded | No load error | pending |
| Terrain visible | Not pink, not flat | pending |
| Materials OK | No missing texture warnings | pending |
| Daylight works | Sun position, shadows | pending |
| Spawn correct | On road, oriented, no fall | pending |
| Road collision | Continuous, no gaps | pending |
| No terrain penetration | Road - terrain ≥ -0.02m | pending |
| Main route drivable | 1km+ without incident | pending |
| Junction traversed | At least one | pending |
| Slope traversed | At least one | pending |
| AI route works | Query + follow (if declared) | pending |
| Save/reload stable | No changes | pending |
| Log clean | No critical errors | pending |

## Performance Budgets (per Quality Profile)
| Metric | Fast Preview | Drivable | High Quality | Studio |
|--------|--------------|----------|--------------|--------|
| Max RAM (GB) | 4 | 8 | 16 | 32 |
| Max terrain samples | 250k | 1M | 4M | 16M |
| Max road length (km) | 10 | 50 | 200 | 500 |
| Max triangles/chunk | 50k | 100k | 200k | 500k |
| Max collision tris | 25k | 50k | 100k | 200k |
| Max materials | 20 | 50 | 100 | 200 |
| Max textures | 30 | 80 | 200 | 500 |
| Max TSStatic | 100 | 500 | 2000 | 5000 |
| Max build time (min) | 2 | 10 | 30 | 60 |

## Determinism Test
| Scenario | Expected |
|----------|----------|
| Same request, cached inputs, clean workspace | Identical ZIP SHA256 |
| Same request, different run order (if parallel) | Identical ZIP SHA256 |
| Resume from checkpoint vs full run | Identical ZIP SHA256 |