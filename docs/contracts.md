# Data Contracts (Pydantic v2 Models)

## MapCompilationRequest
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from enum import Enum

class TrafficSide(str, Enum):
    RIGHT = "right"
    LEFT = "left"

class QualityProfile(str, Enum):
    FAST_PREVIEW = "fast_preview"
    DRIVABLE = "drivable"
    HIGH_QUALITY = "high_quality"
    STUDIO = "studio"

class OutputFlavor(str, Enum):
    PORTABLE = "portable"
    STOCK_ITALY_DEPENDENT = "stock_italy_dependent"
    STUDIO_ORIGINAL = "studio_original"

class SourceConfig(BaseModel):
    roads: dict = Field(default_factory=lambda: {"provider": "overpass-or-cache"})
    dem: dict = Field(default_factory=lambda: {"provider": "mapzen-terrarium"})
    imagery: dict = Field(default_factory=lambda: {"provider": "none"})

class FeaturesConfig(BaseModel):
    sumo: bool = True
    buildings: bool = True
    vegetation: bool = True
    water: bool = True
    blender_qa: bool = False
    road_architect_session: bool = False

class MapCompilationRequest(BaseModel):
    schemaVersion: str = "1.0"
    name: str = Field(pattern=r"^[a-z0-9_]+$")
    center: dict = Field(description="{lat: float, lon: float}")
    extent: dict = Field(description="{widthM: float, heightM: float}")
    terrainResolutionM: float = Field(gt=0, le=10)
    qualityProfile: QualityProfile = QualityProfile.DRIVABLE
    outputFlavor: OutputFlavor = OutputFlavor.PORTABLE
    trafficSide: TrafficSide = TrafficSide.RIGHT
    sources: SourceConfig = Field(default_factory=SourceConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    seed: int = Field(default=184467, ge=0)

    @field_validator("center")
    @classmethod
    def validate_center(cls, v):
        lat, lon = v.get("lat"), v.get("lon")
        if not (-90 <= lat <= 90): raise ValueError("lat out of range")
        if not (-180 <= lon <= 180): raise ValueError("lon out of range")
        return v

    @field_validator("extent")
    @classmethod
    def validate_extent(cls, v):
        w, h = v.get("widthM"), v.get("heightM")
        if not (w > 0 and h > 0): raise ValueError("extent must be positive")
        if max(w, h) > 8192: raise ValueError("extent too large")
        return v
```

## MapFrame
```python
class AxisConvention(BaseModel):
    x: Literal["east"]
    y: Literal["north"]
    z: Literal["up"]
    linearUnit: Literal["metre"]

class VerticalDatum(BaseModel):
    name: str
    normalization: Literal["recorded-not-assumed"]

class RasterConvention(BaseModel):
    row0: Literal["north"]
    pixel: Literal["area"]

class MapFrame(BaseModel):
    schemaVersion: str = "1.0"
    sourceCrs: str = "EPSG:4326"
    projectedCrsWkt2: str
    projectionChoice: str
    anchorLonLat: list[float]  # [lon, lat]
    anchorProjectedM: list[float]  # [x, y]
    localOriginProjectedM: list[float] = [0.0, 0.0]
    axisConvention: AxisConvention = AxisConvention(x="east", y="north", z="up", linearUnit="metre")
    verticalDatum: VerticalDatum
    rasterConvention: RasterConvention = RasterConvention(row0="north", pixel="area")
```

## RoadNetworkIR
```python
class LaneConfig(BaseModel):
    forward: int
    backward: int
    source: str

class WidthConfig(BaseModel):
    total: float
    source: str

class RoadSegment(BaseModel):
    id: str
    source: dict  # {kind: "osm", wayId: int}
    class_: str = Field(alias="class")
    direction: Literal["forward", "backward", "both"]
    lanes: LaneConfig
    widthM: WidthConfig
    layer: int = 0
    bridge: bool = False
    tunnel: bool = False
    roundabout: bool = False
    centerlineLocalM: list[list[float]]  # [[x, y], ...]
    warnings: list[str] = []
```

## CivilRoadIR
```python
class Corridor(BaseModel):
    id: str
    station: list[float]
    xyz: list[list[float]]
    tangent: list[list[float]]
    lateral: list[list[float]]
    grade: list[float]
    curvature: list[float]
    crossfall: list[dict]  # {left, right, bank, transition}
    crossSection: list[dict]  # semantic points per station

class JunctionPatch(BaseModel):
    id: str
    type: Literal["T", "X", "Y", "roundabout", "ramp_merge", "ramp_diverge"]
    polygon: list[list[float]]
    lanes: list[dict]

class BridgeDeck(BaseModel):
    id: str
    corridorId: str
    stationRange: list[float]
    deckPolygon: list[list[float]]
    abutments: list[dict]

class TunnelPolicy(BaseModel):
    id: str
    corridorId: str
    stationRange: list[float]
    portalPolygon: list[list[float]]
    meshPolicy: Literal["skip", "portals_only", "full_mesh"]

class EarthworkCorridor(BaseModel):
    corridorId: str
    formationSurface: list[list[float]]  # target elevation grid
    cutFill: list[float]
    slopeMasks: dict

class CivilRoadIR(BaseModel):
    corridors: list[Corridor]
    junctionPatches: list[JunctionPatch]
    bridgeDecks: list[BridgeDeck]
    tunnelPolicies: list[TunnelPolicy]
    earthworkCorridors: list[EarthworkCorridor]
```

## TerrainIR
```python
class TerrainIR(BaseModel):
    originalDem: dict  # {path, crs, verticalDatum, resolution, nodata, bbox, hash}
    nodataMask: str  # path to boolean mask
    normalizedDem: str  # path to reprojected DEM in MapFrame
    formationTarget: str  # path to road formation surface
    cutFillDelta: str  # path to cut/fill grid
    finalDem: str  # path to final blended DEM
    materialMasks: dict  # {layerName: path}
    transform: dict  # MapFrame projection info
    statistics: dict  # min, max, mean, std, percentiles
```

## MeshIR
```python
class Submesh(BaseModel):
    name: str
    materialSlot: int
    indexStart: int
    indexCount: int

class MeshIR(BaseModel):
    id: str
    positions: list[list[float]]  # [[x, y, z], ...]
    normals: list[list[float]]
    uv0: list[list[float]]
    indices: list[int]
    materialSlots: list[str]
    submeshes: list[Submesh]
    collisionClass: str
    lodClass: str
    bounds: dict  # {min, max}
    sourceIds: list[str]
```

## BeamNGTargetIR
```python
class TSStaticItem(BaseModel):
    class_: Literal["TSStatic"] = "TSStatic"
    name: str
    position: list[float]
    rotation: list[float]  # [x, y, z, w]
    scale: list[float] = [1, 1, 1]
    shapeName: str
    collisionType: Literal["Collision Mesh", "Convex Hull", "Box"]
    decalType: Optional[str] = None

class DecalRoadItem(BaseModel):
    class_: Literal["DecalRoad"] = "DecalRoad"
    name: str
    position: list[float]
    rotation: list[float]
    nodes: list[list[float]]  # [x, y, z, width] - HALF WIDTH per contract
    drivability: float = 1.0
    oneWay: bool = False
    material: str

class BeamNGTargetIR(BaseModel):
    terrainBlock: dict
    tsstatics: list[TSStaticItem]
    decalRoads: list[DecalRoadItem]
    materials: dict
    textures: list[str]
    spawnPoints: list[dict]
    environment: dict
    mapJson: Optional[dict] = None
```