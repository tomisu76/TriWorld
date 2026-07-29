# SUMO, OSM, GIS and DEM QA checklist

Táto gate chráni pred mapou, ktorá vyzerá približne správne, ale má prehodené osi, chybný graph, falošné križovatky alebo vertikálne posuny.

## A. AOI and source provenance

- [ ] User point, requested size a derived bbox/polygon sú uložené.
- [ ] Antimeridian/polar/UTM-zone crossing behavior je definované.
- [ ] OSM source/provider, retrieval timestamp a response checksum sú uložené.
- [ ] Query, endpoint a identifying user-agent/contact sú uložené bez secretov.
- [ ] Cache key zahŕňa AOI, source version/date, relevantné options a schema version.
- [ ] OSM attribution a ODbL review sú pripravené pre UI/ZIP.
- [ ] Tile/Nominatim/Overpass provider policy nie je porušená.
- [ ] Build sa nespolieha na public tile pre offline terrain/texture scraping.

## B. MapFrame contract

Povinné fields:

```text
source_crs
projected_crs
vertical_crs_or_assumption
axis_order
units
origin_lon_lat
origin_projected
local_axis_orientation
map_extent_local
sumo_net_offset
sumo_proj_parameter
round_trip_tolerance
```

Kontroly:

- [ ] WGS84 API convention je explicitne `(lon, lat)`.
- [ ] pyproj používa `always_xy=True`, ak contract očakáva lon/lat.
- [ ] `allow_ballpark=False` a transformer accuracy/area-of-use sú kontrolované pre release build.
- [ ] Projekcia je odvodená z AOI; example EPSG nie je hardcoded.
- [ ] Local BeamNG origin udržuje koordináty v numericky rozumnom rozsahu.
- [ ] East/north/up a BeamNG axes sú jednotne definované.
- [ ] Známy control point prejde forward+inverse round-trip.
- [ ] Corner/bbox round-trips prejdú toleranciou.
- [ ] Transformácie nerekonštruujú transformer per point.
- [ ] Vertical datum/assumption je oddelený od horizontal CRS.

## C. OSM parsing

- [ ] Node/way/relation refs sú kompletné alebo failure explicitný.
- [ ] `highway`, `junction`, `oneway`, `lanes`, `lanes:forward/backward` sú parsované defensívne.
- [ ] `turn:lanes`, `destination`, `access`, vehicle permissions sú zachované, ak sú v scope.
- [ ] `bridge`, `tunnel`, `layer`, `covered`, `ford` vstupujú do grade-separation modelu.
- [ ] `width` a lane widths majú regionálny/profile fallback, nie slepé univerzálne číslo.
- [ ] `surface`, `smoothness`, `tracktype` sa mapujú oddelene od road class.
- [ ] Maxspeed units a implicit regional defaults sú explicitné.
- [ ] Roundabout direction a one-way inference rešpektujú regional driving side.
- [ ] Duplicate geometry a self-intersections majú validation.
- [ ] Missing/invalid tags sa logujú ako structured warnings.

## D. SUMO import

- [ ] `netconvert --version` a tag sú pinned.
- [ ] Použitý config/options sú uložené ako artefakt.
- [ ] Ak sa používajú custom `--type-files`, potrebné default typemaps sú uvedené explicitne.
- [ ] `--junctions.join` výsledky sú auditované; zlé clusters používajú exclude/repair.
- [ ] `--ramps.guess` a signal guesses sú heuristiky a sú auditované.
- [ ] `--osm.turn-lanes` assumptions sú zdokumentované.
- [ ] `--remove-edges.isolated` neodstránil potrebnú infraštruktúru.
- [ ] Internal links zostali pre intersection fidelity, ak nie je ADR opačne.
- [ ] `netconvert` exit code a celý warning/error log sú zachytené.
- [ ] `.net.xml` `<location>` fields sú uložené v MapFrame provenance.
- [ ] Geometria SUMO sa nepovažuje za hotový civil 3D road surface.

## E. SUMO coordinate handling

- [ ] `netOffset`, `convBoundary`, `origBoundary`, `projParameter` sú parsované.
- [ ] Raw SUMO `x,y` sa nepovažujú za absolute UTM.
- [ ] Používa sa `sumolib.convertLonLat2XY`/inverse alebo ekvivalent verifikovaný proti location contractu.
- [ ] Internal edge geometry je zahrnutá tam, kde treba junction movement.
- [ ] `sumolib.net.readNet(..., withInternal=True)` je použité pre internal-edge QA.
- [ ] Junction declared position sa nezamieňa za polygon centroid.
- [ ] Lane index 0 semantics sa mapujú správne.
- [ ] Connection legality sa odvodzuje z connections, nie iba adjacency edges.

