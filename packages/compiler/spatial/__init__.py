"""Spatial utilities: MapFrame, projection, raster helpers."""

from .map_frame import MapFrame, create_map_frame, utm_zone_for_lon
from .raster import (
    RasterConvention,
    decode_terrarium_tile,
    encode_terrarium_tile,
    reproject_raster,
    align_raster,
    nodata_mask,
)

__all__ = [
    "MapFrame",
    "create_map_frame",
    "utm_zone_for_lon",
    "RasterConvention",
    "decode_terrarium_tile",
    "encode_terrarium_tile",
    "reproject_raster",
    "align_raster",
    "nodata_mask",
]
