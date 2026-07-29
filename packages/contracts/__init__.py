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

from .civil_ir import (
    CivilRoadIR,
    Corridor,
    StationFrame,
    JunctionPatch,
    BridgeDeck,
    TunnelPolicy,
    EarthworkCorridor,
)

from .terrain_mesh_beamng import (
    TerrainIR,
    DemArtifact,
    VerticalDatumType,
    MeshIR,
    Submesh,
    TSStaticItem,
    DecalRoadItem,
    TerrainBlockItem,
    BeamNGTargetIR,
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
    # Civil IR
    "CivilRoadIR",
    "Corridor",
    "StationFrame",
    "JunctionPatch",
    "BridgeDeck",
    "TunnelPolicy",
    "EarthworkCorridor",
    # Terrain/Mesh/BeamNG
    "TerrainIR",
    "DemArtifact",
    "VerticalDatumType",
    "MeshIR",
    "Submesh",
    "TSStaticItem",
    "DecalRoadItem",
    "TerrainBlockItem",
    "BeamNGTargetIR",
    # Job State
    "JobStatus",
    "JobEvent",
    "STAGE_WEIGHTS",
    "STAGE_ORDER",
    "TERMINAL_STATES",
    "compute_overall_progress",
]