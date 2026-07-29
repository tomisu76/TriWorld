from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict
from enum import Enum


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
    bounds: Dict[str, List[float]]  # {min: [x,y,z], max: [x,y,z]}
    sourceIds: List[str]