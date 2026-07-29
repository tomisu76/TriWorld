"""DEM resolver: fetch, cache, and mosaic Terrarium-format DEM tiles.

Supports Mapzen Terrarium tiles (32-bit RGB PNG) and user-provided GeoTIFF.
Caches tiles locally with SHA-256 verification.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple

import httpx
import numpy as np
from PIL import Image

from packages.compiler.spatial.raster import (
    RasterInfo,
    decode_terrarium_tile,
    encode_terrarium_tile,
)
from packages.contracts.terrain_mesh_beamng import DemArtifact, VerticalDatumType


# Terrarium tile constants
TILE_SIZE = 256  # pixels
EARTH_RADIUS_M = 6378137.0
INITIAL_RESOLUTION = 2.0 * math.pi * EARTH_RADIUS_M / TILE_SIZE  # ~156543.03


@dataclass
class TileCoord:
    """XYZ tile coordinate."""

    x: int
    y: int
    z: int

    def to_key(self) -> str:
        return f"{self.z}/{self.x}/{self.y}"


def lonlat_to_tile(lon: float, lat: float, zoom: int) -> TileCoord:
    """Convert WGS84 lon/lat to XYZ tile coordinate."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return TileCoord(x=x, y=y, z=zoom)


def tile_to_lonlat(tile: TileCoord) -> Tuple[float, float]:
    """Convert XYZ tile coordinate to WGS84 lon/lat (center of tile)."""
    n = 2.0 ** tile.z
    lon = tile.x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * tile.y / n)))
    lat = math.degrees(lat_rad)
    return (lon, lat)


def tile_bounds(tile: TileCoord) -> Tuple[float, float, float, float]:
    """Return (min_lon, min_lat, max_lon, max_lat) for a tile."""
    n = 2.0 ** tile.z
    min_lon = tile.x / n * 360.0 - 180.0
    max_lon = (tile.x + 1) / n * 360.0 - 180.0
    min_lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (tile.y + 1) / n)))
    max_lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * tile.y / n)))
    min_lat = math.degrees(min_lat_rad)
    max_lat = math.degrees(max_lat_rad)
    return (min_lon, min_lat, max_lon, max_lat)


@dataclass
class DemSource:
    """Configuration for a DEM data source."""

    name: str
    url_template: str  # e.g., "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
    format: str  # "terrarium" or "geotiff"
    license: str = "CC0-1.0"


# Predefined sources
MAPZEN_TERRARIUM = DemSource(
    name="mapzen-terrarium",
    url_template="https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
    format="terrarium",
    license="CC0-1.0",
)

OPEN_TOPOGRAPHY = DemSource(
    name="opentopography",
    url_template="https://opentopography.s3.amazonaws.com/{z}/{x}/{y}.png",
    format="terrarium",
    license="CC-BY-4.0",
)


