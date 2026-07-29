"""Tests for spatial utilities: MapFrame, raster operations."""

import math
import numpy as np
import pytest

from packages.compiler.spatial import (
    MapFrame,
    create_map_frame,
    utm_zone_for_lon,
    decode_terrarium_tile,
    encode_terrarium_tile,
    reproject_raster,
    align_raster,
    nodata_mask,
)
from packages.compiler.spatial.map_frame import select_projection, wgs84_to_local, local_to_wgs84


class TestUtmZone:
    def test_utm_zone_for_lon(self):
        """Test UTM zone computation."""
        # UTM zone formula: int((lon + 180) / 6) + 1
        assert utm_zone_for_lon(0.0) == 31  # (0+180)/6 = 30, +1 = 31
        assert utm_zone_for_lon(14.0) == 33  # (14+180)/6 = 32.33, int=32, +1=33
        assert utm_zone_for_lon(-74.0) == 18  # (-74+180)/6 = 17.67, int=17, +1=18
        assert utm_zone_for_lon(179.0) == 60  # (179+180)/6 = 59.83, int=59, +1=60

    def test_utm_zone_range(self):
        """Test UTM zone is in valid range 1-60."""
        for lon in np.linspace(-180, 179, 37):
            zone = utm_zone_for_lon(lon)
            assert 1 <= zone <= 60


class TestMapFrame:
    def test_create_map_frame_utm(self):
        """Test MapFrame creation for a UTM-projectable area."""
        mf = create_map_frame(48.85, 2.35, 1000, 1000)
        assert mf.sourceCrs == "EPSG:4326"
        assert mf.projectionChoice.startswith("utm_zone_")
        assert mf.anchorLonLat == [2.35, 48.85]
        assert len(mf.anchorProjectedM) == 2
        assert len(mf.localOriginProjectedM) == 2

    def test_create_map_frame_laea_fallback(self):
        """Test MapFrame creation near poles (Equal Earth fallback)."""
        mf = create_map_frame(85.0, 0.0, 1000, 1000)
        assert mf.projectionChoice == "equal_earth"

    def test_create_map_frame_cross_zone(self):
        """Test MapFrame creation for a large area crossing UTM zones."""
        # 50km wide area at zone boundary (lon=9, zone 30/31 boundary)
        # zone 31 center is at lon=9 (31*6-183=3), half-width=3
        # 50km at lat=48 is about 0.5 degrees, so 0.25 deg from center
        # 9 - 3 = 6 > 3 - 0.5 = 2.5, so crosses zone
        mf = create_map_frame(48.0, 9.0, 50000, 1000)
        # With 50km extent, it should cross zone boundary
        assert mf.projectionChoice in ("equal_earth", "utm_zone_31N", "utm_zone_32N")

    def test_select_projection_utm(self):
        """Test projection selection for a small UTM area."""
        result = select_projection(48.85, 2.35, 1000, 1000)
        assert result.projection_choice.startswith("utm_zone_")
        assert result.crs is not None

    def test_select_projection_laea(self):
        """Test projection selection for polar region."""
        result = select_projection(85.0, 0.0, 1000, 1000)
        assert result.projection_choice == "equal_earth"

    def test_wgs84_to_local_and_back(self):
        """Test round-trip: WGS84 -> local -> WGS84."""
        mf = create_map_frame(48.85, 2.35, 1000, 1000)
        lon, lat = 2.351, 48.851
        x, y = wgs84_to_local(mf, lon, lat)
        lon2, lat2 = local_to_wgs84(mf, x, y)
        assert abs(lon - lon2) < 1e-6
        assert abs(lat - lat2) < 1e-6

    def test_map_frame_has_required_fields(self):
        """Test that MapFrame has all required contract fields."""
        mf = create_map_frame(40.0, -74.0, 2000, 2000)
        assert mf.schemaVersion == "1.0"
        assert mf.sourceCrs == "EPSG:4326"
        assert mf.projectedCrsWkt2 is not None
        assert mf.projectionChoice is not None
        assert len(mf.anchorLonLat) == 2
        assert len(mf.anchorProjectedM) == 2
        assert len(mf.localOriginProjectedM) == 2
        assert mf.axisConvention.x == "east"
        assert mf.axisConvention.y == "north"
        assert mf.axisConvention.z == "up"
        assert mf.verticalDatum.name is not None
        assert mf.rasterConvention.row0 == "north"


