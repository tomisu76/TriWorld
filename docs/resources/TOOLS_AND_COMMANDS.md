# Tools and command handbook

Toto je discovery a verification handbook, nie záruka, že uvedená verzia je nainštalovaná. Každý príkaz spusti z explicitnej cesty, skontroluj exit code a zachyť sanitizovaný output.

## 1. Povinné schopnosti

| Oblasť | Nástroje | Účel |
|---|---|---|
| Source control | Git, `rg` | audit, versioning, fast source search |
| Orchestration/UI | Node.js LTS, package manager podľa lockfile | API, worker, web UI |
| Geometry/contracts | Python 3.12+ podľa lockfile | GIS, compiler, tests |
| GIS | GDAL, PROJ, pyproj, raster/vector libs | CRS, warp, crop, DEM |
| Traffic | SUMO tools z jednej pinned distribúcie | OSM net, validation, routing |
| Assets | Blender exact pinned version | deterministic mesh QA/export |
| Runtime | BeamNG.drive exact pinned build | authoritative load/drive/bake |
| Research | Hermes web tools, browser, Git | current primary evidence |
| Optional synthesis | NotebookLM manual or Enterprise Preview | cited source comparison |
| QA | pytest, type/lint/schema tools, Playwright podľa repo | gates |

Nevyber dependency iba podľa popularity. Zaznamenaj verziu, licenciu, platform support a reproducible install.

## 2. Environment inventory on Windows

```powershell
Set-Location -LiteralPath 'C:\TriWorld'

$toolNames = @(
  'git','rg','python','py','node','npm','pnpm','corepack',
  'gdalinfo','gdalwarp','gdal_translate','gdaldem','projinfo',
  'netconvert','netedit','sumo','sumo-gui','duarouter','blender'
)

Get-Command $toolNames -ErrorAction SilentlyContinue |
  Select-Object Name,Source,Version
```

Potom samostatne:

```powershell
git --version
python --version
node --version
gdalinfo --version
projinfo --version
netconvert --version
sumo --version
blender --version
```

V reportoch nahraď lokálne korene placeholdermi:

```text
<REPO_ROOT>
<BEAMNG_INSTALL>
<BEAMNG_USERPATH>
<SUMO_HOME>
<BLENDER_ROOT>
```

## 3. Safe repository audit

```powershell
git -C 'C:\TriWorld' status --short --branch
git -C 'C:\TriWorld' rev-parse --show-toplevel
git -C 'C:\TriWorld' diff --stat
git -C 'C:\TriWorld' ls-files
rg --files 'C:\TriWorld' -g '!node_modules' -g '!dist' -g '!build'
```

Ak repo nemá commit, `git diff` neukáže untracked content. Inventár rob aj cez `rg --files` a `git status`.

Zakázané bez explicitného súhlasu:

```text
git reset --hard
git clean -fdx
recursive delete
force push
```

## 4. Hermes research setup

Oficiálne Hermes CLI používa interaktívny setup:

```text
hermes tools
hermes setup
```

Potrebné capability:

```text
web_search
web_extract
delegate_task
browser navigation/snapshot for exact long-page evidence
```

Príklad configu:

```yaml
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"

delegation:
  max_concurrent_children: 3
  max_spawn_depth: 1
  orchestrator_enabled: true
```

Backends sú príklad. Použi ten, ktorý je autorizovaný a funkčný. API keys patria do Hermes secret/config mechanizmu mimo Git. DDGS/Brave/SearXNG môžu byť search-only; extract backend vyber osobitne. Pri dlhom `web_extract` over presný detail v raw stránke/source.

## 5. Git source pinning

```powershell
git ls-remote https://github.com/eclipse-sumo/sumo.git HEAD
git ls-remote --tags https://github.com/eclipse-sumo/sumo.git
git ls-remote https://github.com/NousResearch/hermes-agent.git HEAD
git ls-remote --tags https://github.com/NousResearch/hermes-agent.git
```

Do `version-lock.md` zapíš canonical URL, tag, resolved SHA, retrieval date a checksum stiahnutého archívu. Nepoužívaj moving `main` vo fixture/release buildoch.

## 6. CRS and DEM audit

CRS:

```powershell
projinfo EPSG:4326
gdalinfo -json '<INPUT_DEM>'
```

Ukážka warp pre continuous elevation; EPSG a extent sú placeholders:

```powershell
gdalwarp `
  -s_srs EPSG:4326 `
  -t_srs EPSG:32634 `
  -te <xmin> <ymin> <xmax> <ymax> `
  -te_srs EPSG:32634 `
  -tr 10 10 `
  -tap `
  -r bilinear `
  -srcnodata -9999 `
  -dstnodata -9999 `
  -ot Float32 `
  -co TILED=YES `
  -co COMPRESS=DEFLATE `
  -overwrite `
  '<INPUT_DEM>' '<ALIGNED_DEM>'
```

Pravidlá:

- `-te` je `xmin ymin xmax ymax`;
- `-te_srs` popisuje súradnice extentu, nenahrádza `-t_srs`;
- categorical raster používa nearest; continuous elevation vhodný continuous resampler;
- vertical datum sa horizontálnym reprojection automaticky neopraví;
- over output CRS, extent, pixel size, nodata, min/max, seams a round-trip.

