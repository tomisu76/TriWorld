# Primary sources and official search map

Kontrolný dátum tohto zoznamu: **2026-07-29**. Pred použitím zapíš aktuálny retrieval date, cieľovú verziu a pri Git zdroji commit SHA. Nepripínaj produkciu na `main`.

## 1. BeamNG.drive

### Level layout, serialization and gameplay

- [Level Creation](https://documentation.beamng.com/modding/levels/level_creation/)
- [Level creation overview and requirements](https://documentation.beamng.com/modding/levels/level_creation/section1/)
- [Level File Formats](https://documentation.beamng.com/modding/levels/level_formats/)
- [`items.level.json`](https://documentation.beamng.com/modding/levels/level_formats/items/)
- [`info.json`](https://documentation.beamng.com/modding/levels/level_formats/info/)
- [Gameplay data](https://documentation.beamng.com/modding/levels/gameplay_data/)
- [Navigation `map.json`](https://documentation.beamng.com/modding/levels/level_formats/map/)
- [Level Object Classes](https://documentation.beamng.com/modding/levels/level_classes/)

### Terrain, roads, collision and spawn

- [Terrain format (`.ter` and `.terrain.json`)](https://documentation.beamng.com/modding/levels/level_formats/terrain/)
- [TerrainBlock](https://documentation.beamng.com/modding/levels/level_classes/terrainblock/)
- [Terrain Editor](https://documentation.beamng.com/world_editor/tools/terrain_editor/)
- [Roads and drivable surfaces](https://documentation.beamng.com/modding/levels/level_creation/section3/)
- [DecalRoad](https://documentation.beamng.com/modding/levels/level_classes/decalorad/)
- [Decal Road Editor](https://documentation.beamng.com/world_editor/tools/decalroad_editor/)
- [MeshRoad](https://documentation.beamng.com/modding/levels/level_classes/meshroad/)
- [MeshRoad Editor](https://documentation.beamng.com/world_editor/tools/meshroad_editor/)
- [TSStatic](https://documentation.beamng.com/modding/levels/level_classes/tsstatic/)
- [SpawnSphere](https://documentation.beamng.com/modding/levels/level_classes/spawn/)

Pozor: aktuálna verejná DecalRoad dokumentácia môže pomenovať štvrtý node komponent `width`, kým staršie interné/generátorové kontrakty ho interpretujú ako `halfWidth`. TriWorld musí mať internú jednotku pomenovanú explicitne a versioned BeamNG serializer s canary testom. Nerieš tento rozpor premenovaním bez geometrického merania v presnej cieľovej verzii.

### Materials, assets and import

- [Materials JSON](https://documentation.beamng.com/modding/file_formats/materials/)
- [Level materials workflow](https://documentation.beamng.com/modding/levels/level_creation/section6/)
- [Blender → DAE asset pipeline](https://documentation.beamng.com/modding/levels/level_creation/section11/)
- [Shared `assets/` folder and `.link` migration](https://documentation.beamng.com/modding/levels/assets/)

### World Editor and Road Architect

- [World Editor overview](https://documentation.beamng.com/world_editor/overview/)
- [World Editor tools](https://documentation.beamng.com/world_editor/tools/)
- [Road Architect hub](https://documentation.beamng.com/world_editor/tools/road_architect/)
- [Road Architect introduction](https://documentation.beamng.com/world_editor/tools/road_architect/introduction/)
- [Road Architect getting started](https://documentation.beamng.com/world_editor/tools/road_architect/getting_started/)
- [Road Architect tool window](https://documentation.beamng.com/world_editor/tools/road_architect/tool_window_overview/)
- [Road Architect disk options](https://documentation.beamng.com/world_editor/tools/road_architect/disk_options/)
- [Road Architect troubleshooting](https://documentation.beamng.com/world_editor/tools/road_architect/troubleshooting/)

Road Architect je WIP a jeho session formát nie je runtime contract. Over Edit/Render režim, save/load, terrain association a presný spôsob bake v cieľovej verzii.

### Validation and packaging

- [Testing and validation](https://documentation.beamng.com/modding/levels/level_creation/section9/)
- [Packaging and publishing](https://documentation.beamng.com/modding/levels/level_creation/section10/)
- [Troubleshooting](https://documentation.beamng.com/modding/levels/level_creation/section12/)
- [BeamNG.drive v0.38.6 patch page](https://www.beamng.com/game/news/patch/beamng-drive-v0-38-6/)

Neinterpretuj „latest“ ako dlhodobý target. Cieľovú verziu zapíš do version locku a runtime reportu.

## 2. SUMO

- [SUMO documentation root](https://sumo.dlr.de/docs/)
- [SUMO Git repository](https://github.com/eclipse-sumo/sumo)
- [OSM Web Wizard](https://sumo.dlr.de/docs/Tutorials/OSMWebWizard.html)
- [Import from OpenStreetMap](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html)
- [`netconvert`](https://sumo.dlr.de/docs/netconvert.html)
- [Network elevation](https://sumo.dlr.de/docs/Networks/Elevation.html)
- [Netedit](https://sumo.dlr.de/docs/Netedit/index.html)
- [Network format](https://sumo.dlr.de/docs/Networks/SUMO_Road_Networks.html)
- [Network checking](https://sumo.dlr.de/docs/Tools/Net.html)
- [`osmBuild.py` source](https://github.com/eclipse-sumo/sumo/blob/main/tools/osmBuild.py)
- [`netcheck.py` source](https://github.com/eclipse-sumo/sumo/blob/main/tools/net/netcheck.py)
- [Shortest/optimal path routing](https://sumo.dlr.de/docs/Demand/Shortest_or_Optimal_Path_Routing.html)
- [`duarouter`](https://sumo.dlr.de/docs/duarouter.html)
- [`randomTrips.py`](https://sumo.dlr.de/docs/Tools/Trip.html)
- [TraCI](https://sumo.dlr.de/docs/TraCI.html)
- [sumolib](https://sumo.dlr.de/docs/Tools/Sumolib.html)

Pred implementáciou pinni SUMO release/tag a otvor source skriptu z rovnakého tagu, nie `main`.

## 3. OSM, attribution and service policies

- [OpenStreetMap copyright and licence](https://www.openstreetmap.org/copyright)
- [OSMF attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)
- [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/)
- [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)
- [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Overpass public instances](https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances)
- [Geofabrik downloads](https://download.geofabrik.de/)
- [OSM data model](https://wiki.openstreetmap.org/wiki/Elements)
- [OSM tagging index](https://wiki.openstreetmap.org/wiki/Map_features)

Verejné OSM služby nie sú backend pre produkčný bulk traffic. Implementuj cache, fair use, attribution, user-agent/contact a možnosť vlastného/provider endpointu.

## 4. GIS, CRS and raster processing

- [PROJ documentation](https://proj.org/en/stable/)
- [PROJ FAQ: axis order](https://proj.org/en/stable/faq.html)
- [pyproj Transformer](https://pyproj4.github.io/pyproj/stable/api/transformer.html)
- [GDAL documentation](https://gdal.org/en/stable/)
- [`gdalwarp`](https://gdal.org/en/stable/programs/gdalwarp.html)
- [`gdal_translate`](https://gdal.org/en/stable/programs/gdal_translate.html)
- [`gdaldem`](https://gdal.org/en/stable/programs/gdaldem.html)
- [`gdalinfo`](https://gdal.org/en/stable/programs/gdalinfo.html)
- [Rasterio](https://rasterio.readthedocs.io/en/stable/)
- [GeoPandas](https://geopandas.org/en/stable/)
- [Shapely](https://shapely.readthedocs.io/en/stable/)

Každá transformácia musí mať explicitný source CRS, target CRS, axis order, jednotky, origin, vertical datum/assumption a round-trip test.

## 5. Elevation data

- [OpenTopography developers/API](https://opentopography.org/developers)
- [Mapzen terrain tiles on AWS](https://registry.opendata.aws/terrain-tiles/)
- [Copernicus DEM on AWS](https://registry.opendata.aws/copernicus-dem/)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)

Pred stiahnutím over pokrytie, rozlíšenie, vertikálny datum, nodata, licenciu/terms, rate limits a redistribučné podmienky. DEM nie je automaticky povrch vozovky.

## 6. Civil road geometry and interchange

- [ASAM OpenDRIVE specification](https://www.asam.net/standards/detail/opendrive/)
- [OpenDRIVE elevation and superelevation model 1.8](https://publications.pages.asam.net/standards/ASAM_OpenDRIVE/ASAM_OpenDRIVE_Specification/1.8.0/specification/10_roads/10_05_elevation.html)
- [OGC GeoPackage standard](https://www.geopackage.org/spec/)
- [OGC Simple Features](https://www.ogc.org/standard/sfa/)

ASAM OpenDRIVE je matematická/reference inšpirácia a možný interchange, nie automaticky BeamNG Road Architect import contract. V BeamNG.drive môžu byť niektoré OpenDRIVE tlačidlá alebo workflow obmedzené na BeamNG.tech.

## 7. Blender and asset generation

- [Blender manual](https://docs.blender.org/manual/en/latest/)
- [Blender 4.5 import/export](https://docs.blender.org/manual/en/4.5/files/import_export/index.html)
- [Blender Python API](https://docs.blender.org/api/current/)
- [Blender command-line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)
- [Hermes Blender skill pinned example](https://github.com/NousResearch/hermes-agent/blob/v2026.7.20/optional-skills/creative/blender-mcp/SKILL.md)
- [Hermes Blender MCP manifest pinned example](https://github.com/NousResearch/hermes-agent/blob/v2026.7.20/optional-mcps/blender/manifest.yaml)
- [Blender MCP](https://github.com/ahujasid/blender-mcp)

Pre produkčný build preferuj deterministický headless Python/CLI export. Interaktívny MCP používaj na objavovanie a authoring, nie ako jedinú reprodukovateľnú cestu.

## 8. Hermes Agent

- [Hermes Agent repository](https://github.com/NousResearch/hermes-agent)
- [Hermes Web Search & Extract](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search/)
- [Hermes delegation guide](https://hermes-agent.nousresearch.com/docs/guides/delegation-patterns/)
- [Hermes delegation reference](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation)
- [Hermes configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration/)
- [Hermes persistent memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/)
- [Hermes optional skills catalog](https://hermes-agent.nousresearch.com/docs/reference/optional-skills-catalog/)

Konkrétny Hermes setup over proti nainštalovanému release/tagu. `web_extract` môže dlhé stránky sumarizovať; presné tvrdenia kontroluj v raw zdroji alebo browser snapshote.

## 9. NotebookLM

- [Learn about NotebookLM](https://support.google.com/notebooklm/answer/16164461?hl=en)
- [Add/discover sources](https://support.google.com/notebooklm/answer/16215270?hl=en)
- [Use NotebookLM chat and citations](https://support.google.com/notebooklm/answer/16179559?hl=en)
- [Create, manage and share notebooks](https://support.google.com/notebooklm/answer/16206563?hl=en)
- [NotebookLM FAQ and current limits](https://support.google.com/notebooklm/answer/16269187?hl=en)
- [Gemini Notebook Enterprise notebook API](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)
- [Gemini Notebook Enterprise sources API](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources)

Konzumný NotebookLM nemá v tomto balíku predpokladané stabilné verejné API. Enterprise API je Preview/Pre-GA `v1alpha`, vyžaduje projekt, licenciu a IAM a nesmie byť core dependency.

## 10. Useful reference implementations — not authorities

- [OSM2World RoadModule](https://github.com/tordanik/OSM2World/blob/master/core/src/main/java/org/osm2world/world/modules/RoadModule.java)
- [QGIS](https://github.com/qgis/QGIS)
- [OSMnx](https://github.com/gboeing/osmnx)

Použi ich na objavenie algoritmov a edge cases. Skontroluj licenciu a nekopíruj kód iba preto, že je verejne čitateľný.

## 11. Local read-only archaeology

Ak tieto cesty existujú, môžu ukázať skoršie experimenty. Nie sú autoritou a nič z nich nekopíruj bez testu a licenčnej kontroly:

- `C:\GeoCrashSim\GeoCrashSim-BeamNG\apps\geocrash_bridge\services\adapters\osm_road_ir_adapter.py`
- `C:\GeoCrashSim\GeoCrashSim-BeamNG\apps\geocrash_bridge\services\spatial\map_frame.py`
- `C:\GeoCrashSim\GeoCrashSim-BeamNG\apps\geocrash_bridge\adapters\road_ir_to_native_roads.py`
- `C:\GeoCrashSim\GeoCrashSim-BeamNG\apps\geocrash_bridge\services\beamng_world_backend.py`
- `C:\GeoCrashSim\GeoCrashSim-BeamNG\geocrash\beamng\native_roads.py`
- `C:\GeoCrashSim\GeoCrashSim-BeamNG\geocrash\beamng\validation.py`
- `C:\GeoCrashSim\GeoCrashSim-BeamNG\geocrash\beamng\visual_diagnostic.py`
- `C:\GeoCrashSim\mapng\services\exportBeamNGLevel.js`
- `C:\GeoCrashSim\mapng\components\panels\ExportPanel.vue`

Známu historickú neistotu zachovaj: generovaný DecalRoad/AI alebo Road Architect session ešte neznamená overený viditeľný, fyzický a po reload jazditeľný runtime level.
