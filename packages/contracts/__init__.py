"""TriWorld Contracts Package - Pydantic v2 Data Models"""

from .map_request import (
    MapCompilationRequest,
    MapFrame,
    AxisConvention,
    VerticalDatum,
    RasterConvention,
    TrafficSide,
    QualityProfile,
    OutputFlavor,
)

from .road_ir import (
    RoadNetworkIR,
    RoadSegment,
    RoadClass,
    LaneConfig,
    WidthConfig,
    SourceRef,
)

from .terrain_ir import TerrainIR

from .mesh_ir import MeshIR, Submesh

from .beamng_target_ir import (
    BeamNGTargetIR,
    TSStaticItem,
    DecalRoadItem,
)

from .job_state import (
    JobStatus,
    JobEvent,
    STAGE_WEIGHTS,
    STAGE_ORDER,
    TERMINAL_STATES,
    compute_overall_progress,
)

__all__ = [
    # Map Request
    "MapCompilationRequest",
    "MapFrame",
    "AxisConvention",
    "VerticalDatum",
    "RasterConvention",
    "TrafficSide",
    "QualityProfile",
    "OutputFlavor",
    # Road IR
    "RoadNetworkIR",
    "RoadSegment",
    "RoadClass",
    "LaneConfig",
    "WidthConfig",
    "SourceRef",
    # Terrain IR
    "TerrainIR",
    # Mesh IR
    "MeshIR",
    "Submesh",
    # BeamNG Target IR
    "BeamNGTargetIR",
    "TSStaticItem",
    "DecalRoadItem",
    # Job State
    "JobStatus",
    "JobEvent",
    "STAGE_WEIGHTS",
    "STAGE_ORDER",
    "TERMINAL_STATES",
    "compute_overall_progress",
]