# Hermes execution hints for TriWorld

Toto sú praktické návrhy a známe pasce. Master prompt a contracts majú vyššiu autoritu.

## 1. Začni úzkym vertical slice

Prvý dôkaz nemá používať internet, OSM, DEM, Blender ani Road Architect. Vytvor malú syntetickú mapu:

- deterministický flat terrain;
- jedna rovná, jedna zakrivená road;
- jeden jednoduchý junction;
- vlastné redistribuovateľné materiály;
- fyzická collision;
- jedna autoritatívna AI road;
- bezpečný spawn;
- validné metadata;
- deterministic ZIP.

Tento slice musí prejsť static gate aj skutočný BeamNG load-and-drive gate. Až potom nahraď synthetic inputs skutočnými dátami.

Výhoda: ak mapa nefunguje, problém je BeamNG target/packaging, nie OSM/CRS/DEM/SUMO chaos.

## 2. Udrž jeden kanonický intermediate model

Nedovoľ, aby UI, SUMO adapter, Blender a BeamNG serializer mali vlastnú definíciu cesty.

Odporúčaná vrstvenosť:

```text
SourceObservation
  -> MapFrame
  -> RoadTopologyIR
  -> RoadCivilIR
  -> RoadSurfaceIR
  -> BeamNG target artifacts
  -> QA evidence
```

Každý IR má:

- `schemaVersion`;
- jednotky;
- coordinate frame;
- stable IDs;
- source provenance;
- confidence/assumption fields;
- deterministic ordering;
- JSON Schema/Pydantic or equivalent;
- migration policy;
- golden fixtures.

SUMO je topology/traffic compiler a oracle. Nie je zdroj finálnej 3D surface. Blender je geometry tool. Nie je source of truth. BeamNG runtime je posledný target gate.

## 3. Road layers nesplývajú

Pre každý logical road corridor drž:

1. topológiu — directed edges, lanes, connections, restrictions;
2. civil geometry — centerline, stationing, profile, crossfall, widths;
3. physical surface — mesh + collision + terrain formation;
4. visual surface — materials, decals, markings, wear;
5. AI navigation — jedna autoritatívna drivable layer;
6. provenance/QA — source IDs, warnings, measured errors.

Najčastejší omyl je viditeľný DecalRoad bez collision alebo MeshRoad/mesh bez správnej AI navigácie.

## 4. DecalRoad width konflikt uzavri canary testom

TriWorld historical/internal contract používa `[x, y, z, halfWidth]`. Aktuálna verejná BeamNG class dokumentácia môže štvrtý scalar pomenovať `width`. Nerob tichú zmenu.

Odporúčanie:

- v RoadIR používaj jednoznačné `half_width_m`;
- BeamNG adapter má explicitnú conversion funkciu pre target build;
- vytvor editorom dve road šírky merané v world units;
- save, inspect `items.level.json`, reload a znovu zmeraj;
- pridaj golden fixture a version gate;
- kým test neprejde, serializer je `not yet proven`.

Takto sa interná geometria nemení podľa nejasného externého názvu.

## 5. Scene layout a terrain

- Moderný target typicky používa `levels/<slug>/main/` scene tree a `levels/<slug>/info.json`; exact starter level cieľovej verzie je najlepší golden.
- `items.level.json` môže byť line-oriented objects, nie JSON array.
- `.terrain.json` nie je náhrada binary `.ter`.
- Direct `.ter` writer je rizikový a versioned; začni editor-saved golden alebo engine-authoritative bake.
- Terrain world size, sample resolution, square size, origin a material map musia byť jeden contract.
- Decals/projected roads môžu mať iné behavior na TSStatic než na TerrainBlock; fyzický mesh a visual overlay testuj oddelene.

## 6. Junctions sú samostatný problém

Neoffsetuj iba centerline a neočakávaj dobrú križovatku.

Potrebuješ:

- topology node/connection model;
- trimmed approaches;
- shared junction polygon/surface;
- lane connector curves;
- height/normal blending;
- UV/material continuity;
- collision continuity;
- AI connector graph;
- markings/yields/signals;
- negative test na bridge/tunnel false junction.

Junction triangulation musí byť deterministická a testovať holes/self-intersections.

## 7. Civil profile pred scenery

Italy-like kvalita začína jazdou:

