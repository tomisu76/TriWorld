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
        if not (-90 <= lat <= 90):
            raise ValueError("lat out of range")
        if not (-180 <= lon <= 180):
            raise ValueError("lon out of range")
        return v

    @field_validator("extent")
    @classmethod
    def validate_extent(cls, v):
        w, h = v.get("widthM"), v.get("heightM")
        if not (w > 0 and h > 0):
            raise ValueError("extent must be positive")
        if max(w, h) > 8192:
            raise ValueError("extent too large")
        return v


class AxisConvention(BaseModel):
    x: Literal["east"] = "east"
    y: Literal["north"] = "north"
    z: Literal["up"] = "up"
    linearUnit: Literal["metre"] = "metre"


class VerticalDatum(BaseModel):
    name: str
    normalization: Literal["recorded-not-assumed"] = "recorded-not-assumed"


class RasterConvention(BaseModel):
    row0: Literal["north"] = "north"
    pixel: Literal["area"] = "area"


class MapFrame(BaseModel):
    schemaVersion: str = "1.0"
    sourceCrs: str = "EPSG:4326"
    projectedCrsWkt2: str
    projectionChoice: str
    anchorLonLat: list[float]  # [lon, lat]
    anchorProjectedM: list[float]  # [x, y]
    localOriginProjectedM: list[float] = [0.0, 0.0]
    axisConvention: AxisConvention = AxisConvention()
    verticalDatum: VerticalDatum
    rasterConvention: RasterConvention = RasterConvention()