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
        
        height_map, layer_map, layer_texture_map = create_flat_terrain_ter(256)
        writer.write(path, height_map, layer_map, layer_texture_map)
        
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
            
            # Layer texture map: 256*256 bytes (version 9+)
            layer_tex_bytes = f.read(256 * 256)
            assert len(layer_tex_bytes) == 256 * 256
            
            # Material count
            mat_count = int.from_bytes(f.read(4), 'little')
            assert mat_count == 1
            
            # Material name length
            name_len = int.from_bytes(f.read(4), 'little')
            assert name_len == len("asphalt")
            
            name = f.read(name_len).decode('utf-8')
            assert name == "asphalt"


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


if __name__ == "__main__":
    test_ter_writer()
    print("test_ter_writer passed")
    test_dae_serializer()
    print("test_dae_serializer passed")
    test_create_straight_road_dae()
    print("test_create_straight_road_dae passed")