Python transform:

```python
from pyproj import CRS, Transformer

source = CRS.from_epsg(4326)
target = CRS.from_epsg(32634)  # example only; derive from AOI
transformer = Transformer.from_crs(
    source,
    target,
    always_xy=True,
    allow_ballpark=False,
    only_best=True,
)
easting, northing = transformer.transform(lon, lat)
```

Nepreber example EPSG do produkcie. Zvoľ projekciu podľa AOI, area of use a distortion budget.

## 7. SUMO build and QA

Minimal discovery:

```powershell
netconvert --help
netconvert --osm-files '<AOI_OSM>' --output-file '<AREA_NET>'
```

Controlled options musia byť uložené v configu a overené proti pinned docs:

```powershell
netconvert `
  --osm-files '<AOI_OSM>' `
  --heightmap.geotiff '<ALIGNED_DEM>' `
  --output-file '<AREA_NET>' `
  --geometry.remove `
  --ramps.guess `
  --junctions.join `
  --tls.guess-signals `
  --tls.discard-simple `
  --tls.join `
  --tls.default-type actuated `
  --osm.turn-lanes `
  --output.original-names
```

Tieto flags nie sú univerzálne správne. `--junctions.join` môže nesprávne zlúčiť križovatky; custom `--type-files` nahradia default typemap; `--no-internal-links` poškodí intersection fidelity. Vždy ulož warnings.

Connectivity:

```powershell
python '<SUMO_HOME>\tools\net\netcheck.py' '<AREA_NET>' `
  --component-output '<COMPONENTS>' `
  --results-output '<NETCHECK_RESULTS>' `
  --vclass passenger
```

Source/destination checks spúšťaj osobitne:

```powershell
python '<SUMO_HOME>\tools\net\netcheck.py' '<AREA_NET>' `
  --source '<START_EDGE>' `
  --selection-output '<REACHABLE>' `
  --vclass passenger
```

Routing:

```powershell
duarouter `
  --trip-files '<TRIPS_XML>' `
  --net-file '<AREA_NET>' `
  --output-file '<ROUTES_XML>'
```

Headless smoke:

```powershell
sumo -c '<SCENARIO_SUMOCFG>' --no-step-log --error-log '<RUN_ERRORS>'
```

Nezapínaj globálne `--ignore-errors` alebo `--no-warnings` ako spôsob, ako dostať build cez gate.

## 8. Blender deterministic probe

```powershell
blender --background --factory-startup --python '<PROBE_SCRIPT>'
```

Probe:

```python
import bpy

print({
    "version": bpy.app.version_string,
    "collada_import": hasattr(bpy.ops.wm, "collada_import"),
    "collada_export": hasattr(bpy.ops.wm, "collada_export"),
})
```

Každý asset build má explicitné units, axes, triangulation policy, normals/tangents, material slots, collision naming, LOD, origin a deterministic ordering. Skontroluj exit code a otvor výsledok na čistom Blender profile.

## 9. BeamNG launch and World Editor

Bez dôkazu nehardcoduj `-level`, `-editor` ani internú Lua command line. Presný launcher contract sa musí nájsť v:

1. oficiálnej dokumentácii pre cieľovú verziu;
2. lokálnom command parser/source cieľovej inštalácie;
3. minimálnom direct-launch canary.

Bezpečný manuálny fallback:

1. vlož overený ZIP do správneho user mods location;
2. spusti BeamNG normálne;
3. vyber level v UI;
4. počkaj na spawn a čistý log;
5. stlač `F11`;
6. otvor Road Architect cez World Editor tools/mode;
7. pri bake vykonaj Render/finalize, save, close/reload a persistence check.

Budúci `scripts/open-in-beamng.ps1` musí:

- nájsť executable a user path bez hardcoded používateľského mena;
- overiť target version;
- overiť nainštalovaný ZIP hash;
- použiť iba versioned launch adapter;
- zachytiť nový PID a nový log;
- čakať na konkrétny load marker s timeoutom;
- pri neznámom argumente failnúť closed;
- mať manual UI fallback.

Existencia procesu nie je level-load dôkaz. `F11` nie je API a manuálny flow musí zostať zdokumentovaný.

## 10. Hashing and ZIP inspection

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '<MAP_ZIP>'

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead('<MAP_ZIP>')
try {
  $archive.Entries | Select-Object FullName,Length,CompressedLength
}
finally {
  $archive.Dispose()
}
```

Validátor musí navyše zakázať:

- absolute paths;
- `..` traversal;
- wrapper directory nad `levels/<slug>/`;
- duplicate/case-colliding paths;
- temp/cache/source/autosave;
- symlinks/reparse surprises;
- chýbajúce referenced files;
- neznáme proprietary dependencies;
- extrémny compression ratio/resource use.

## 11. Test command policy

Skutočné príkazy odvodzuj z lockfile/package configu. Očakávaný tvar:

```powershell
python -m pytest
python -m ruff check .
python -m mypy packages
corepack enable
pnpm install --frozen-lockfile
pnpm test
pnpm build
```

Nespúšťaj placeholder príkaz, ak repo nepoužíva daný nástroj. Najprv inspect `pyproject.toml`, `package.json`, workspace file a lockfile. Reportuj exit code a zlyhania; nefabrikuj zelený výsledok.