class TestTerrarium:
    def test_decode_terrarium_basic(self):
        """Test basic Terrarium decode.

        Formula: R*256 + G + B/256 - 32768
        For elevation 0: R=128, G=0, B=0 -> 128*256 + 0 + 0 - 32768 = 0
        """
        rgb = np.array([[[128, 0, 0]]], dtype=np.uint8)
        elev = decode_terrarium_tile(rgb)
        assert abs(elev[0, 0]) < 1.0

    def test_decode_terrarium_positive(self):
        """Test Terrarium decode for positive elevation."""
        # Elevation 100: 100 + 32768 = 32868 -> R=128, G=100, B=0
        # 128*256 + 100 + 0 - 32768 = 32768 + 100 - 32768 = 100
        rgb = np.array([[[128, 100, 0]]], dtype=np.uint8)
        elev = decode_terrarium_tile(rgb)
        assert abs(elev[0, 0] - 100.0) < 1.0

    def test_decode_terrarium_negative(self):
        """Test Terrarium decode for negative elevation."""
        # Elevation -100: -100 + 32768 = 32668 -> R=127, G=156, B=0
        # 127*256 + 156 + 0 - 32768 = 32512 + 156 - 32768 = -100
        rgb = np.array([[[127, 156, 0]]], dtype=np.uint8)
        elev = decode_terrarium_tile(rgb)
        assert abs(elev[0, 0] - (-100.0)) < 1.0

    def test_decode_terrarium_array(self):
        """Test Terrarium decode for a 2D array."""
        rgb = np.zeros((10, 10, 3), dtype=np.uint8)
        rgb[:, :, 0] = 128  # elevation 0
        elev = decode_terrarium_tile(rgb)
        assert elev.shape == (10, 10)
        assert np.allclose(elev, 0.0, atol=1.0)

    def test_decode_terrarium_invalid_shape(self):
        """Test that invalid shapes raise ValueError."""
        rgb = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError):
            decode_terrarium_tile(rgb)

    def test_encode_decode_roundtrip(self):
        """Test that encode -> decode is approximately identity."""
        original = np.array([[0.0, 100.0, -100.0], [50.0, -50.0, 200.0]], dtype=np.float32)
        rgb = encode_terrarium_tile(original)
        decoded = decode_terrarium_tile(rgb)
        # Terrarium has 1m resolution
        assert np.allclose(decoded, original, atol=1.0)

    def test_decode_terrarium_multi_pixel(self):
        """Test decoding a multi-pixel tile."""
        rgb = np.array([
            [[128, 0, 0], [128, 100, 0]],
            [[127, 156, 0], [128, 200, 0]],
        ], dtype=np.uint8)
        elev = decode_terrarium_tile(rgb)
        assert elev.shape == (2, 2)
        assert abs(elev[0, 0]) < 1.0  # ~0
        assert abs(elev[0, 1] - 100.0) < 1.0
        assert abs(elev[1, 0] - (-100.0)) < 1.0
        assert abs(elev[1, 1] - 200.0) < 1.0


class TestRaster:
    def test_nodata_mask(self):
        """Test nodata mask creation."""
        data = np.array([[1.0, -9999.0], [3.0, -9999.0]], dtype=np.float32)
        mask = nodata_mask(data, -9999.0)
        assert mask[0, 0] == True
        assert mask[0, 1] == False
        assert mask[1, 0] == True
        assert mask[1, 1] == False

    def test_nodata_mask_nan(self):
        """Test nodata mask with NaN."""
        data = np.array([[1.0, np.nan], [3.0, np.nan]], dtype=np.float32)
        mask = nodata_mask(data, float("nan"))
        assert mask[0, 0] == True
        assert mask[0, 1] == False
        assert mask[1, 0] == True
        assert mask[1, 1] == False

    def test_align_raster(self):
        """Test raster alignment to a target grid."""
        # Source: 4x4 grid with values 0-15
        data = np.arange(16, dtype=np.float32).reshape(4, 4)
        # Source transform: top-left at (0, 4), pixel size 1
        # GDAL: (c, a, b, f, d, e) where c=top-left x, f=top-left y, a=x pixel, e=y pixel (negative)
        src_transform = (0.0, 1.0, 0.0, 4.0, 0.0, -1.0)
        # Target: 2x2 grid, same area
        dst_transform = (0.0, 2.0, 0.0, 4.0, 0.0, -2.0)
        result = align_raster(data, src_transform, dst_transform, 2, 2)
        assert result.shape == (2, 2)
        # Top-left of dst maps to (0, 4) in src -> pixel (0, 0) -> data[0, 0] = 0
        assert result[0, 0] == data[0, 0]
        # Bottom-right of dst maps to (2, 2) in src -> pixel (2, 2) -> data[2, 2] = 10
        assert result[1, 1] == data[2, 2]