- rozumné horizontálne curvature;
- grade a vertical curves;
- smooth superelevation/crossfall transitions;
- lane/shoulder/curb consistency;
- terrain cut/fill;
- mosty, tunely, retaining walls;
- drainage cues;
- continuous collision;
- čitateľné junctions.

Stovky budov nezachránia cestu s prudkým roll flipom alebo falošným junctionom.

## 8. „Italy assets“ používaj iba legálne

Italy je vhodná ako:

- benchmark kategórií a density;
- runtime reference na používateľovej lokálnej inštalácii;
- zdroj meraní a vizuálnych observations, ak to EULA dovoľuje;
- dependency počas lokálneho QA, ak sa asset referencuje zákonným spôsobom a target install ho obsahuje.

Italy nie je vhodná ako:

- asset pack na extrakciu a priloženie do TriWorld ZIP;
- source textúr/mesh/materialov na redistribúciu;
- cesta, na ktorú sa hardcoduje generátor bez version/dependency checku.

Bezpečný model:

- vlastné alebo explicitne redistribuovateľné assets;
- procedural/CC0 knižnica s manifestom;
- voliteľný `stock-dependency` adapter, ktorý nič nekopíruje a pri chýbajúcej kompatibilnej inštalácii failne alebo použije vlastný fallback;
- každý external material/path má capability check a target-version test;
- credits/attribution sú generované z manifestu.

Systémové kategórie, ktoré možno napodobniť bez kopírovania:

- regionálne biome palettes;
- hierarchy roads/settlements/landmarks;
- material variation;
- LOD/instancing;
- ambient sound zones;
- signage/road furniture rules;
- art-direction presets;
- density/performance budgets;
- vista composition.

## 9. Road Architect je bake authority, nie základná závislosť

Udrž dve cesty:

### Portable fallback

TriWorld priamo vytvorí runtime-compatible terrain, physical roads, visuals, AI a metadata bez editora. Toto je CI/offline baseline.

### Enhanced Road Architect bake

Versioned adapter:

```text
capability scan
-> session/profile generation
-> target map load
-> Road Architect session load
-> junction finalize
-> Render Mode
-> save
-> full reload
-> persistence/collision/AI check
-> package persisted artifacts
```

Ak chýba symbol alebo handshake marker, enhanced mode failne closed a nepoškodí portable fallback.

## 10. World Editor opening

Nesľubuj priamy launch bez versioned canary. Príkazový parser, user path a level-load behavior sa môžu meniť.

Implementuj:

- detector exact executable/build;
- detector user path/mod location;
- ZIP hash check;
- version adapter;
- process/log tracker;
- bounded level-load timeout;
- manual fallback instructions.

Manuálny fallback:

```text
Start BeamNG normally -> choose TriWorld level -> wait for spawn -> F11
-> open Road Architect -> edit/render -> save -> close/reload -> verify.
```

Process started ≠ map loaded. Editor open ≠ road baked. Save called ≠ persisted after reload.

## 11. SUMO tips

- Pin SUMO and use its bundled docs/source.
- `netconvert` heuristics are candidates, nie ground truth.
- Custom typemap môže vypnúť default typemap, ak ich neuvedieš spolu.
- `--junctions.join` vie opraviť aj pokaziť topology.
- Internal edges/connections sú kľúčové pre junction movement.
- Weak connectivity nie je directed routability.
- Testuj vclass permissions.
- `--ignore-errors` nie je produkčný fix.
- Headless QA používa `sumo`, bounded end, deterministic seed, exit code a error log.
- Preserve original OSM IDs/names in provenance, ale runtime IDs sanitizuj/stabilizuj.

## 12. GIS tips

- `(lon, lat)` contract a `always_xy=True` používaj konzistentne.
- SUMO `x,y` zahŕňa `netOffset`; nevolaj ho UTM bez inverse.
- UTM nie je vždy správna projekcia pre veľké/pásmové AOI.
- Horizontal reprojection neprevedie automaticky vertical datum.
- DSM zahŕňa vegetáciu/budovy; road elevation potrebuje filtering/civil profile.
- Keep Float32 DEM until controlled BeamNG terrain quantization.
- Report max/RMS transform and quantization error.
- Nodata nikdy nenahrádzaj nulou bez policy.

## 13. Determinism

Do build identity zahrň:

