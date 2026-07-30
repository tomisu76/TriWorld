"""BeamNG .ter binary writer and DAE serializer for synthetic canary."""

import struct
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import xml.etree.ElementTree as ET


class TerWriter:
    """Writer for BeamNG .ter binary heightfield format.

    Format (BeamNG 0.38.6, version 9):
    - u8: binaryVersion (9)
    - u32: size (heightmap dimension, power of 2)
    - u16[size*size]: heightMap (16-bit unsigned)
    - u8[size*size]: layerMap (8-bit, 255 = hole)
    - u32: materialCount
    - materialCount * (u8 length + string): materialNames (u8 length-prefixed UTF-8)
    """

    BINARY_VERSION = 9

    def __init__(self, size: int = 256, square_size: float = 2.0, max_height: float = 500.0):
        """
        Args:
            size: Heightmap dimension (must be power of 2, 128-8192)
            square_size: World size of one pixel in meters
            max_height: Maximum height value in meters (for quantization)
        """
        if size < 128 or size > 8192 or (size & (size - 1)) != 0:
            raise ValueError(f"Size must be power of 2 between 128 and 8192, got {size}")
        self.size = size
        self.square_size = square_size
        self.max_height = max_height
        self.material_names: List[str] = []

    def write(self, path: Path, height_map: np.ndarray, layer_map: Optional[np.ndarray] = None):
        """Write .ter file.

        Args:
            path: Output file path
            height_map: 2D array of shape (size, size) with heights in meters
            layer_map: Optional 2D array of shape (size, size) with material indices (0-254, 255=hole)
        """
        if height_map.shape != (self.size, self.size):
            raise ValueError(f"Height map must be {self.size}x{self.size}, got {height_map.shape}")

        if layer_map is None:
            layer_map = np.zeros((self.size, self.size), dtype=np.uint8)
        elif layer_map.shape != (self.size, self.size):
            raise ValueError(f"Layer map must be {self.size}x{self.size}, got {layer_map.shape}")

        # Quantize heights to 16-bit unsigned.
        # .ter height samples are unsigned local heights.
        # TerrainBlock.position.z supplies the terrain base/world offset.
        # negative world elevations must be represented through TerrainBlock.position.z, not negative uint16 samples.
        # Formula: quantized = round(height_map / max_height * 65535)
        quantized = np.clip(
            np.round(height_map / self.max_height * 65535),
            0, 65535
        ).astype(np.uint16)

        with open(path, 'wb') as f:
            # Binary version (u8)
            f.write(struct.pack('B', self.BINARY_VERSION))

            # Size (u32)
            f.write(struct.pack('<I', self.size))

            # Height map (row-major, row 0 = north)
            f.write(quantized.tobytes())

            # Layer map
            f.write(layer_map.astype(np.uint8).tobytes())

            # Material count and names
            f.write(struct.pack('<I', len(self.material_names)))
            for name in self.material_names:
                name_bytes = name.encode('utf-8')
                if len(name_bytes) == 0:
                    raise ValueError(f"Material name cannot be empty, got '{name}'")
                if len(name_bytes) > 255:
                    raise ValueError(f"Material name '{name}' exceeds maximum UTF-8 length of 255 bytes ({len(name_bytes)} bytes)")
                f.write(struct.pack('B', len(name_bytes)))
                f.write(name_bytes)

    def add_material(self, name: str):
        if name not in self.material_names:
            self.material_names.append(name)


