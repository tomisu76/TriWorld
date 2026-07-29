# Search query cookbook

Tieto dotazy sú štartovacie šablóny. Doplň cieľovú verziu, operačný systém, presný symbol a rok. Preferuj domain filter na oficiálny zdroj. Po nájdení výsledku otvor plnú stránku/source a zapíš commit alebo retrieval date.

## BeamNG level format

```text
site:documentation.beamng.com/modding/levels/level_formats items.level.json SimGroup line delimited
site:documentation.beamng.com/modding/levels/level_formats info.json defaultSpawnPointName spawnPoints
site:documentation.beamng.com/modding/levels/gameplay_data navgraph traffic POI
site:documentation.beamng.com/modding/levels/level_classes terrainblock terrainFile squareSize
site:documentation.beamng.com/modding/levels/level_formats terrain .ter version materials
site:documentation.beamng.com/modding/file_formats materials.json mapTo persistentId
site:documentation.beamng.com/modding/levels/assets ".link" shared assets migration
site:documentation.beamng.com/modding/levels/level_creation packaging zip root levels
site:documentation.beamng.com/modding/levels/level_creation testing fresh profile cache
```

## BeamNG roads, AI and World Editor

```text
site:documentation.beamng.com DecalRoad nodes width drivability oneWay flipDirection
site:documentation.beamng.com MeshRoad nodes width depth normal collision
site:documentation.beamng.com map.json drivability oneWay lanesLeft lanesRight
site:documentation.beamng.com World Editor launch level command line
site:documentation.beamng.com/world_editor/tools/road_architect Render Mode save load session terrain
site:documentation.beamng.com/world_editor/tools/road_architect OpenDRIVE BeamNG.tech
site:documentation.beamng.com/world_editor/tools/road_architect troubleshooting folding missing triangles
site:beamng.com/game/news/patch BeamNG 0.38.6
```

V lokálnom source presnej inštalácie hľadaj podľa reálnych názvov objektov a UI textu:

```text
RoadArchitect
road architect
DecalRoad
MeshRoad
items.level.json
saveLevel
loadLevel
Render Mode
session
```

Nezovšeobecňuj nájdený symbol na verejné API bez canary.

## SUMO OSM import

```text
site:sumo.dlr.de/docs/Networks/Import/OpenStreetMap netconvert OSM typemap turn lanes
site:sumo.dlr.de/docs/netconvert junctions.join ramps.guess geometry.remove
site:sumo.dlr.de/docs/Networks/Elevation heightmap.geotiff osm.elevation
site:sumo.dlr.de/docs/Networks/SUMO_Road_Networks internal edges connections lane index
site:github.com/eclipse-sumo/sumo osmBuild.py tag
site:github.com/eclipse-sumo/sumo netcheck.py tag vclass source destination
site:sumo.dlr.de/docs/Tools/Net.html netcheck component-output results-output
site:sumo.dlr.de/docs/duarouter no connection ignore errors repair
site:sumo.dlr.de/docs/Tools/Trip.html randomTrips validate
site:sumo.dlr.de/docs/sumo.html error-log no-step-log headless
```

## SUMO geometry and coordinates

```text
site:sumo.dlr.de/docs/Geo-Coordinates.html netOffset projParameter convBoundary origBoundary
site:sumo.dlr.de/docs/Tools/Sumolib.html convertLonLat2XY convertXY2LonLat withInternal
site:sumo.dlr.de/docs lane index rightmost internal edge connections
site:sumo.dlr.de/docs fromLonLat mapmatch.distance duarouter
```

## OSM schema and licensing

```text
site:wiki.openstreetmap.org highway lanes oneway bridge tunnel layer turn:lanes
site:wiki.openstreetmap.org highway width maxspeed surface smoothness lit sidewalk
site:wiki.openstreetmap.org junction roundabout motorway_link destination
site:osmfoundation.org Attribution Guidelines simulation routing engine
site:operations.osmfoundation.org/policies tiles bulk download caching user agent
site:operations.osmfoundation.org/policies nominatim one request per second autocomplete
site:openstreetmap.org/copyright ODbL derivative database attribution
```

Community tagging wiki vysvetľuje použitie tagov, ale aktuálne dáta vždy parsuj defensívne; tag môže chýbať, byť neplatný alebo regionálne odlišný.

