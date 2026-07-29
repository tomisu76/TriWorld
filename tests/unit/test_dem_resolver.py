"""Tests for DEM resolver: tile coordinates, Terrarium decoding, caching."""

import tempfile
import numpy as np
import pytest
from pathlib import Path

from packages.compiler.dem_resolver import (
    DemResolver,
    DemSource,
    TileCoord,
    lonlat_to_tile,
    tile_to_lonlat,
    tile_bounds,
    MAPZEN_TERRARIUM,
    TILE_SIZE,
)


class TestTileCoords:
    def test_lonlat_to_tile(self):
        """Test lon/lat to tile conversion."""
        tile = lonlat_to_tile(0.0, 0.0, 0)
        assert tile.x == 0
        assert tile.y == 0
        assert tile.z == 0

    def test_lonlat_to_tile_zoom14(self):
        """Test lon/lat to tile conversion at zoom 14."""
        tile = lonlat_to_tile(2.35, 48.85, 14)
        assert tile.z == 14
        assert 0 <= tile.x < 2**14
        assert 0 <= tile.y < 2**14

    def test_tile_to_lonlat_roundtrip(self):
        """Test tile -> lon/lat -> tile roundtrip."""
        original = TileCoord(x=8300, y=5400, z=14)
        lon, lat = tile_to_lonlat(original)
        result = lonlat_to_tile(lon, lat, 14)
        assert result.x == original.x
        assert result.y == original.y

    def test_tile_bounds(self):
        """Test tile bounds computation."""
        tile = TileCoord(x=0, y=0, z=1)
        min_lon, min_lat, max_lon, max_lat = tile_bounds(tile)
        assert min_lon == -180.0
        assert max_lon == 0.0
        # For z=1, y=0, the tile covers from ~85.05 to 0 latitude
        assert min_lat < max_lat

    def test_tile_bounds_zoom0(self):
        """Test tile bounds at zoom 0 (entire world)."""
        tile = TileCoord(x=0, y=0, z=0)
        min_lon, min_lat, max_lon, max_lat = tile_bounds(tile)
        assert min_lon == -180.0
        assert max_lon == 180.0
        assert min_lat < 0 < max_lat

    def test_tile_key(self):
        """Test tile key format."""
        tile = TileCoord(x=100, y=200, z=14)
        assert tile.to_key() == "14/100/200"


class TestDemResolver:
    def test_resolver_init(self):
        """Test DemResolver initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir))
            assert resolver.cache_dir == Path(tmpdir)
            assert resolver.max_retries == 3
            resolver.close()

    def test_resolver_cache_path(self):
        """Test cache path computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir))
            tile = TileCoord(x=100, y=200, z=14)
            path = resolver._tile_cache_path(MAPZEN_TERRARIUM, tile)
            assert "mapzen-terrarium" in str(path)
            assert "14" in str(path)
            assert "100" in str(path)
            assert "200.png" in str(path)
            resolver.close()

    def test_resolver_hash_computation(self):
        """Test SHA-256 hash computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir))
            data = b"test data"
            h = resolver._compute_hash(data)
            assert len(h) == 64
            resolver.close()

    def test_resolver_cache_miss(self):
        """Test that cache miss returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir))
            tile = TileCoord(x=100, y=200, z=14)
            assert not resolver.is_tile_cached(MAPZEN_TERRARIUM, tile)
            resolver.close()

    def test_resolver_cache_hit(self):
        """Test that cache hit returns True after caching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir))
            tile = TileCoord(x=100, y=200, z=14)
            cache_path = resolver._tile_cache_path(MAPZEN_TERRARIUM, tile)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            test_data = b"fake png data"
            cache_path.write_bytes(test_data)
            hash_path = resolver._tile_hash_path(MAPZEN_TERRARIUM, tile)
            hash_path.write_text(resolver._compute_hash(test_data))
            assert resolver.is_tile_cached(MAPZEN_TERRARIUM, tile)
            resolver.close()

    def test_resolver_cache_corrupted(self):
        """Test that corrupted cache (hash mismatch) is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir))
            tile = TileCoord(x=100, y=200, z=14)
            cache_path = resolver._tile_cache_path(MAPZEN_TERRARIUM, tile)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(b"fake data")
            hash_path = resolver._tile_hash_path(MAPZEN_TERRARIUM, tile)
            hash_path.write_text("wrong_hash_value")
            assert not resolver.is_tile_cached(MAPZEN_TERRARIUM, tile)
            resolver.close()

    def test_resolver_custom_sources(self):
        """Test DemResolver with custom sources."""
        custom = DemSource(
            name="custom-dem",
            url_template="https://example.com/{z}/{x}/{y}.png",
            format="terrarium",
            license="CC0-1.0",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir), sources=[custom])
            assert len(resolver.sources) == 1
            assert resolver.sources[0].name == "custom-dem"
            resolver.close()

    def test_resolver_bbox_tile_range(self):
        """Test that bbox fetch computes correct tile range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = DemResolver(cache_dir=Path(tmpdir))
            # Small bbox around Paris
            bbox = (2.34, 48.84, 2.36, 48.86)
            # min_lon, max_lat -> min_tile (west, north)
            min_tile = lonlat_to_tile(bbox[0], bbox[3], 14)
            # max_lon, min_lat -> max_tile (east, south)
            max_tile = lonlat_to_tile(bbox[2], bbox[1], 14)
            assert min_tile.x <= max_tile.x
            # Note: y increases southward, so min_lat (south) gives larger y
            # max_lat (north) gives smaller y
            assert min_tile.y <= max_tile.y
