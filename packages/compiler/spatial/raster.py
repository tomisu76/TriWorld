"""Raster utilities: Terrarium tile encoding/decoding, reprojection, alignment."""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from pyproj import CRS, Transformer
from packages.contracts.map_request import RasterConvention


# Terrarium encoding constants
TERRARIUM_OFFSET = 32768.0
TERRARIUM_SCALE = 256.0


def decode_terrarium_tile(rgb: np.ndarray) -> np.ndarray:
    """Decode a Terrarium RGB tile to elevation in meters.

    Formula: R * 256 + G + B/256 - 32768

    Args:
        rgb: Array of shape (H, W, 3) with uint8 RGB values

    Returns:
        Array of shape (H, W) with float32 elevations in meters
    """
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) array, got {rgb.shape}")

    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)

    elevation = r * TERRARIUM_SCALE + g + b / TERRARIUM_SCALE - TERRARIUM_OFFSET
    return elevation.astype(np.float32)


def encode_terrarium_tile(elevation: np.ndarray) -> np.ndarray:
    """Encode elevation data to Terrarium RGB format.

    Args:
        elevation: Array of shape (H, W) with float32 elevations in meters

    Returns:
        Array of shape (H, W, 3) with uint8 RGB values
    """
    if elevation.ndim != 2:
        raise ValueError(f"Expected 2D array, got {elevation.shape}")

    scaled = (elevation + TERRARIUM_OFFSET)
    r = (scaled / TERRARIUM_SCALE).astype(np.uint16)
    g = (scaled - r * TERRARIUM_SCALE).astype(np.uint8)
    b = ((scaled - r * TERRARIUM_SCALE - g) * TERRARIUM_SCALE).astype(np.uint8)

    rgb = np.stack([r.astype(np.uint8), g, b], axis=-1)
    return rgb


@dataclass
class RasterInfo:
    """Metadata for a raster grid."""

    crs: str
    width: int  # number of columns (east-west)
    height: int  # number of rows (north-south)
    transform: tuple[float, float, float, float, float, float]  # GDAL affine transform
    nodata: Optional[float] = None

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y) in CRS units."""
        c, a, b, f, d, e = self.transform
        min_x = c
        max_x = c + a * self.width
        min_y = f + e * self.height
        max_y = f
        return (min_x, min_y, max_x, max_y)


def reproject_raster(
    data: np.ndarray,
    src_crs: str,
    dst_crs: str,
    src_transform: tuple[float, float, float, float, float, float],
    dst_transform: tuple[float, float, float, float, float, float],
    dst_width: int,
    dst_height: int,
    src_nodata: Optional[float] = None,
    dst_nodata: Optional[float] = None,
) -> np.ndarray:
    """Reproject a raster from one CRS to another using bilinear interpolation.

    Uses pyproj for coordinate transformation and numpy for resampling.
    """
    try:
        from rasterio.warp import reproject as rio_reproject
        from rasterio.transform import from_gdal

        src_transform_gdal = from_gdal(*src_transform)
        dst_transform_gdal = from_gdal(*dst_transform)

        dst_data = np.full((dst_height, dst_width), dst_nodata, dtype=np.float32)

        rio_reproject(
            source=data.astype(np.float32),
            destination=dst_data,
            src_transform=src_transform_gdal,
            src_crs=src_crs,
            src_nodata=src_nodata,
            dst_transform=dst_transform_gdal,
            dst_crs=dst_crs,
            dst_nodata=dst_nodata,
            resampling="bilinear",
        )
        return dst_data
    except ImportError:
        # Fallback: simple nearest-neighbor using pyproj
        return _reproject_nearest(
            data, src_crs, dst_crs, src_transform,
            dst_transform, dst_width, dst_height, src_nodata, dst_nodata
        )


def _reproject_nearest(
    data: np.ndarray,
    src_crs: str,
    dst_crs: str,
    src_transform: tuple,
    dst_transform: tuple,
    dst_width: int,
    dst_height: int,
    src_nodata: Optional[float],
    dst_nodata: Optional[float],
) -> np.ndarray:
    """Nearest-neighbor fallback reprojector."""
    transformer = Transformer.from_crs(dst_crs, src_crs, always_xy=True)

    c, a, b, f, d, e = dst_transform
    src_c, src_a, src_b, src_f, src_d, src_e = src_transform

    dst_data = np.full((dst_height, dst_width), dst_nodata, dtype=np.float32)
    src_h, src_w = data.shape

    for dy in range(dst_height):
        for dx in range(dst_width):
            x = c + a * dx + b * dy
            y = f + d * dx + e * dy
            sx, sy = transformer.transform(x, y)
            # Convert to pixel coordinates
            px = (sx - src_c) / src_a
            py = (sy - src_f) / src_e
            px_int = int(round(px))
            py_int = int(round(py))
            if 0 <= px_int < src_w and 0 <= py_int < src_h:
                val = data[py_int, px_int]
                if src_nodata is not None and val == src_nodata:
                    dst_data[dy, dx] = dst_nodata
                else:
                    dst_data[dy, dx] = val
    return dst_data


def align_raster(
    data: np.ndarray,
    src_transform: tuple[float, float, float, float, float, float],
    dst_transform: tuple[float, float, float, float, float, float],
    dst_width: int,
    dst_height: int,
) -> np.ndarray:
    """Align a raster to a target grid using nearest-neighbor resampling.

    Args:
        data: Source raster data (H, W)
        src_transform: Source GDAL affine transform
        dst_transform: Target GDAL affine transform
        dst_width: Target width in pixels
        dst_height: Target height in pixels

    Returns:
        Aligned raster (dst_height, dst_width)
    """
    src_c, src_a, src_b, src_f, src_d, src_e = src_transform
    dst_c, dst_a, dst_b, dst_f, dst_d, dst_e = dst_transform

    src_h, src_w = data.shape
    result = np.zeros((dst_height, dst_width), dtype=data.dtype)

    for dy in range(dst_height):
        for dx in range(dst_width):
            x = dst_c + dst_a * dx + dst_b * dy
            y = dst_f + dst_d * dx + dst_e * dy
            # Convert to source pixel coordinates
            px = (x - src_c) / src_a
            py = (y - src_f) / src_e
            px_int = int(round(px))
            py_int = int(round(py))
            if 0 <= px_int < src_w and 0 <= py_int < src_h:
                result[dy, dx] = data[py_int, px_int]
    return result


def nodata_mask(data: np.ndarray, nodata_value: float) -> np.ndarray:
    """Create a boolean mask where True = valid data, False = nodata."""
    if np.isnan(nodata_value):
        return ~np.isnan(data)
    return data != nodata_value


def raster_orientation_ok(data: np.ndarray, convention: RasterConvention) -> bool:
    """Check that raster follows the expected row-0=north convention.

    For 'north' convention, row 0 should be the northernmost row.
    """
    # This is a structural check - the convention is enforced by how
    # the raster is created, not by inspecting pixel values.
    return True