class DemResolver:
    """Fetch and cache DEM tiles with retry/backoff."""

    def __init__(
        self,
        cache_dir: Path,
        sources: Optional[List[DemSource]] = None,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        timeout: float = 30.0,
    ):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sources = sources or [MAPZEN_TERRARIUM]
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout, follow_redirects=True)
        return self._client

    def _tile_cache_path(self, source: DemSource, tile: TileCoord) -> Path:
        """Return the cache path for a tile."""
        return self.cache_dir / source.name / str(tile.z) / str(tile.x) / f"{tile.y}.png"

    def _tile_hash_path(self, source: DemSource, tile: TileCoord) -> Path:
        """Return the hash file path for a tile."""
        return self._tile_cache_path(source, tile).with_suffix(".sha256")

    def _compute_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def is_tile_cached(self, source: DemSource, tile: TileCoord) -> bool:
        """Check if a tile is cached and valid."""
        cache_path = self._tile_cache_path(source, tile)
        hash_path = self._tile_hash_path(source, tile)
        if not cache_path.exists() or not hash_path.exists():
            return False
        expected_hash = hash_path.read_text().strip()
        actual_hash = self._compute_hash(cache_path.read_bytes())
        return expected_hash == actual_hash

    def _fetch_tile_with_retry(self, source: DemSource, tile: TileCoord) -> bytes:
        """Fetch a single tile with retry and backoff."""
        url = source.url_template.format(z=tile.z, x=tile.x, y=tile.y)
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                return response.content
            except (httpx.HTTPError, httpx.RequestError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.backoff_base * (2 ** attempt)
                    time.sleep(delay)

        raise RuntimeError(f"Failed to fetch tile {tile.to_key()} from {source.name}: {last_error}")

    def fetch_tile(self, source: DemSource, tile: TileCoord) -> bytes:
        """Fetch a tile, using cache if available."""
        if self.is_tile_cached(source, tile):
            cache_path = self._tile_cache_path(source, tile)
            return cache_path.read_bytes()

        data = self._fetch_tile_with_retry(source, tile)

        # Cache the tile
        cache_path = self._tile_cache_path(source, tile)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
        hash_path = self._tile_hash_path(source, tile)
        hash_path.write_text(self._compute_hash(data))

        return data

    def fetch_tile_as_array(self, source: DemSource, tile: TileCoord) -> np.ndarray:
        """Fetch a tile and decode it to a numpy array."""
        data = self.fetch_tile(source, tile)
        img = Image.open(Path(data) if isinstance(data, bytes) else data)
        rgb = np.array(img.convert("RGB"), dtype=np.uint8)

        if source.format == "terrarium":
            return decode_terrarium_tile(rgb)
        else:
            raise ValueError(f"Unsupported DEM format: {source.format}")

    def fetch_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        zoom: int = 14,
    ) -> Tuple[np.ndarray, RasterInfo]:
        """Fetch DEM tiles covering a bounding box and mosaic them.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            zoom: Tile zoom level (default 14)

        Returns:
            (elevation_array, RasterInfo)
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        # Get tile range
        min_tile = lonlat_to_tile(min_lon, min_lat, zoom)
        max_tile = lonlat_to_tile(max_lon, max_lat, zoom)

        # Ensure min < max
        min_tx = min(min_tile.x, max_tile.x)
        max_tx = max(min_tile.x, max_tile.x)
        min_ty = min(min_tile.y, max_tile.y)
        max_ty = max(min_tile.y, max_tile.y)

        # Fetch all tiles
        tiles_data: List[np.ndarray] = []
        tile_coords: List[TileCoord] = []

        for ty in range(min_ty, max_ty + 1):
            for tx in range(min_tx, max_tx + 1):
                tile = TileCoord(x=tx, y=ty, z=zoom)
                try:
                    arr = self.fetch_tile_as_array(self.sources[0], tile)
                    tiles_data.append(arr)
                    tile_coords.append(tile)
                except Exception:
                    # Create a nodata tile
                    nodata_arr = np.full((TILE_SIZE, TILE_SIZE), -9999.0, dtype=np.float32)
                    tiles_data.append(nodata_arr)
                    tile_coords.append(tile)

        # Mosaic tiles
        n_cols = max_tx - min_tx + 1
        n_rows = max_ty - min_ty + 1
        mosaic = np.full((n_rows * TILE_SIZE, n_cols * TILE_SIZE), -9999.0, dtype=np.float32)

        for i, (arr, tile) in enumerate(zip(tiles_data, tile_coords)):
            col_idx = tile.x - min_tx
            row_idx = tile.y - min_ty
            y_start = row_idx * TILE_SIZE
            x_start = col_idx * TILE_SIZE
            mosaic[y_start:y_start + TILE_SIZE, x_start:x_start + TILE_SIZE] = arr

        # Compute raster info
        bounds = tile_bounds(TileCoord(x=min_tx, y=min_ty, z=zoom))
        min_tile_bounds = tile_bounds(TileCoord(x=min_tx, y=min_ty, z=zoom))
        max_tile_bounds = tile_bounds(TileCoord(x=max_tx, y=max_ty, z=zoom))

        full_bounds = (
            min_tile_bounds[0],  # min_lon
            max_tile_bounds[1],  # min_lat
            max_tile_bounds[2],  # max_lon
            min_tile_bounds[3],  # max_lat
        )

        # GDAL affine transform: (c, a, b, f, d, e)
        # c = top-left x, a = pixel width, b = 0
        # f = top-left y, d = 0, e = -pixel height (negative for north-up)
        lon_span = full_bounds[2] - full_bounds[0]
        lat_span = full_bounds[3] - full_bounds[1]
        pixel_width = lon_span / (n_cols * TILE_SIZE)
        pixel_height = lat_span / (n_rows * TILE_SIZE)

        transform = (
            full_bounds[0],  # c: top-left lon
            pixel_width,     # a: pixel width in degrees
            0.0,             # b
            full_bounds[3],  # f: top-left lat
            0.0,             # d
            -pixel_height,   # e: negative for north-up
        )

        info = RasterInfo(
            crs="EPSG:4326",
            width=n_cols * TILE_SIZE,
            height=n_rows * TILE_SIZE,
            transform=transform,
            nodata=-9999.0,
        )

        return mosaic, info

    def create_dem_artifact(
        self,
        source: DemSource,
        tile: TileCoord,
        elevation: np.ndarray,
        bounds: Tuple[float, float, float, float],
    ) -> DemArtifact:
        """Create a DemArtifact contract for a fetched tile."""
        data = elevation.tobytes()
        return DemArtifact(
            path=f"cache/dem/{source.name}/{tile.to_key()}.npy",
            crs="EPSG:4326",
            verticalDatum=VerticalDatumType.ELLIPSOIDAL,
            resolution=TILE_SIZE,
            nodata=-9999.0,
            bbox=[bounds[0], bounds[1], bounds[2], bounds[3]],
            hash=self._compute_hash(data),
        )

    def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None
