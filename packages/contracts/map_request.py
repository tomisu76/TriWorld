from pydantic import BaseModel, Field
from typing import List, Optional

class GeoPoint(BaseModel):
    longitude: float
    latitude: float

class AreaConfig(BaseModel):
    center: GeoPoint
    sizeMetres: float
    terrainResolution: int
    bufferMetres: int

class SourceConfig(BaseModel):
    provider: str
    snapshotRequired: bool = True

class SourcesConfig(BaseModel):
    roads: SourceConfig
    terrain: SourceConfig
    landcover: Optional[SourceConfig] = None

class RoadsConfig(BaseModel):
    topologyEngine: str
    qualityProfile: str

class OutputConfig(BaseModel):
    target: str
    levelId: str
    mode: str
    assetMode: str
    targetBeamngVersion: str

class MapCompilationRequest(BaseModel):
    schemaVersion: str = "1.0"
    area: AreaConfig
    sources: SourcesConfig
    roads: RoadsConfig
    output: OutputConfig
