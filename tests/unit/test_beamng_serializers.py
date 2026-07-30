import tempfile
import numpy as np
from pathlib import Path

from packages.compiler.beamng_serializers import (
    TerWriter, DaeSerializer,
    create_flat_terrain_ter, create_straight_road_dae
)


def test_ter_writer():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.ter"
        writer = TerWriter(size=256, square_size=2.0, max_height=500.0)
        writer.add_material("asphalt")

        height_map, layer_map = create_flat_terrain_ter(256)
        writer.write(path, height_map, layer_map)

        assert path.exists()
        assert path.stat().st_size > 0

        # Read back and verify header (version 9)
        with open(path, 'rb') as f:
            version = f.read(1)[0]
            assert version == 9  # BeamNG 0.38.6 uses version 9

            size = int.from_bytes(f.read(4), 'little')
            assert size == 256

            # Height map: 256*256*2 bytes
            height_bytes = f.read(256 * 256 * 2)
            assert len(height_bytes) == 256 * 256 * 2

            # Layer map: 256*256 bytes
            layer_bytes = f.read(256 * 256)
            assert len(layer_bytes) == 256 * 256

            # Material count
            mat_count = int.from_bytes(f.read(4), 'little')
            assert mat_count == 1

            # Material name length (u8)
            name_len = f.read(1)[0]
            assert name_len == len("asphalt")

            name = f.read(name_len).decode('utf-8')
            assert name == "asphalt"


def test_ter_writer_name_validation():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_val.ter"
        writer = TerWriter(size=128)
        writer.add_material("")
        hm, lm = create_flat_terrain_ter(128)
        import pytest
        with pytest.raises(ValueError, match="empty"):
            writer.write(path, hm, lm)

        writer2 = TerWriter(size=128)
        writer2.add_material("a" * 256)
        with pytest.raises(ValueError, match="exceeds maximum"):
            writer2.write(path, hm, lm)


def test_dae_serializer():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "road_chunk.dae"

        positions = [[0, 0, 0], [10, 0, 0], [10, 7, 0], [0, 7, 0]]
        normals = [[0, 0, 1]] * 4
        uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        indices = [0, 1, 2, 0, 2, 3]
        bounds = {'min': [0, 0, 0], 'max': [10, 7, 0]}

        DaeSerializer.write_road_chunk(
            path=path,
            mesh_id="road_chunk_001",
            positions=positions,
            normals=normals,
            uvs=uvs,
            indices=indices,
            material_name="asphalt",
            bounds=bounds,
        )

        assert path.exists()

        # Verify it's valid XML
        import xml.etree.ElementTree as ET
        tree = ET.parse(path)
        root = tree.getroot()
        assert root.tag.endswith('COLLADA')

        # Check for key elements
        geometries = root.findall('.//{http://www.collada.org/2005/11/COLLADASchema}geometry')
        assert len(geometries) == 1


def test_create_straight_road_dae():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "straight_road.dae"
        bounds = create_straight_road_dae(path, "straight_road", length=500.0, width=7.0)

        assert path.exists()
        assert bounds['min'][0] == 0.0  # start of road
        assert bounds['max'][0] == 500.0  # end of road
        assert bounds['min'][1] == -3.5  # half width (left edge)
        assert bounds['max'][1] == 3.5   # half width (right edge)
        assert bounds['max'][2] == 0.0


def test_ter_quantization():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_quant.ter"
        max_h = 100.0
        writer = TerWriter(size=128, square_size=2.0, max_height=max_h)

        # Create heightmap with specific test values
        # [0.0, max_h, max_h/2, -10.0, max_h + 10.0]
        hm = np.zeros((128, 128), dtype=np.float32)
        hm[0, 0] = 0.0            # should be 0
        hm[0, 1] = max_h          # should be 65535
        hm[0, 2] = max_h / 2.0    # should be ~32768
        hm[0, 3] = -10.0          # should clamp to 0
        hm[0, 4] = max_h + 10.0   # should clamp to 65535

        lm = np.zeros((128, 128), dtype=np.uint8)

        writer.write(path, hm, lm)

        with open(path, 'rb') as f:
            f.seek(1 + 4)  # Skip version (1) and size (4)
            # Read first 5 uint16 values
            import struct
            v1 = struct.unpack('<H', f.read(2))[0]
            v2 = struct.unpack('<H', f.read(2))[0]
            v3 = struct.unpack('<H', f.read(2))[0]
            v4 = struct.unpack('<H', f.read(2))[0]
            v5 = struct.unpack('<H', f.read(2))[0]

            assert v1 == 0, f"0.0 encodes to {v1}, expected 0"
            assert v2 == 65535, f"maxHeight encodes to {v2}, expected 65535"
            assert abs(v3 - 32768) <= 1, f"maxHeight/2 encodes to {v3}, expected ~32768"
            assert v4 == 0, f"Negative input encodes to {v4}, expected 0"
            assert v5 == 65535, f"Above maxHeight encodes to {v5}, expected 65535"


def test_flat_canary_ter_is_zero():
    # generated flat canary .ter contains only zero height samples
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_flat.ter"
        writer = TerWriter(size=128, square_size=2.0, max_height=100.0)
        hm, lm = create_flat_terrain_ter(128)

        # Verify hm contains only 0.0
        assert np.all(hm == 0.0), "flat canary input contains non-zero heights"

        writer.write(path, hm, lm)

        with open(path, 'rb') as f:
            f.seek(1 + 4)
            height_bytes = f.read(128 * 128 * 2)
            import struct
            heights = struct.unpack(f'<{128*128}H', height_bytes)
            assert all(h == 0 for h in heights), "flat canary encoded output contains non-zero samples"


if __name__ == "__main__":
    test_ter_writer()
    print("test_ter_writer passed")
    test_dae_serializer()
    print("test_dae_serializer passed")
    test_create_straight_road_dae()
    print("test_create_straight_road_dae passed")
    test_ter_quantization()
    print("test_ter_quantization passed")
    test_flat_canary_ter_is_zero()
    print("test_flat_canary_ter_is_zero passed")