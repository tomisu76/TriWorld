"""Static ZIP validator for BeamNG level packages."""

import zipfile
import json
import hashlib
import re
import xml.etree.ElementTree as ET
import struct
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZipValidationReport:
    """Complete validation report for a ZIP file."""
    zip_path: str
    sha256: str
    total_files: int
    total_size: int
    root_level: str
    checks: List[ValidationResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> List[ValidationResult]:
        return [c for c in self.checks if not c.passed]

    def summary(self) -> str:
        lines = [
            f"ZIP Validation Report: {self.zip_path}",
            f"SHA256: {self.sha256}",
            f"Total files: {self.total_files}, Total size: {self.total_size} bytes",
            f"Root level: {self.root_level}",
            f"Checks: {len([c for c in self.checks if c.passed])}/{len(self.checks)} passed",
            ""
        ]
        for check in self.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"  [{status}] {check.check_name}: {check.message}")
            if check.details:
                for k, v in check.details.items():
                    lines.append(f"    {k}: {v}")
        return "\n".join(lines)


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def parse_dae_vertices_and_bounds(dae_content: str) -> Tuple[np.ndarray, Dict[str, float]]:
    """Parse DAE positions array and compute world-space bounds."""
    root = ET.fromstring(dae_content)
    ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
    
    # Find positions array
    pos_array = root.find('.//c:float_array[@id]', ns)
    if pos_array is None or not pos_array.text:
        raise ValueError("No positions array found in DAE")
    
    values = [float(v) for v in pos_array.text.split()]
    vertices = np.array(values).reshape(-1, 3)
    
    bounds = {
        'min_x': float(vertices[:, 0].min()),
        'max_x': float(vertices[:, 0].max()),
        'min_y': float(vertices[:, 1].min()),
        'max_y': float(vertices[:, 1].max()),
        'min_z': float(vertices[:, 2].min()),
        'max_z': float(vertices[:, 2].max()),
    }
    
    return vertices, bounds


def determine_road_axis(bounds: Dict[str, float]) -> str:
    """Determine the longitudinal axis of a road from its bounds."""
    extent_x = bounds['max_x'] - bounds['min_x']
    extent_y = bounds['max_y'] - bounds['min_y']
    
    if extent_x > extent_y:
        return 'X'
    elif extent_y > extent_x:
        return 'Y'
    else:
        return 'unknown'


