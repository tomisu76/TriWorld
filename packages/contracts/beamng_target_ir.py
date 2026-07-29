from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict
from enum import Enum


class TSStaticItem(BaseModel):
    class_: Literal["TSStatic"] = "TSStatic"
    name: str
    position: List[float]  # [x, y, z]
    rotation: List[float]  # [x, y, z, w] quaternion
    scale: List[float] = [1.0, 1.0, 1.0]
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


class BeamNGTargetIR(BaseModel):
    terrainBlock: Dict
    tsstatics: List[TSStaticItem]
    decalRoads: List[DecalRoadItem]
    materials: Dict
    textures: List[str]
    spawnPoints: List[Dict]
    environment: Dict
    mapJson: Optional[Dict] = None