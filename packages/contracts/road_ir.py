from pydantic import BaseModel, Field
from typing import Literal, List, Optional
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