def validate_zip_structure(zip_path: Path) -> ZipValidationReport:
    """Run comprehensive static validation on a BeamNG level ZIP."""

    report = ZipValidationReport(
        zip_path=str(zip_path),
        sha256=compute_sha256(zip_path),
        total_files=0,
        total_size=0,
        root_level="",
        checks=[]
    )

    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = zf.namelist()
        report.total_files = len(namelist)
        report.total_size = sum(zf.getinfo(n).file_size for n in namelist)

        # Check 1: Single level root (levels/<slug>/...)
        root_dirs = set()
        for name in namelist:
            parts = name.split('/')
            if len(parts) >= 2 and parts[0] == 'levels':
                root_dirs.add(parts[1])

        if len(root_dirs) == 1:
            report.root_level = list(root_dirs)[0]
            report.checks.append(ValidationResult(
                check_name="single_level_root",
                passed=True,
                message=f"Single level root: levels/{report.root_level}/",
                details={"root_level": report.root_level}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="single_level_root",
                passed=False,
                message=f"Expected exactly one level root, found: {sorted(root_dirs)}",
                details={"root_dirs": list(root_dirs)}
            ))

        level_prefix = f"levels/{report.root_level}/" if report.root_level else "levels/"

        # Check 2: info.json exists and parses
        info_path = f"{level_prefix}info.json"
        info_json = None
        if info_path in namelist:
            try:
                with zf.open(info_path) as f:
                    info_json = json.load(f)
                report.checks.append(ValidationResult(
                    check_name="info_json_exists",
                    passed=True,
                    message="info.json exists and parses",
                    details={"keys": list(info_json.keys())}
                ))
            except Exception as e:
                report.checks.append(ValidationResult(
                    check_name="info_json_exists",
                    passed=False,
                    message=f"info.json exists but failed to parse: {e}",
                    details={"error": str(e)}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="info_json_exists",
                passed=False,
                message="info.json missing",
                details={}
            ))

        # Check 3: .ter file exists
        ter_files = [n for n in namelist if n.endswith('.ter') and n.startswith(level_prefix)]
        if ter_files:
            report.checks.append(ValidationResult(
                check_name="ter_file_exists",
                passed=True,
                message=f"Found .ter file(s): {ter_files}",
                details={"ter_files": ter_files}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="ter_file_exists",
                passed=False,
                message="No .ter file found",
                details={}
            ))

        # Check 4: .terrain.json exists with version 9
        terrain_json_files = [n for n in namelist if n.endswith('.terrain.json') and n.startswith(level_prefix)]
        terrain_json = None
        if terrain_json_files:
            for tjf in terrain_json_files:
                try:
                    with zf.open(tjf) as f:
                        tj = json.load(f)
                    version = tj.get('version', 0)
                    if version == 9:
                        report.checks.append(ValidationResult(
                            check_name="terrain_json_version",
                            passed=True,
                            message=f"{tjf} has correct version 9",
                            details={"version": version, "file": tjf}
                        ))
                    else:
                        report.checks.append(ValidationResult(
                            check_name="terrain_json_version",
                            passed=False,
                            message=f"{tjf} has version {version}, expected 9",
                            details={"version": version, "file": tjf}
                        ))
                    terrain_json = tj
                    break
                except Exception as e:
                    report.checks.append(ValidationResult(
                        check_name="terrain_json_version",
                        passed=False,
                        message=f"Failed to parse {tjf}: {e}",
                        details={"error": str(e), "file": tjf}
                    ))
        else:
            report.checks.append(ValidationResult(
                check_name="terrain_json_version",
                passed=False,
                message="No .terrain.json found",
                details={}
            ))

        # Check 5: main.materials.json exists and parses
        mat_path = f"{level_prefix}main.materials.json"
        materials = []
        if mat_path in namelist:
            try:
                with zf.open(mat_path) as f:
                    mat_json = json.load(f)
                materials = mat_json.get('materials', [])
                report.checks.append(ValidationResult(
                    check_name="materials_json_exists",
                    passed=True,
                    message=f"main.materials.json exists with {len(materials)} materials",
                    details={"material_count": len(materials), "material_names": [m.get('name') for m in materials]}
                ))
            except Exception as e:
                report.checks.append(ValidationResult(
                    check_name="materials_json_exists",
                    passed=False,
                    message=f"main.materials.json failed to parse: {e}",
                    details={"error": str(e)}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="materials_json_exists",
                passed=False,
                message="main.materials.json missing",
                details={}
            ))

        # Check 6: main/items.level.json exists and valid LDJSON
        items_path = f"{level_prefix}main/items.level.json"
        items_content = ""
        if items_path in namelist:
            try:
                with zf.open(items_path) as f:
                    items_content = f.read().decode('utf-8')
                lines = items_content.strip().split('\n')
                valid_lines = 0
                for line in lines:
                    if line.strip():
                        json.loads(line)
                        valid_lines += 1
                report.checks.append(ValidationResult(
                    check_name="items_level_json_valid",
                    passed=True,
                    message=f"main/items.level.json valid LDJSON with {valid_lines} objects",
                    details={"object_count": valid_lines}
                ))
            except Exception as e:
                report.checks.append(ValidationResult(
                    check_name="items_level_json_valid",
                    passed=False,
                    message=f"main/items.level.json invalid LDJSON: {e}",
                    details={"error": str(e)}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="items_level_json_valid",
                passed=False,
                message="main/items.level.json missing",
                details={}
            ))

        # Check 7: SpawnSphere with SpawnSphereMarker datablock
        spawns = []
        if items_path in namelist:
            try:
                with zf.open(items_path) as f:
                    content = f.read().decode('utf-8')
                for line in content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'SpawnSphere':
                            spawns.append(obj)
                if spawns:
                    all_correct = all(s.get('dataBlock') == 'SpawnSphereMarker' for s in spawns)
                    if all_correct:
                        report.checks.append(ValidationResult(
                            check_name="spawn_sphere_datablock",
                            passed=True,
                            message=f"Found {len(spawns)} SpawnSphere(s) with SpawnSphereMarker datablock",
                            details={"spawn_names": [s.get('name') for s in spawns]}
                        ))
                    else:
                        report.checks.append(ValidationResult(
                            check_name="spawn_sphere_datablock",
                            passed=False,
                            message=f"Some SpawnSphere objects have wrong datablock",
                            details={"spawns": spawns}
                        ))
                else:
                    report.checks.append(ValidationResult(
                        check_name="spawn_sphere_datablock",
                        passed=False,
                        message="No SpawnSphere found in items.level.json",
                        details={}
                    ))
            except Exception as e:
                report.checks.append(ValidationResult(
                    check_name="spawn_sphere_datablock",
                    passed=False,
                    message=f"Error checking SpawnSphere: {e}",
                    details={"error": str(e)}
                ))

        # Check 8: defaultSpawnPointName matches a SpawnSphere name
        if info_json and items_path in namelist:
            try:
                default_spawn = info_json.get('defaultSpawnPointName', '')
                with zf.open(items_path) as f:
                    content = f.read().decode('utf-8')
                spawn_names = []
                for line in content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'SpawnSphere':
                            spawn_names.append(obj.get('name'))
                if default_spawn in spawn_names:
                    report.checks.append(ValidationResult(
                        check_name="spawn_name_match",
                        passed=True,
                        message=f"defaultSpawnPointName '{default_spawn}' matches SpawnSphere name",
                        details={"default_spawn": default_spawn, "available_spawns": spawn_names}
                    ))
                else:
                    report.checks.append(ValidationResult(
                        check_name="spawn_name_match",
                        passed=False,
                        message=f"defaultSpawnPointName '{default_spawn}' does not match any SpawnSphere",
                        details={"default_spawn": default_spawn, "available_spawns": spawn_names}
                    ))
            except Exception as e:
                report.checks.append(ValidationResult(
                    check_name="spawn_name_match",
                    passed=False,
                    message=f"Error checking spawn name match: {e}",
                    details={"error": str(e)}
                ))

        # Check 9: Exactly one Sky and one Sun across ALL items.level.json files
        sky_count = 0
        sun_count = 0
        sky_sun_details = []
        for name in namelist:
            if name.endswith('items.level.json'):
                try:
                    with zf.open(name) as f:
                        content = f.read().decode('utf-8')
                    for line in content.strip().split('\n'):
                        if line.strip():
                            obj = json.loads(line)
                            if obj.get('class') == 'Sky':
                                sky_count += 1
                                sky_sun_details.append(f"Sky in {name}")
                            elif obj.get('class') == 'Sun':
                                sun_count += 1
                                sky_sun_details.append(f"Sun in {name}")
                except Exception:
                    pass
        if sky_count == 1 and sun_count == 1:
            report.checks.append(ValidationResult(
                check_name="single_sky_sun",
                passed=True,
                message="Exactly one Sky and one Sun found across all items.level.json",
                details={"sky_count": sky_count, "sun_count": sun_count, "details": sky_sun_details}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="single_sky_sun",
                passed=False,
                message=f"Expected 1 Sky and 1 Sun, found Sky={sky_count}, Sun={sun_count}",
                details={"sky_count": sky_count, "sun_count": sun_count, "details": sky_sun_details}
            ))

        # Check 10: Asset references exist (DAE files referenced in TSStatic)
        dae_refs = set()
        if items_path in namelist:
            try:
                with zf.open(items_path) as f:
                    content = f.read().decode('utf-8')
                for line in content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'TSStatic':
                            shape_name = obj.get('shapeName', '')
                            if shape_name:
                                dae_refs.add(shape_name)
            except Exception:
                pass

        missing_dae = []
        for dae in dae_refs:
            full_path = f"{level_prefix}{dae}" if not dae.startswith('levels/') else dae
            if full_path not in namelist:
                missing_dae.append(full_path)

        if not missing_dae and dae_refs:
            report.checks.append(ValidationResult(
                check_name="asset_references_exist",
                passed=True,
                message=f"All {len(dae_refs)} DAE references exist in ZIP",
                details={"dae_files": list(dae_refs)}
            ))
        elif missing_dae:
            report.checks.append(ValidationResult(
                check_name="asset_references_exist",
                passed=False,
                message=f"Missing DAE files: {missing_dae}",
                details={"missing": missing_dae, "referenced": list(dae_refs)}
            ))

        # Check 11: .ter file version 9 and structure
        for ter_file in ter_files:
            try:
                with zf.open(ter_file) as f:
                    data = f.read()
                if len(data) >= 5:
                    version = data[0]
                    size = int.from_bytes(data[1:5], 'little')
                    expected_heightmap = size * size * 2
                    expected_layermap = size * size
                    expected_layertexturemap = size * size  # version 9+
                    expected_min = 5 + expected_heightmap + expected_layermap + expected_layertexturemap + 4
                    if version == 9 and len(data) >= expected_min:
                        report.checks.append(ValidationResult(
                            check_name="ter_version_structure",
                            passed=True,
                            message=f"{ter_file}: version 9, size {size}, structure valid",
                            details={"version": version, "size": size, "file_size": len(data)}
                        ))
                    else:
                        report.checks.append(ValidationResult(
                            check_name="ter_version_structure",
                            passed=False,
                            message=f"{ter_file}: version={version} (expected 9), size={size}, file_size={len(data)} (expected>={expected_min})",
                            details={"version": version, "size": size, "file_size": len(data)}
                        ))
            except Exception as e:
                report.checks.append(ValidationResult(
                    check_name="ter_version_structure",
                    passed=False,
                    message=f"Error reading {ter_file}: {e}",
                    details={"error": str(e)}
                ))

        # Check 12: Unsafe paths (traversal, absolute, case collisions)
        unsafe = []
        case_map = {}
        for name in namelist:
            if '..' in name or name.startswith('/') or re.match(r'^[A-Za-z]:', name):
                unsafe.append(f"Unsafe path: {name}")
            lower = name.lower()
            if lower in case_map and case_map[lower] != name:
                unsafe.append(f"Case collision: {case_map[lower]} vs {name}")
            case_map[lower] = name

        if not unsafe:
            report.checks.append(ValidationResult(
                check_name="unsafe_paths",
                passed=True,
                message="No unsafe paths or case collisions",
                details={}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="unsafe_paths",
                passed=False,
                message=f"Found {len(unsafe)} unsafe path issues",
                details={"issues": unsafe}
            ))

        # Check 13: Duplicate ZIP entries
        duplicates = [n for n in namelist if namelist.count(n) > 1]
        if not duplicates:
            report.checks.append(ValidationResult(
                check_name="duplicate_entries",
                passed=True,
                message="No duplicate ZIP entries",
                details={}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="duplicate_entries",
                passed=False,
                message=f"Duplicate entries found: {list(set(duplicates))}",
                details={"duplicates": list(set(duplicates))}
            ))

        # Check 14: Deterministic timestamps (all 1980-01-01 00:00:00)
        non_deterministic = []
        for name in namelist:
            info = zf.getinfo(name)
            if info.date_time != (1980, 1, 1, 0, 0, 0):
                non_deterministic.append(f"{name}: {info.date_time}")
        if not non_deterministic:
            report.checks.append(ValidationResult(
                check_name="deterministic_timestamps",
                passed=True,
                message="All entries have fixed timestamp (1980-01-01)",
                details={}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="deterministic_timestamps",
                passed=False,
                message=f"{len(non_deterministic)} entries have non-fixed timestamps",
                details={"non_fixed": non_deterministic[:10]}
            ))

        # Check 15: Road axis alignment - AI DecalRoad and TSStatic share same Y; DAE direction matches
        tsstatic_y = None
        decal_road_y = None
        dae_direction = None
        decal_nodes = None

        if items_path in namelist:
            try:
                with zf.open(items_path) as f:
                    content = f.read().decode('utf-8')
                for line in content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'TSStatic':
                            pos_str = obj.get('position', '0 0 0')
                            parts = pos_str.split()
                            if len(parts) >= 2:
                                tsstatic_y = float(parts[1])
                        elif obj.get('class') == 'DecalRoad' and 'nodes' in obj:
                            nodes = obj['nodes']
                            decal_nodes = nodes
                            if nodes:
                                decal_road_y = nodes[0][1] if len(nodes[0]) > 1 else None
            except Exception:
                pass

        # Check DAE direction
        for name in namelist:
            if name.endswith('.dae') and name.startswith(level_prefix):
                try:
                    with zf.open(name) as f:
                        dae_content = f.read().decode('utf-8')
                    vertices, bounds = parse_dae_vertices_and_bounds(dae_content)
                    dae_direction = determine_road_axis(bounds)
                except Exception:
                    pass

        if tsstatic_y is not None and decal_road_y is not None:
            y_match = abs(tsstatic_y - decal_road_y) < 0.01
            if y_match and dae_direction == 'X':
                report.checks.append(ValidationResult(
                    check_name="road_axis_alignment",
                    passed=True,
                    message=f"AI DecalRoad (Y={decal_road_y}) and TSStatic (Y={tsstatic_y}) share same Y axis; DAE direction: {dae_direction}",
                    details={"tsstatic_y": tsstatic_y, "decal_road_y": decal_road_y, "dae_direction": dae_direction}
                ))
            else:
                report.checks.append(ValidationResult(
                    check_name="road_axis_alignment",
                    passed=False,
                    message=f"Alignment failed: Y_match={y_match}, DAE_direction={dae_direction} (expected X), TSStatic_Y={tsstatic_y}, DecalRoad_Y={decal_road_y}",
                    details={"tsstatic_y": tsstatic_y, "decal_road_y": decal_road_y, "dae_direction": dae_direction, "y_match": y_match}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="road_axis_alignment",
                passed=False,
                message="Could not determine Y coordinates for alignment check",
                details={"tsstatic_y": tsstatic_y, "decal_road_y": decal_road_y, "dae_direction": dae_direction}
            ))

        # Check 16: Spawn position on/above physical road
        spawn_pos = None
        if items_path in namelist:
            try:
                with zf.open(items_path) as f:
                    content = f.read().decode('utf-8')
                for line in content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'SpawnSphere':
                            pos_str = obj.get('position', '0 0 0')
                            parts = pos_str.split()
                            if len(parts) >= 3:
                                spawn_pos = (float(parts[0]), float(parts[1]), float(parts[2]))
            except Exception:
                pass

        if spawn_pos and tsstatic_y is not None:
            if abs(spawn_pos[1] - tsstatic_y) < 0.01 and spawn_pos[2] > 0:
                report.checks.append(ValidationResult(
                    check_name="spawn_on_road",
                    passed=True,
                    message=f"Spawn at ({spawn_pos[0]}, {spawn_pos[1]}, {spawn_pos[2]}) is on physical road",
                    details={"spawn_pos": spawn_pos, "road_y": tsstatic_y}
                ))
            else:
                report.checks.append(ValidationResult(
                    check_name="spawn_on_road",
                    passed=False,
                    message=f"Spawn at ({spawn_pos[0]}, {spawn_pos[1]}, {spawn_pos[2]}) not on road (road Y={tsstatic_y})",
                    details={"spawn_pos": spawn_pos, "road_y": tsstatic_y}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="spawn_on_road",
                passed=False,
                message="Could not verify spawn position relative to road",
                details={"spawn_pos": spawn_pos, "road_y": tsstatic_y}
            ))

        # Check 17: Material texture references - verify ALL texture paths in Stages
        # For /levels/italy paths, verify against actual Italy.zip; for others, check ZIP
        italy_zip_path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\levels\italy.zip")
        missing_textures = []
        if mat_path in namelist:
            try:
                with zf.open(mat_path) as f:
                    mat_json = json.load(f)
                materials = mat_json.get('materials', [])
                italy_files = set()
                if italy_zip_path.exists():
                    with zipfile.ZipFile(italy_zip_path, 'r') as iz:
                        italy_files = set(iz.namelist())
                
                for mat in materials:
                    stages = mat.get('Stages', [])
                    for stage in stages:
                        if not isinstance(stage, dict):
                            continue
                        for key in ['baseColorMap', 'normalMap', 'roughnessMap', 'metallicMap', 
                                   'ambientOcclusionMap', 'opacityMap', 'diffuseMap', 'specularMap', 
                                   'detailMap', 'detailNormalMap']:
                            tex = stage.get(key, '')
                            if not tex:
                                continue
                            if tex.startswith('/levels/italy/'):
                                clean = tex.lstrip('/')
                                if clean not in italy_files:
                                    missing_textures.append(f"{mat.get('name')}: {key}={clean}")
                            elif not tex.startswith('/'):
                                # Relative path - check in ZIP
                                full_path = f"{level_prefix}{tex}" if not tex.startswith('levels/') else tex
                                if full_path not in namelist:
                                    missing_textures.append(f"{mat.get('name')}: {key}={full_path}")
            except Exception as e:
                missing_textures.append(f"Error checking textures: {e}")

        if not missing_textures:
            report.checks.append(ValidationResult(
                check_name="material_textures",
                passed=True,
                message="All material texture references resolved (stock Italy paths verified or in ZIP)",
                details={"material_count": len(materials)}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="material_textures",
                passed=False,
                message=f"Missing texture references: {missing_textures}",
                details={"missing": missing_textures}
            ))

        # Check 18: Material schema - class=Material, mapTo, Stages
        schema_issues = []
        if mat_path in namelist:
            try:
                with zf.open(mat_path) as f:
                    mat_json = json.load(f)
                materials = mat_json.get('materials', [])
                for mat in materials:
                    if not isinstance(mat, dict):
                        schema_issues.append(f"Material not a dict: {mat}")
                        continue
                    if mat.get('class') != 'Material':
                        schema_issues.append(f"Material {mat.get('name')} missing class=Material")
                    if 'mapTo' not in mat:
                        schema_issues.append(f"Material {mat.get('name')} missing mapTo")
                    if 'Stages' not in mat:
                        schema_issues.append(f"Material {mat.get('name')} missing Stages")
            except Exception as e:
                schema_issues.append(f"Error validating material schema: {e}")

        if not schema_issues:
            report.checks.append(ValidationResult(
                check_name="material_schema",
                passed=True,
                message="All materials follow BeamNG schema (class=Material, mapTo, Stages)",
                details={"material_count": len(materials)}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="material_schema",
                passed=False,
                message=f"Material schema issues: {schema_issues}",
                details={"issues": schema_issues}
            ))

        # Check 19: DecalRoad position = first node position, improvedSpline=true
        decal_road_position = None
        decal_road_improved_spline = None
        if items_path in namelist:
            try:
                with zf.open(items_path) as f:
                    content = f.read().decode('utf-8')
                for line in content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'DecalRoad':
                            decal_road_position = obj.get('position')
                            decal_road_improved_spline = obj.get('improvedSpline')
                            break
            except Exception:
                pass

        if decal_road_position and decal_nodes:
            first_node_pos = f"{decal_nodes[0][0]} {decal_nodes[0][1]} {decal_nodes[0][2]}"
            if decal_road_position == first_node_pos:
                report.checks.append(ValidationResult(
                    check_name="decalroad_position",
                    passed=True,
                    message=f"DecalRoad position matches first node: {first_node_pos}",
                    details={"decalroad_position": decal_road_position, "first_node": first_node_pos}
                ))
            else:
                report.checks.append(ValidationResult(
                    check_name="decalroad_position",
                    passed=False,
                    message=f"DecalRoad position {decal_road_position} != first node {first_node_pos}",
                    details={"decalroad_position": decal_road_position, "first_node": first_node_pos}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="decalroad_position",
                passed=False,
                message="Could not verify DecalRoad position vs first node",
                details={"decalroad_position": decal_road_position, "has_nodes": decal_nodes is not None}
            ))

        if decal_road_improved_spline is True:
            report.checks.append(ValidationResult(
                check_name="decalroad_improved_spline",
                passed=True,
                message="DecalRoad has improvedSpline=true",
                details={"improvedSpline": decal_road_improved_spline}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="decalroad_improved_spline",
                passed=False,
                message=f"DecalRoad improvedSpline is {decal_road_improved_spline}, expected true",
                details={"improvedSpline": decal_road_improved_spline}
            ))

    return report


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        zip_path = Path("artifacts/canary_test.zip")
    
    if zip_path.exists():
        report = validate_zip_structure(zip_path)
        print(report.summary())
        sys.exit(0 if report.all_passed else 1)
    else:
        print(f"ZIP not found: {zip_path}")
        sys.exit(1)