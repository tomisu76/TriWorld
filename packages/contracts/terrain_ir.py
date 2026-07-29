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
    nodata: float
    bbox: List[float]
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