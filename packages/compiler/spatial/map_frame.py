"""MapFrame: WGS84 -> local projected coordinate system.

Handles UTM zone selection, LAEA fallback for cross-zone spans,
and creates a MapFrame contract for the pipeline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from pyproj import CRS, Transformer
from packages.contracts.map_request import (
    AxisConvention,
    MapFrame,
    RasterConvention,
    VerticalDatum,
)


def utm_zone_for_lon(lon: float) -> int:
    """Return the UTM zone number (1-60) for a given longitude."""
    return int((lon + 180.0) / 6.0) + 1


def _utm_crs(zone: int, hemisphere: str) -> CRS:
    """Build a UTM CRS for the given zone and hemisphere ('N' or 'S')."""
    epsg = 32600 + zone if hemisphere.upper() == "N" else 32700 + zone
    return CRS.from_epsg(epsg)


def _lae_crs(lat_0: float, lon_0: float) -> CRS:
    """Build an Equal Earth CRS centered on (lat_0, lon_0)."""
    return CRS.from_proj4(
        f"+proj=eqearth +lat_0={lat_0} +lon_0={lon_0} +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    )


@dataclass
class ProjectionResult:
    """Result of projection selection."""

    crs: CRS
    crs_wkt2: str
    projection_choice: str
    transformer_to_local: Transformer
    transformer_to_wgs84: Transformer


def select_projection(
    center_lat: float,
    center_lon: float,
    extent_width_m: float,
    extent_height_m: float,
) -> ProjectionResult:
    """Select an appropriate projected CRS for the given area.

    Uses UTM if the area fits within a single zone with sufficient margin.
    Falls back to Equal Earth for cross-zone or polar regions.
    """
    zone = utm_zone_for_lon(center_lon)
    hemisphere = "N" if center_lat >= 0 else "S"
    utm = _utm_crs(zone, hemisphere)

    # Check if center point projects well into UTM and area doesn't cross zone boundary
    half_width = extent_width_m / 2.0
    half_height = extent_height_m / 2.0

    # UTM zone is 6 degrees wide; check if area stays within zone
    degrees_per_zone = 6.0
    zone_center_lon = zone * 6.0 - 183.0  # center longitude of the zone
    zone_half_width_deg = degrees_per_zone / 2.0

    # Approximate degrees per meter at this latitude
    degrees_per_meter_lon = 1.0 / (111320.0 * math.cos(math.radians(center_lat)))
    degrees_per_meter_lat = 1.0 / 110574.0

    extent_half_width_deg = half_width * degrees_per_meter_lon
    extent_half_height_deg = half_height * degrees_per_meter_lat

    # Check if area crosses zone boundary or extends beyond zone
    crosses_zone = (
        abs(center_lon - zone_center_lon) + extent_half_width_deg > zone_half_width_deg - 0.5
    )

    # Check if near poles (UTM is undefined at poles)
    near_pole = abs(center_lat) > 84.0

    if crosses_zone or near_pole:
        crs = _lae_crs(center_lat, center_lon)
        projection_choice = "equal_earth"
    else:
        crs = utm
        projection_choice = f"utm_zone_{zone}{hemisphere}"

    transformer_to_local = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    transformer_to_wgs84 = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    return ProjectionResult(
        crs=crs,
        crs_wkt2=crs.to_wkt(),
        projection_choice=projection_choice,
        transformer_to_local=transformer_to_local,
        transformer_to_wgs84=transformer_to_wgs84,
    )


def create_map_frame(
    center_lat: float,
    center_lon: float,
    extent_width_m: float,
    extent_height_m: float,
    vertical_datum_name: str = "wgs84_ellipsoid",
) -> MapFrame:
    """Create a MapFrame contract for the given geographic area.

    Args:
        center_lat: Center latitude in degrees
        center_lon: Center longitude in degrees
        extent_width_m: Width of the area in meters (east-west)
        extent_height_m: Height of the area in meters (north-south)
        vertical_datum_name: Name of the vertical datum

    Returns:
        MapFrame contract with projection info
    """
    proj = select_projection(center_lat, center_lon, extent_width_m, extent_height_m)

    # Project the center point to local coordinates
    cx_local, cy_local = proj.transformer_to_local.transform(center_lon, center_lat)

    # Project the corners to get the projected bounding box
    half_w = extent_width_m / 2.0
    half_h = extent_height_m / 2.0

    # Approximate corner projection (using center + offsets in local space)
    # The local origin is at the projected center
    local_origin_x = cx_local - half_w
    local_origin_y = cy_local - half_h

    return MapFrame(
        schemaVersion="1.0",
        sourceCrs="EPSG:4326",
        projectedCrsWkt2=proj.crs_wkt2,
        projectionChoice=proj.projection_choice,
        anchorLonLat=[center_lon, center_lat],
        anchorProjectedM=[cx_local, cy_local],
        localOriginProjectedM=[local_origin_x, local_origin_y],
        axisConvention=AxisConvention(),
        verticalDatum=VerticalDatum(name=vertical_datum_name),
        rasterConvention=RasterConvention(),
    )


def wgs84_to_local(
    map_frame: MapFrame,
    lon: float,
    lat: float,
) -> tuple[float, float]:
    """Transform WGS84 lon/lat to local projected coordinates."""
    crs = CRS.from_wkt(map_frame.projectedCrsWkt2)
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    # Adjust for local origin offset
    ox, oy = map_frame.localOriginProjectedM
    return (x - ox, y - oy)


def local_to_wgs84(
    map_frame: MapFrame,
    x: float,
    y: float,
) -> tuple[float, float]:
    """Transform local projected coordinates to WGS84 lon/lat."""
    crs = CRS.from_wkt(map_frame.projectedCrsWkt2)
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    ox, oy = map_frame.localOriginProjectedM
    lon, lat = transformer.transform(x + ox, y + oy)
    return (lon, lat)
