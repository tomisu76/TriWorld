from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Optional
from enum import Enum


class VerticalDatumType(str, Enum):
    ELLIPSOIDAL = "ellipsoidal"
    ORTHOMETRIC = "orthometric"
    UNKNOWN = "unknown"


class DemArtifact(BaseModel):
    path: str
    crs: str
    verticalDatum: VerticalDatumType
    resolution: float
    nodata: Optional[float] = None
    bbox: List[float]  # [minx, miny, maxx, maxy]
    hash: str


class TerrainIR(BaseModel):
    originalDem: DemArtifact
    nodataMask: str  # path to boolean mask
    normalizedDem: str  # path to reprojected DEM in MapFrame
    formationTarget: str  # path to road formation surface
    cutFillDelta: str  # path to cut/fill grid
    finalDem: str  # path to final blended DEM
    materialMasks: Dict[str, str]  # {layerName: path}
    transform: Dict  # MapFrame projection info
    statistics: Dict  # min, max, mean, std, percentiles


class Submesh(BaseModel):
    name: str
    materialSlot: int
    indexStart: int
    indexCount: int


class MeshIR(BaseModel):
    id: str
    positions: List[List[float]]  # [[x, y, z], ...]
    normals: List[List[float]]
    uv0: List[List[float]]
    indices: List[int]
    materialSlots: List[str]
    submeshes: List[Submesh]
    collisionClass: str
    lodClass: str
    bounds: Dict  # {min: [x,y,z], max: [x,y,z]}
    sourceIds: List[str]


class TSStaticItem(BaseModel):
    class_: Literal["TSStatic"] = "TSStatic"
    name: str
    position: List[float]
    rotation: List[float]  # [x, y, z, w]
    scale: List[float] = [1, 1, 1]
    shapeName: str
    collisionType: Literal["Collision Mesh", "Convex Hull", "Box"] = "Collision Mesh"
    decalType: Optional[str] = None


class DecalRoadItem(BaseModel):
    class_: Literal["DecalRoad"] = "DecalRoad"
    name: str
    position: List[float]
    rotation: List[float]
    nodes: List[List[float]]  # [x, y, z, halfWidth]
    drivability: float = 1.0
    oneWay: bool = False
    material: str


class TerrainBlockItem(BaseModel):
    class_: Literal["TerrainBlock"] = "TerrainBlock"
    name: str
    position: List[float]
    rotation: List[float]
    scale: List[float]
    terrainFile: str
    squareSize: float
    maxHeight: float


class BeamNGTargetIR(BaseModel):
    terrainBlock: TerrainBlockItem
    tsstatics: List[TSStaticItem]
    decalRoads: List[DecalRoadItem]
    materials: Dict
    textures: List[str]
    spawnPoints: List[Dict]
    environment: Dict
    mapJson: Optional[Dict] = None