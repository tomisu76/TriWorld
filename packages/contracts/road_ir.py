from pydantic import BaseModel
from typing import List, Tuple

class RoadSegmentIR(BaseModel):
    id: str
    centerline: List[Tuple[float, float]]
    roadWidthMetres: float = 3.25

class RoadNetworkIR(BaseModel):
    segments: List[RoadSegmentIR]