- normalized user request/AOI;
- source URLs + checksums;
- OSM/DEM retrieval versions;
- tool versions;
- config/profile;
- schema versions;
- random seeds;
- target BeamNG adapter;
- asset manifest;
- code commit;
- build mode.

Deterministic ZIP:

- stable file ordering;
- normalized paths;
- fixed timestamp policy;
- stable JSON formatting/order;
- locale/timezone-independent formatting;
- seeded procedural generation;
- no temp/user path;
- hash report.

Rovnaký input s nepinned live OSM/DEM nie je rovnaký build. Cache/provenance musí odlíšiť source version.

## 14. Job state machine

Odporúčané high-level states:

```text
created
-> validating_input
-> researching_capabilities
-> acquiring_sources
-> compiling_mapframe
-> compiling_topology
-> compiling_civil_geometry
-> building_target
-> validating_static
-> awaiting_runtime_bake | runtime_testing
-> packaging
-> verifying_package
-> complete
```

Každý state:

- idempotent;
- má explicitný input/output contract;
- zapisuje progress a structured error;
- používa atomic temp→final publish;
- podporuje cancellation;
- po zlyhaní nevystaví starý ZIP ako nový;
- rozlišuje retryable a terminal errors.

## 15. Security

Kontroluj:

- bbox/area/raster dimension/feature count limits;
- URL allowlist/SSRF;
- archive traversal, symlink, duplicate/case collision;
- XML entity expansion;
- JSON/CSV size/depth;
- subprocess argv bez shell interpolation;
- timeouts, memory/disk budgets;
- temp isolation;
- secret redaction;
- outbound provider policy;
- dependency signatures/checksums;
- asset licences.

OSM/DEM input je nedôveryhodný. Aj legitímny dataset môže byť extrémne veľký alebo malformed.

## 16. Testing pyramid

### Unit/property

- CRS round-trip;
- stable IDs;
- lane widths;
- station interpolation;
- curvature/grade/crossfall continuity;
- polygon validity;
- bridge/tunnel topology;
- ZIP path sanitizer.

### Golden

- editor-saved minimal level;
- DecalRoad/MeshRoad nodes;
- terrain binary;
- DAE/material;
- SUMO network;
- deterministic ZIP.

### Integration

- synthetic OSM → SUMO → RoadIR;
- DEM → aligned terrain;
- RoadIR → physical/visual/AI target;
- clean package validator.

### Runtime

- BeamNG load/spawn/drive/AI/reload;
- Road Architect save/reload;
- headless SUMO route/simulation;
- Blender import/export probe.

### Visual

- fixed cameras;
- road/terrain seams;
- junctions;
- material/LOD;
- day/night if supported.

## 17. UI hint

Wizard má používateľovi ukázať:

- location/AOI a attribution;
- estimated source/build size;
- data/provider status;
- quality profile;
- advanced engineering assumptions;
- progress per stage;
- warnings, retries a actionable blocker;
- QA evidence;
- ZIP hash/download;
- „Open in BeamNG“ iba ak launch capability prešla.

Tlačidlo Generate nesmie okamžite sľúbiť úspech. UI musí kopírovať server-side state machine a po zlyhaní skryť neplatný download.

## 18. Local archaeology hints

Ak existujú, čítaj iba ako lessons/fixtures:

```text
C:\GeoCrashSim\GeoCrashSim-BeamNG\apps\geocrash_bridge\...
C:\GeoCrashSim\GeoCrashSim-BeamNG\geocrash\beamng\...
C:\GeoCrashSim\mapng\services\exportBeamNGLevel.js
C:\GeoCrashSim\mapng\components\panels\ExportPanel.vue
```

Hľadaj:

- MapFrame assumptions;
- native road serializer;
- ZIP validation;
- visual diagnostics;
- Road Architect session/profile generator;
- UI export modes.

Nekopíruj bug ani tvrdenie bez testu. Známa pasca: session/profile generation alebo AI DecalRoad môže existovať bez overenej viditeľnej fyzickej cesty.

## 19. Definition of a truthful progress report

Každý report rozdeľ:

```text
Implemented:
Statically validated:
Integration tested:
Runtime verified:
Visually inspected:
Not yet proven:
Blocked by:
Evidence paths:
Next falsifiable milestone:
```

Najlepší report nie je najoptimistickejší. Je ten, z ktorého ďalší človek presne vie, čo funguje a čo ešte nie.

