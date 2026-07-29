from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict
from enum import Enum


class RoadClass(str, Enum):
    MOTORWAY = "motorway"
    TRUNK = "trunk"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    UNCLASSIFIED = "unclassified"
    RESIDENTIAL = "residential"
    SERVICE = "service"
    TRACK = "track"


class LaneConfig(BaseModel):
    forward: int = Field(ge=0)
    backward: int = Field(ge=0)
    source: str


class WidthConfig(BaseModel):
    total: float = Field(gt=0)
    source: str


class SourceRef(BaseModel):
    kind: Literal["osm"] = "osm"
    wayId: int


class RoadSegment(BaseModel):
    id: str
    source: SourceRef
    class_: RoadClass = Field(alias="class")
    direction: Literal["forward", "backward", "both"]
    lanes: LaneConfig
    widthM: WidthConfig
    layer: int = 0
    bridge: bool = False
    tunnel: bool = False
    roundabout: bool = False
    centerlineLocalM: List[List[float]]  # [[x, y], ...]
    warnings: List[str] = []


class RoadNetworkIR(BaseModel):
    segments: List[RoadSegment]


class StationFrame(BaseModel):
    station: float
    xyz: List[float]  # [x, y, z]
    tangent: List[float]  # [tx, ty, tz]
    lateral: List[float]  # [lx, ly, lz]
    grade: float
    curvature: float
    crossfall: Dict[str, float]  # {left, right, bank}
    crossSection: Dict[str, List[float]]  # semantic points


class Corridor(BaseModel):
    id: str
    stations: List[float]
    frames: List[StationFrame]
    sourceSegmentIds: List[str]


class JunctionPatch(BaseModel):
    id: str
    type: Literal["T", "X", "Y", "roundabout", "ramp_merge", "ramp_diverge"]
    polygon: List[List[float]]
    lanes: List[Dict]


class BridgeDeck(BaseModel):
    id: str
    corridorId: str
    stationRange: List[float]
    deckPolygon: List[List[float]]
    abutments: List[Dict]


class TunnelPolicy(BaseModel):
    id: str
    corridorId: str
    stationRange: List[float]
    portalPolygon: List[List[float]]
    meshPolicy: Literal["skip", "portals_only", "full_mesh"]


class EarthworkCorridor(BaseModel):
    corridorId: str
    formationSurface: List[List[float]]  # target elevation grid
    cutFill: List[float]
    slopeMasks: Dict


class CivilRoadIR(BaseModel):
    corridors: List[Corridor]
    junctionPatches: List[JunctionPatch]
    bridgeDecks: List[BridgeDeck]
    tunnelPolicies: List[TunnelPolicy]
    earthworkCorridors: List[EarthworkCorridor]