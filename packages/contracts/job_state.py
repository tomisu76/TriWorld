from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict, Any
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    VALIDATING_REQUEST = "validating_request"
    RESOLVING_SOURCES = "resolving_sources"
    FETCHING_OSM = "fetching_osm"
    FETCHING_DEM = "fetching_dem"
    NORMALIZING_SPATIAL_DATA = "normalizing_spatial_data"
    BUILDING_ROAD_TOPOLOGY = "building_road_topology"
    RUNNING_SUMO = "running_sumo"
    DESIGNING_CIVIL_ROADS = "designing_civil_roads"
    FORMING_TERRAIN = "forming_terrain"
    BUILDING_MESHES = "building_meshes"
    BUILDING_VISUAL_LAYERS = "building_visual_layers"
    PLACING_ASSETS = "placing_assets"
    SERIALIZING_BEAMNG = "serializing_beamng"
    VALIDATING_TARGET = "validating_target"
    PACKAGING = "packaging"
    AUDITING_ZIP = "auditing_zip"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobEvent(BaseModel):
    jobId: str
    stage: str
    stageProgress: float
    overallProgress: float
    message: str
    metrics: Dict[str, Any] = {}


STAGE_WEIGHTS = {
    "validating_request": 0.02,
    "resolving_sources": 0.03,
    "fetching_osm": 0.07,
    "fetching_dem": 0.07,
    "normalizing_spatial_data": 0.05,
    "building_road_topology": 0.10,
    "running_sumo": 0.08,
    "designing_civil_roads": 0.13,
    "forming_terrain": 0.10,
    "building_meshes": 0.10,
    "building_visual_layers": 0.08,
    "placing_assets": 0.05,
    "serializing_beamng": 0.05,
    "validating_target": 0.03,
    "packaging": 0.02,
    "auditing_zip": 0.02,
}

STAGE_ORDER = list(STAGE_WEIGHTS.keys())

TERMINAL_STATES = {JobStatus.READY, JobStatus.FAILED, JobStatus.CANCELLED}


def compute_overall_progress(current_stage: str, stage_progress: float) -> float:
    """Compute overall progress from stage progress."""
    try:
        idx = STAGE_ORDER.index(current_stage)
    except ValueError:
        return 0.0
    
    completed_weight = sum(STAGE_WEIGHTS[s] for s in STAGE_ORDER[:idx])
    current_weight = STAGE_WEIGHTS.get(current_stage, 0.0)
    return min(1.0, completed_weight + current_weight * stage_progress)