## F. Graph topology

Fixtures:

- [ ] simple two-way road;
- [ ] one-way pair;
- [ ] T and four-way junction;
- [ ] roundabout;
- [ ] motorway ramp;
- [ ] divided road;
- [ ] bridge over road without junction;
- [ ] tunnel crossing;
- [ ] cul-de-sac;
- [ ] disconnected island;
- [ ] restricted vehicle class;
- [ ] malformed OSM fragment.

Checks:

- [ ] `netcheck.py` weak components sú známe.
- [ ] Directed reachability je testovaná source/destination mode.
- [ ] Checks sa opakujú pre `passenger` a ďalšie supported vclasses.
- [ ] Largest drivable component threshold je definovaný.
- [ ] Expected islands/parking/service access sú oddelené od defects.
- [ ] False junction na grade-separated crossing je zero.
- [ ] Lane-to-lane connections majú legal turn coverage.
- [ ] Prohibited turns zostali prohibited.

## G. Routing and headless simulation

- [ ] Deterministická sada OD pairs je uložená.
- [ ] `duarouter` prejde bez blanket `--ignore-errors`.
- [ ] „No connection between“ sa rieši ako defect/permission issue.
- [ ] Trips/flows sú sorted podľa depart/begin, ak to loader vyžaduje.
- [ ] Route definitions neobsahujú ručne internal edges.
- [ ] Map-matching radius/tolerance je explicitný.
- [ ] Headless `sumo` má bounded end/termination.
- [ ] Exit code a `--error-log` sú kontrolované.
- [ ] Warnings nie sú globálne vypnuté počas QA.
- [ ] Deterministic seed a demand version sú zaznamenané.

## H. DEM provenance

- [ ] Dataset/product, provider a original source sú rozlíšené.
- [ ] Licence, attribution, commercial use a redistribution sú vyhodnotené.
- [ ] Horizontal CRS je zapísaný.
- [ ] Vertical datum/geoid je zapísaný.
- [ ] DSM vs bare-earth DTM je zapísané.
- [ ] Resolution, accuracy, acquisition date a coverage sú zapísané.
- [ ] Nodata a void-fill policy sú zapísané.
- [ ] Provider rate limits/key requirements sú dodržané.
- [ ] Download checksum a cache provenance sú uložené.
- [ ] Miešanie EGM96, EGM2008, ellipsoidal alebo national datum bez transformácie je zakázané.

Odporúčané poradie podľa dostupnosti a licencie:

1. national/regional bare-earth LiDAR/DTM;
2. USGS 3DEP pre USA;
3. legitímny globálny fallback (Copernicus/NASADEM/AW3D30) s vedomím, že môže byť DSM;
4. provider/intermediary podľa jeho terms.

## I. Raster warp

- [ ] Source/destination SRS sú explicitné.
- [ ] `-te` order je correct.
- [ ] `-te_srs` zodpovedá extent coordinates.
- [ ] Pixel resolution a `-tap` alignment sú explicitné.
- [ ] Resampler zodpovedá continuous elevation.
- [ ] Source/destination nodata sú explicitné.
- [ ] Float32 sa zachová až do kontrolovanej terrain quantization.
- [ ] Existing overviews/resampler mismatch je kontrolovaný.
- [ ] Output CRS, geotransform, bounds, dimensions a nodata prešli auditom.
- [ ] Min/max/percentiles a nodata count sú v reportoch.
- [ ] Warp nepridal seam/ringing, ktoré ovplyvnia roads.
- [ ] Vertical conversion používa explicitné compound CRS/geoid grids alebo je označená assumption.

## J. Road/terrain coupling

- [ ] DEM je background terrain, nie road final elevation.
- [ ] Road vertical profile má vlastný engineering contract.
- [ ] Cut/fill/embankment sa generujú deterministicky.
- [ ] Terrain conformity používa corridor mask a blending falloff.
- [ ] Road surface a terrain majú clearance tolerance.
- [ ] Bridge deck nie je prilepený k terrainu.
- [ ] Tunnel portal/cut a terrain masking sú riešené.
- [ ] Junction surface je spoločná a bez overlap/gap.
- [ ] Drainage/crossfall nevytvára abrupt roll transitions.
- [ ] Terrain quantization RMS/max error je reportovaný.

## K. Gate report

```text
AOI:
OSM source/checksum:
DEM source/checksum:
MapFrame schema/version:
CRS and vertical datum:
SUMO version:
netconvert config/checksum:
Warnings:
Weak components:
Directed passenger reachability:
OD routing pass rate:
Headless SUMO:
False junction count:
DEM nodata/min/max:
Round-trip max error:
Road/terrain clearance error:
Licensing status:
Not yet proven:
Gate: pass | fail | blocked
```