## PROJ and CRS

```text
site:proj.org axis ordering EPSG:4326 longitude latitude
site:proj.org projinfo area of use accuracy grid
site:pyproj4.github.io Transformer always_xy allow_ballpark only_best
site:pyproj4.github.io CRS axis_info area_of_use
site:gdal.org gdalwarp te_srs tap nodata vertical shift
site:gdal.org gdalinfo json statistics checksum
site:gdal.org gdaldem slope hillshade
```

## DEM and vertical datum

```text
site:opentopography.org/developers API limits commercial enterprise key DEM
site:dataspace.copernicus.eu Copernicus DEM GLO-30 license EGM2008
site:earthdata.nasa.gov NASADEM SRTM EGM96 data use
site:usgs.gov 3DEP bare earth DEM vertical datum
site:eorc.jaxa.jp AW3D30 terms EGM96
site:registry.opendata.aws terrain tiles Mapzen license
site:registry.opendata.aws copernicus-dem
```

Vždy hľadaj aj:

```text
<dataset> horizontal CRS
<dataset> vertical datum
<dataset> nodata
<dataset> resolution
<dataset> redistribution commercial use attribution
<provider> rate limits terms of service
```

## Civil geometry

```text
site:asam.net OpenDRIVE superelevation crossfall lane width spiral
site:publications.pages.asam.net/standards/ASAM_OpenDRIVE 1.8 elevation superelevation
site:fhwa.dot.gov road design superelevation transition stopping sight distance
site:dot.state.* highway design manual vertical curve grade drainage
```

Regulačné/civilné limity sú jurisdiction-specific. Neaplikuj americký alebo iný manuál globálne bez regionálneho profilu. Interný generator môže mať konzervatívne engineering defaults, ale musí ich označiť ako profil, nie univerzálny zákon.

## Blender and assets

```text
site:docs.blender.org/manual/en/4.5 files import export DAE collada
site:docs.blender.org/api/current bpy export scene deterministic
site:docs.blender.org/manual command line background python exit code
site:github.com/NousResearch/hermes-agent blender-mcp SKILL.md manifest.yaml
site:github.com/ahujasid/blender-mcp release security permissions
site:documentation.beamng.com Blender DAE collision materials LOD
```

## Hermes Agent

```text
site:hermes-agent.nousresearch.com/docs web search extract backend trust model
site:hermes-agent.nousresearch.com/docs delegation patterns max concurrent children depth
site:hermes-agent.nousresearch.com/docs configuration checkpoints project context .hermes.md
site:hermes-agent.nousresearch.com/docs memory write approval session search
site:github.com/NousResearch/hermes-agent releases delegation web_search web_extract
```

## NotebookLM

```text
site:support.google.com/notebooklm add sources limits citations notebook independent
site:support.google.com/notebooklm share Chat View sources artifacts permissions
site:support.google.com/notebooklm reports export Docs Sheets citations
site:docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise v1alpha API sources Preview
```

## GitHub source archaeology

```text
repo:eclipse-sumo/sumo path:tools/net netcheck.py
repo:eclipse-sumo/sumo path:tools osmBuild.py
repo:NousResearch/hermes-agent path:website/docs delegation
repo:NousResearch/hermes-agent path:website/docs web-search
repo:tordanik/OSM2World path:core RoadModule
```

Pri každom Git výsledku:

1. otvor file history;
2. vyber tag zodpovedajúci target version;
3. zapíš SHA;
4. skontroluj licenciu;
5. prečítaj tests/callers, nie iba jednu funkciu.

## Failure-oriented queries

Najlepšie dotazy často hľadajú hranice, nie happy path:

```text
<tool/version> known issues migration breaking change
<format> parser rejects unsupported version
<field> ignored after reload
<workflow> save reload missing collision
<asset> missing material mapTo
<SUMO option> warning no connection internal edge
<CRS> axis swapped wrong hemisphere
<DEM> vertical datum offset nodata seam
<BeamNG level> works unpacked fails zip clean profile
```

## Query log

Ku každému sprintu zaznamenaj:

```text
Timestamp:
Research question:
Queries used:
Domains searched:
Results opened:
Rejected sources and reason:
Accepted evidence IDs:
Remaining uncertainty:
```