class DaeSerializer:
    """Minimal deterministic Collada DAE serializer for road chunks."""

    @staticmethod
    def write_road_chunk(
        path: Path,
        mesh_id: str,
        positions: List[List[float]],
        normals: List[List[float]],
        uvs: List[List[float]],
        indices: List[int],
        material_name: str,
        bounds: dict,
    ):
        """Write a road chunk as Collada DAE.

        Args:
            path: Output .dae file path
            mesh_id: Unique mesh identifier
            positions: List of [x, y, z] vertices
            normals: List of [nx, ny, nz] normals
            uvs: List of [u, v] texture coordinates
            indices: Triangle indices
            material_name: Material name (e.g., "asphalt")
            bounds: {min: [x,y,z], max: [x,y,z]}
        """
        root = ET.Element('COLLADA', {
            'xmlns': 'http://www.collada.org/2005/11/COLLADASchema',
            'version': '1.4.1',
        })

        # Asset info
        asset = ET.SubElement(root, 'asset')
        ET.SubElement(asset, 'unit', {'name': 'meter', 'meter': '1.0'})
        ET.SubElement(asset, 'up_axis').text = 'Z_UP'
        ET.SubElement(asset, 'contributor')

        # 1. Library effects
        lib_fx = ET.SubElement(root, 'library_effects')
        effect = ET.SubElement(lib_fx, 'effect', {'id': f'{material_name}-fx', 'name': material_name})
        profile = ET.SubElement(effect, 'profile_COMMON')
        technique = ET.SubElement(profile, 'technique', {'sid': 'common'})
        phong = ET.SubElement(technique, 'phong')

        emission = ET.SubElement(phong, 'emission')
        color = ET.SubElement(emission, 'color', {'sid': 'emission'})
        color.text = '0 0 0 1'

        ambient = ET.SubElement(phong, 'ambient')
        color = ET.SubElement(ambient, 'color', {'sid': 'ambient'})
        color.text = '0.3 0.3 0.3 1'

        diffuse = ET.SubElement(phong, 'diffuse')
        color = ET.SubElement(diffuse, 'color', {'sid': 'diffuse'})
        color.text = '0.4 0.4 0.4 1'

        specular = ET.SubElement(phong, 'specular')
        color = ET.SubElement(specular, 'color', {'sid': 'specular'})
        color.text = '0.1 0.1 0.1 1'

        shininess = ET.SubElement(phong, 'shininess')
        float_elem = ET.SubElement(shininess, 'float', {'sid': 'shininess'})
        float_elem.text = '10'

        transparency = ET.SubElement(phong, 'transparency')
        float_elem = ET.SubElement(transparency, 'float', {'sid': 'transparency'})
        float_elem.text = '1'

        # 2. Library materials
        lib_mat = ET.SubElement(root, 'library_materials')
        mat = ET.SubElement(lib_mat, 'material', {'id': f'{material_name}-mat', 'name': material_name})
        ET.SubElement(mat, 'instance_effect', {'url': f'#{material_name}-fx'})

        # 3. Library geometries
        lib_geom = ET.SubElement(root, 'library_geometries')
        geom = ET.SubElement(lib_geom, 'geometry', {'id': f'{mesh_id}-geom', 'name': mesh_id})
        mesh = ET.SubElement(geom, 'mesh')

        # Positions source
        pos_src = ET.SubElement(mesh, 'source', {'id': f'{mesh_id}-positions'})
        pos_array = ET.SubElement(pos_src, 'float_array', {
            'id': f'{mesh_id}-positions-array',
            'count': str(len(positions) * 3)
        })
        pos_array.text = ' '.join(f'{v:.6f}' for p in positions for v in p)
        ET.SubElement(pos_src, 'technique_common').append(
            ET.Element('accessor', {
                'source': f'#{mesh_id}-positions-array',
                'count': str(len(positions)),
                'stride': '3'
            })
        )

        # Normals source
        norm_src = ET.SubElement(mesh, 'source', {'id': f'{mesh_id}-normals'})
        norm_array = ET.SubElement(norm_src, 'float_array', {
            'id': f'{mesh_id}-normals-array',
            'count': str(len(normals) * 3)
        })
        norm_array.text = ' '.join(f'{v:.6f}' for n in normals for v in n)
        ET.SubElement(norm_src, 'technique_common').append(
            ET.Element('accessor', {
                'source': f'#{mesh_id}-normals-array',
                'count': str(len(normals)),
                'stride': '3'
            })
        )

        # UV source
        uv_src = ET.SubElement(mesh, 'source', {'id': f'{mesh_id}-uvs'})
        uv_array = ET.SubElement(uv_src, 'float_array', {
            'id': f'{mesh_id}-uvs-array',
            'count': str(len(uvs) * 2)
        })
        uv_array.text = ' '.join(f'{v:.6f}' for uv in uvs for v in uv)
        ET.SubElement(uv_src, 'technique_common').append(
            ET.Element('accessor', {
                'source': f'#{mesh_id}-uvs-array',
                'count': str(len(uvs)),
                'stride': '2'
            })
        )

        # Vertices
        vertices = ET.SubElement(mesh, 'vertices', {'id': f'{mesh_id}-vertices'})
        ET.SubElement(vertices, 'input', {'semantic': 'POSITION', 'source': f'#{mesh_id}-positions'})

        # Triangles
        triangles = ET.SubElement(mesh, 'triangles', {'material': material_name, 'count': str(len(indices) // 3)})
        ET.SubElement(triangles, 'input', {'semantic': 'VERTEX', 'source': f'#{mesh_id}-vertices', 'offset': '0'})
        ET.SubElement(triangles, 'input', {'semantic': 'NORMAL', 'source': f'#{mesh_id}-normals', 'offset': '1'})
        ET.SubElement(triangles, 'input', {'semantic': 'TEXCOORD', 'source': f'#{mesh_id}-uvs', 'offset': '2', 'set': '0'})
        p = ET.SubElement(triangles, 'p')
        p.text = ' '.join(f'{idx} {idx} {idx}' for idx in indices)

        # 4. Library visual scenes
        lib_scene = ET.SubElement(root, 'library_visual_scenes')
        vs = ET.SubElement(lib_scene, 'visual_scene', {'id': 'VisualScene', 'name': 'VisualScene'})
        node = ET.SubElement(vs, 'node', {'id': f'{mesh_id}-node', 'name': mesh_id})
        inst_geom = ET.SubElement(node, 'instance_geometry', {'url': f'#{mesh_id}-geom'})
        bind_mat = ET.SubElement(inst_geom, 'bind_material')
        tech_common = ET.SubElement(bind_mat, 'technique_common')
        ET.SubElement(tech_common, 'instance_material', {
            'symbol': material_name,
            'target': f'#{material_name}-mat'
        })

        # 5. Scene (MUST BE LAST in Collada schema)
        scene = ET.SubElement(root, 'scene')
        ET.SubElement(scene, 'instance_visual_scene', {'url': '#VisualScene'})

        # Write with stable formatting
        ET.indent(root, space='  ')
        tree = ET.ElementTree(root)
        tree.write(path, encoding='utf-8', xml_declaration=True)


def create_flat_terrain_ter(size: int = 256, square_size: float = 2.0) -> Tuple[np.ndarray, np.ndarray]:
    """Create a flat terrain at elevation 0.

    Returns:
        (height_map, layer_map)
    """
    height_map = np.zeros((size, size), dtype=np.float32)
    layer_map = np.zeros((size, size), dtype=np.uint8)
    return height_map, layer_map


def create_straight_road_dae(
    path: Path,
    mesh_id: str,
    length: float = 500.0,
    width: float = 7.0,
    material_name: str = "triworld_road_asphalt",
) -> dict:
    """Create a straight road DAE along X axis centered at origin.

    Returns bounds dict.
    """
    half_w = width / 2.0

    # 4 vertices for a simple rectangular road strip
    # X extent = length (500m), Y extent = width (7m)
    # Vertex order: bottom-left, bottom-right, top-right, top-left (Z-up, X-forward, Y-left)
    positions = [
        [0.0, -half_w, 0.0],      # 0: left edge at start
        [length, -half_w, 0.0],   # 1: right edge at start
        [length, half_w, 0.0],    # 2: right edge at end
        [0.0, half_w, 0.0],       # 3: left edge at end
    ]

    # All normals point up
    normals = [
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
    ]

    # UVs: map along length and width, tiling every 7 meters
    u_max = width / 7.0
    v_max = length / 7.0
    uvs = [
        [0.0, 0.0],
        [u_max, 0.0],
        [u_max, v_max],
        [0.0, v_max],
    ]

    # Two triangles
    indices = [0, 1, 2, 0, 2, 3]

    bounds = {
        'min': [0.0, -half_w, 0.0],
        'max': [length, half_w, 0.0],
    }

    DaeSerializer.write_road_chunk(
        path=path,
        mesh_id=mesh_id,
        positions=positions,
        normals=normals,
        uvs=uvs,
        indices=indices,
        material_name=material_name,
        bounds=bounds,
    )

    return bounds