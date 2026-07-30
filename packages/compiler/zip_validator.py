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


def validate_zip_structure(zip_path: Path, stock_assets: Optional[set] = None) -> ZipValidationReport:
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

        # Check 2b: info.json metadata schema — BeamNG 0.38.6 level selector schema
        # Requires: non-empty title, authors, non-empty previews array with existing files
        # Rejects: legacy name, author, previewImage; rejects empty missionFile
        # Verifies: defaultSpawnPointName matches a declared spawn
        if info_json:
            metadata_issues = []

            # Require non-empty title
            title = info_json.get('title', '')
            if not title or not isinstance(title, str):
                metadata_issues.append("Missing or empty 'title' field")

            # Require authors
            authors = info_json.get('authors', '')
            if not authors or not isinstance(authors, str):
                metadata_issues.append("Missing or empty 'authors' field")

            # Require non-empty previews array
            previews = info_json.get('previews', [])
            if not isinstance(previews, list) or len(previews) == 0:
                metadata_issues.append("Missing or empty 'previews' array")
            else:
                # Verify preview files exist in ZIP
                for preview in previews:
                    if not isinstance(preview, str):
                        metadata_issues.append(f"Preview entry not a string: {preview}")
                        continue
                    # Check both with and without level_prefix
                    preview_paths = [
                        f"{level_prefix}{preview}",
                        preview,
                        f"levels/{report.root_level}/{preview}"
                    ]
                    if not any(p in namelist for p in preview_paths):
                        metadata_issues.append(f"Preview file not found in ZIP: {preview}")

            # Reject legacy fields
            legacy_fields = ['name', 'author', 'previewImage']
            for field in legacy_fields:
                if field in info_json:
                    metadata_issues.append(f"Legacy field '{field}' present (use 'title'/'authors'/'previews' instead)")

            # Reject empty missionFile
            if 'missionFile' in info_json:
                mission_file = info_json.get('missionFile', '')
                if mission_file == "":
                    metadata_issues.append("'missionFile' is empty string — omit field entirely")
                elif not isinstance(mission_file, str):
                    metadata_issues.append("'missionFile' must be string if present")

            # Verify defaultSpawnPointName matches a declared spawn
            default_spawn = info_json.get('defaultSpawnPointName', '')
            spawn_points = info_json.get('spawnPoints', [])
            if default_spawn:
                spawn_names = [s.get('objectname', '') for s in spawn_points if isinstance(s, dict)]
                if default_spawn not in spawn_names:
                    metadata_issues.append(f"defaultSpawnPointName '{default_spawn}' not found in spawnPoints objectname list: {spawn_names}")

            if not metadata_issues:
                report.checks.append(ValidationResult(
                    check_name="info_json_metadata_schema",
                    passed=True,
                    message="info.json metadata schema valid (title, authors, previews, no legacy fields, spawn match)",
                    details={"title": title, "authors": authors, "previews": previews}
                ))
            else:
                report.checks.append(ValidationResult(
                    check_name="info_json_metadata_schema",
                    passed=False,
                    message=f"info.json metadata schema issues: {'; '.join(metadata_issues)}",
                    details={"issues": metadata_issues}
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


        # Check 5: (Removed) main.materials.json is now validated recursively in Check 17

        # Check 6: All items.level.json files exist and are valid LDJSON
        items_files = [n for n in namelist if n.endswith('items.level.json')]
        invalid_items = []
        valid_lines_total = 0
        if items_files:
            for items_path in items_files:
                try:
                    with zf.open(items_path) as f:
                        items_content = f.read().decode('utf-8')
                    lines = items_content.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            json.loads(line)
                            valid_lines_total += 1
                except Exception as e:
                    invalid_items.append(f"{items_path}: {e}")

            if not invalid_items:
                report.checks.append(ValidationResult(
                    check_name="items_level_json_valid",
                    passed=True,
                    message=f"All {len(items_files)} items.level.json files valid LDJSON ({valid_lines_total} objects)",
                    details={"object_count": valid_lines_total, "files": len(items_files)}
                ))
            else:
                report.checks.append(ValidationResult(
                    check_name="items_level_json_valid",
                    passed=False,
                    message=f"Invalid items.level.json files found: {len(invalid_items)}",
                    details={"errors": invalid_items}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="items_level_json_valid",
                passed=False,
                message="No items.level.json missing",
                details={}
            ))

                # Check 7: SpawnSphere with SpawnSphereMarker datablock and numeric arrays for position and rotationMatrix
        spawns = []
        spawn_type_errors = []
        for items_path in items_files:
            try:
                with zf.open(items_path) as f:
                    file_content = f.read().decode('utf-8')
                for line in file_content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'SpawnSphere':
                            spawns.append(obj)

                            # Validate position
                            pos = obj.get('position')
                            if not isinstance(pos, list) or len(pos) != 3 or not all(isinstance(x, (int, float)) for x in pos):
                                spawn_type_errors.append(f"SpawnSphere {obj.get('name')} 'position' must be a numeric array of 3 finite values")

                            # Validate rotationMatrix
                            rot = obj.get('rotationMatrix')
                            if not isinstance(rot, list) or len(rot) != 9 or not all(isinstance(x, (int, float)) for x in rot):
                                spawn_type_errors.append(f"SpawnSphere {obj.get('name')} 'rotationMatrix' must be a numeric array of 9 finite values")

            except Exception:
                pass

        if spawns:
            all_correct = all(s.get('dataBlock') == 'SpawnSphereMarker' for s in spawns) and not spawn_type_errors
            if all_correct:
                report.checks.append(ValidationResult(
                    check_name="spawn_sphere_datablock",
                    passed=True,
                    message=f"Found {len(spawns)} SpawnSphere(s) with SpawnSphereMarker datablock and valid numeric position/rotationMatrix arrays",
                    details={"spawn_names": [s.get('name') for s in spawns]}
                ))
            else:
                report.checks.append(ValidationResult(
                    check_name="spawn_sphere_datablock",
                    passed=False,
                    message=f"SpawnSphere validation failed: errors={spawn_type_errors}",
                    details={"spawns": spawns, "errors": spawn_type_errors}
                ))
        else:
            report.checks.append(ValidationResult(
                check_name="spawn_sphere_datablock",
                passed=False,
                message="No SpawnSphere found in items.level.json files",
                details={}
            ))

        # Check 8: defaultSpawnPointName matches a SpawnSphere name
        if info_json:
            try:
                default_spawn = info_json.get('defaultSpawnPointName', '')
                spawn_names = [s.get('name') for s in spawns]
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

                # Check 9: Exactly one ScatterSky, TimeOfDay, TerrainBlock, LevelInfo
        counts = {'ScatterSky': 0, 'TimeOfDay': 0, 'TerrainBlock': 0, 'LevelInfo': 0, 'SimGroupEnd': 0, 'Sky': 0, 'Sun': 0}
        details = {'LevelInfo_globalEnviromentMap': None, 'ScatterSky_obj': None, 'TimeOfDay_obj': None}
        for items_path in items_files:
            try:
                with zf.open(items_path) as f:
                    file_content = f.read().decode('utf-8')
                for line in file_content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        cls = obj.get('class')
                        if cls in counts:
                            counts[cls] += 1
                        if cls == 'LevelInfo':
                            details['LevelInfo_globalEnviromentMap'] = obj.get('globalEnviromentMap')
                        elif cls == 'ScatterSky':
                            details['ScatterSky_obj'] = obj
                        elif cls == 'TimeOfDay':
                            details['TimeOfDay_obj'] = obj
            except Exception:
                pass

        # Check 9b: Reject SimGroupEnd - BeamNG 0.38.6 does not recognize this class
        if counts['SimGroupEnd'] == 0:
            report.checks.append(ValidationResult(
                check_name="no_simgroupend",
                passed=True,
                message="No SimGroupEnd objects found (BeamNG 0.38.6 incompatible)",
                details={"files_checked": len(items_files)}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="no_simgroupend",
                passed=False,
                message=f"Found {counts['SimGroupEnd']} SimGroupEnd object(s) - NOT supported in BeamNG 0.38.6",
                details={"count": counts['SimGroupEnd']}
            ))

        env_reqs = (counts['ScatterSky'] == 1 and counts['TimeOfDay'] == 1 and
                    counts['TerrainBlock'] == 1 and counts['LevelInfo'] == 1 and
                    counts['Sky'] == 0 and counts['Sun'] == 0)
        env_map_req = details['LevelInfo_globalEnviromentMap'] == "BNG_Sky_02_cubemap"

        if env_reqs and env_map_req:
            report.checks.append(ValidationResult(
                check_name="single_env_objects",
                passed=True,
                message="Exactly one ScatterSky, TimeOfDay, TerrainBlock, LevelInfo found with correct globalEnviromentMap",
                details=counts
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="single_env_objects",
                passed=False,
                message=f"Expected 1 of each (ScatterSky, TimeOfDay, TerrainBlock, LevelInfo), zero Sky/Sun and globalEnviromentMap='BNG_Sky_02_cubemap'. Got: {counts}, map={details['LevelInfo_globalEnviromentMap']}",
                details=counts
            ))


        # Check 9d: ScatterSky and TimeOfDay configurations
        env_errors = []
        sky = details.get('ScatterSky_obj')
        if sky:
            # ScatterSky position is numeric array of 3 finite values
            pos = sky.get('position')
            if not isinstance(pos, list) or len(pos) != 3 or not all(isinstance(x, (int, float)) for x in pos):
                env_errors.append('ScatterSky position must be a numeric array of 3 finite values')

            # elevation is within a daylight range, for this canary 30-80 degrees
            ele = sky.get('elevation', 0)
            if not isinstance(ele, (int, float)) or not (30 <= ele <= 80):
                env_errors.append(f'ScatterSky elevation must be between 30 and 80, got {ele}')

            # skyBrightness is positive
            sb = sky.get('skyBrightness')
            if sb is None:
                env_errors.append('ScatterSky skyBrightness is missing')
            elif not isinstance(sb, (int, float)) or sb <= 0:
                env_errors.append(f'ScatterSky skyBrightness must be positive, got {sb}')

            # ambientScale and sunScale are numeric RGBA arrays
            for k in ['ambientScale', 'sunScale']:
                val = sky.get(k)
                if not isinstance(val, list) or len(val) != 4 or not all(isinstance(x, (int, float)) for x in val):
                    env_errors.append(f'ScatterSky {k} must be a numeric array of 4 finite values')

            # required gradient paths are non-empty strings
            for k in ['ambientScaleGradientFile', 'sunScaleGradientFile', 'fogScaleGradientFile']:
                val = sky.get(k)
                if not isinstance(val, str) or not val.strip():
                    env_errors.append(f'ScatterSky {k} must be a non-empty string')

        tod = details.get('TimeOfDay_obj')
        if tod:
            # TimeOfDay time and startTime are finite and within 0-1
            time_val = tod.get('time')
            start_time = tod.get('startTime')
            for k, val in [('time', time_val), ('startTime', start_time)]:
                if not isinstance(val, (int, float)) or not (0 <= val <= 1):
                    env_errors.append(f'TimeOfDay {k} must be between 0 and 1, got {val}')

            # time equals startTime for this non-animated canary
            if time_val != start_time:
                env_errors.append(f'TimeOfDay time ({time_val}) must equal startTime ({start_time})')

            # animate is disabled and play is false
            if tod.get('animate') != '0':
                env_errors.append('TimeOfDay animate must be "0"')
            if tod.get('play') is not False:
                env_errors.append('TimeOfDay play must be false')

        if not env_errors and counts.get('Sky') == 0 and counts.get('Sun') == 0:
            report.checks.append(ValidationResult(
                check_name="daylight_configuration",
                passed=True,
                message="ScatterSky and TimeOfDay configurations are valid for daylight",
                details={}
            ))
        else:
            if counts.get('Sky') > 0 or counts.get('Sun') > 0:
                env_errors.append('Legacy Sky or Sun objects found')
            report.checks.append(ValidationResult(
                check_name="daylight_configuration",
                passed=False,
                message=f"Environment configuration errors: {env_errors}",
                details={"errors": env_errors}
            ))

        # Check 9c: Nested SimGroup Directory Structure
        nested_missing = []
        parent_errors = []
        for items_path in items_files:
            try:
                # determine represented parent group from its containing directory
                parts = items_path.split("/")
                if len(parts) >= 2:
                    current_dir_name = parts[-2]
                else:
                    current_dir_name = ""

                is_main_root = (items_path == f"{level_prefix}main/items.level.json")

                with zf.open(items_path) as f:
                    file_content = f.read().decode('utf-8')
                for line in file_content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)

                        # Parent relationship check
                        parent = obj.get('__parent')

                        if is_main_root:
                            if obj.get('name') == 'MissionGroup':
                                pass # allowed to lack __parent
                            else:
                                if parent != 'MissionGroup':
                                    parent_errors.append(f"Root object {obj.get('name')} parent is '{parent}', expected 'MissionGroup' or None (if MissionGroup)")
                        else:
                            if not parent:
                                parent_errors.append(f"Object {obj.get('name')} in {items_path} is missing __parent")
                            elif parent != current_dir_name:
                                parent_errors.append(f"Object {obj.get('name')} in {items_path} has __parent '{parent}', expected '{current_dir_name}'")

                        # Directory validation for SimGroups
                        if obj.get('class') == 'SimGroup':
                            sg_name = obj.get('name')
                            parent_dir = "/".join(items_path.split("/")[:-1])
                            expected_dir = f"{parent_dir}/{sg_name}"
                            expected_items = f"{expected_dir}/items.level.json"

                            if expected_items not in namelist:
                                nested_missing.append(f"{sg_name} defined in {items_path} misses {expected_items}")

            except Exception as e:
                nested_missing.append(f"Exception parsing {items_path}: {e}")

        if not nested_missing and not parent_errors:
            report.checks.append(ValidationResult(
                check_name="nested_simgroup_directory_structure",
                passed=True,
                message="Every SimGroup has a corresponding nested directory with items.level.json and parents match",
                details={}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="nested_simgroup_directory_structure",
                passed=False,
                message=f"Missing nested directories: {len(nested_missing)}, Parent errors: {len(parent_errors)}",
                details={"missing": nested_missing, "parent_errors": parent_errors}
            ))

                # Check 10: Asset references exist (DAE files referenced in TSStatic)
        dae_refs = set()
        for items_path in items_files:
            try:
                with zf.open(items_path) as f:
                    file_content = f.read().decode('utf-8')
                for line in file_content.strip().split('\n'):
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
            # Handle absolute paths starting with /levels/
            if dae.startswith('/levels/'):
                full_path = dae.lstrip('/')
            elif dae.startswith('levels/'):
                full_path = dae
            else:
                full_path = f"{level_prefix}{dae}"
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
                    expected_min = 5 + expected_heightmap + expected_layermap + 4
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

        for items_path in items_files:
            try:
                with zf.open(items_path) as f:
                    file_content = f.read().decode('utf-8')
                for line in file_content.strip().split('\n'):
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
        for items_path in items_files:
            try:
                with zf.open(items_path) as f:
                    file_content = f.read().decode('utf-8')
                for line in file_content.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'SpawnSphere':
                            pos_val = obj.get('position')
                            if isinstance(pos_val, list) and len(pos_val) >= 3:
                                spawn_pos = (float(pos_val[0]), float(pos_val[1]), float(pos_val[2]))
                            elif isinstance(pos_val, str):
                                parts = pos_val.split()
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


        # Check 17: Discover and validate all *.materials.json recursively
        materials_json_files = [n for n in namelist if n.endswith('.materials.json')]

        # We need to collect:
        # - all TerrainMaterial.internalName values
        # - TerrainMaterialTextureSet objects
        # - stock texture references
        terrain_materials = set()
        terrain_texture_sets = set()
        ordinary_materials = {}
        ordinary_mapTo_set = set()
        schema_issues = []
        missing_textures = []

        for mat_path in materials_json_files:
            try:
                with zf.open(mat_path) as f:
                    mat_json = json.load(f)

                # Check root is a flat dictionary, reject top-level "materials"
                if not isinstance(mat_json, dict):
                    schema_issues.append(f"{mat_path} root is not a dictionary")
                    continue
                if "materials" in mat_json and isinstance(mat_json["materials"], list):
                    schema_issues.append(f"{mat_path} uses invalid 'materials' list wrapper")
                    continue

                for key, mat in mat_json.items():
                    if not isinstance(mat, dict):
                        schema_issues.append(f"{mat_path}[{key}] is not a dict")
                        continue

                    cls = mat.get('class')
                    if cls == 'TerrainMaterialTextureSet':
                        if 'name' not in mat:
                            schema_issues.append(f"{mat_path}[{key}] missing name")
                        else:
                            terrain_texture_sets.add(mat['name'])
                        if 'persistentId' not in mat:
                            schema_issues.append(f"{mat_path}[{key}] missing persistentId")
                        for size_key in ['baseTexSize', 'detailTexSize', 'macroTexSize']:
                            if size_key in mat:
                                val = mat[size_key]
                                if not isinstance(val, list) or len(val) != 2 or not all(isinstance(x, (int, float)) for x in val):
                                    schema_issues.append(f"{mat_path}[{key}] {size_key} must be a numeric array of 2")

                    elif cls == 'TerrainMaterial':
                        internal_name = mat.get('internalName')
                        if not internal_name:
                            schema_issues.append(f"{mat_path}[{key}] missing internalName")
                        elif internal_name in terrain_materials:
                            schema_issues.append(f"Duplicate TerrainMaterial internalName: {internal_name}")
                        else:
                            terrain_materials.add(internal_name)

                        if 'persistentId' not in mat:
                            schema_issues.append(f"{mat_path}[{key}] missing persistentId")
                        if 'groundmodelName' not in mat:
                            schema_issues.append(f"{mat_path}[{key}] missing groundmodelName")

                        # Gather textures
                        for tkey, tval in mat.items():
                            if isinstance(tval, str) and (tval.endswith('.png') or tval.endswith('.jpg') or tval.endswith('.dds')):
                                if stock_assets is not None:
                                    # Normalize path for check
                                    normalized = tval.lstrip('/')
                                    if normalized not in stock_assets:
                                        missing_textures.append(tval)

                    elif cls == 'Material':
                        # Ordinary material logic
                        map_to = mat.get('mapTo')
                        name = mat.get('name')
                        if not map_to:
                            schema_issues.append(f"Material {name} missing mapTo")
                        elif map_to in ordinary_mapTo_set:
                            schema_issues.append(f"Duplicate ordinary Material.mapTo: {map_to}")
                        else:
                            ordinary_mapTo_set.add(map_to)
                            ordinary_materials[map_to] = mat

                        stages = mat.get('Stages')
                        if not stages or not isinstance(stages, list) or len(stages) == 0:
                            schema_issues.append(f"Material {name or map_to} missing or empty Stages")
                        else:
                            stage0 = stages[0]
                            if isinstance(stage0, dict):
                                if 'baseColorMap' not in stage0:
                                    schema_issues.append(f"Material {name or map_to} Stage 0 missing baseColorMap")
                                if 'normalMap' not in stage0:
                                    schema_issues.append(f"Material {name or map_to} Stage 0 missing normalMap")
                                if 'roughnessMap' not in stage0:
                                    schema_issues.append(f"Material {name or map_to} Stage 0 missing roughnessMap")

                                for tkey, tval in stage0.items():
                                    if isinstance(tval, str) and (tval.endswith('.png') or tval.endswith('.jpg') or tval.endswith('.dds')):
                                        if stock_assets is not None:
                                            normalized = tval.lstrip('/')
                                            if normalized not in stock_assets:
                                                missing_textures.append(tval)

            except Exception as e:
                schema_issues.append(f"Error validating {mat_path}: {e}")

        if not schema_issues:
            report.checks.append(ValidationResult(
                check_name="material_schema",
                passed=True,
                message="All materials follow BeamNG schema",
                details={
                    "terrain_materials": list(terrain_materials),
                    "texture_sets": list(terrain_texture_sets),
                    "ordinary_materials": list(ordinary_mapTo_set)
                }
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="material_schema",
                passed=False,
                message=f"Material schema issues: {schema_issues}",
                details={"issues": schema_issues}
            ))

        if stock_assets is not None:
            if not missing_textures:
                report.checks.append(ValidationResult(
                    check_name="material_textures",
                    passed=True,
                    message="All stock texture references are valid",
                    details={}
                ))
            else:
                report.checks.append(ValidationResult(
                    check_name="material_textures",
                    passed=False,
                    message=f"Missing stock texture references: {missing_textures}",
                    details={"missing": missing_textures}
                ))

        # Check 18: TerrainBlock material linking and .ter matching
        ter_issues = []

        # 1. Check TerrainBlock in items.level.json
        terrain_block_obj = None
        for items_path in items_files:
            try:
                with zf.open(items_path) as f:
                    content_str = f.read().decode('utf-8')
                for line in content_str.strip().split('\n'):
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'TerrainBlock':
                            terrain_block_obj = obj
                            break
            except Exception:
                pass
            if terrain_block_obj:
                break

        if terrain_block_obj:
            if 'materials' in terrain_block_obj:
                ter_issues.append("TerrainBlock uses legacy 'materials' comma-string instead of materialTextureSet")
            mat_tex_set = terrain_block_obj.get('materialTextureSet')
            if mat_tex_set:
                if mat_tex_set not in terrain_texture_sets:
                    ter_issues.append(f"TerrainBlock materialTextureSet '{mat_tex_set}' is not defined in any materials.json")
            else:
                ter_issues.append("TerrainBlock missing materialTextureSet")
        else:
            ter_issues.append("TerrainBlock not found")

        # 2. Check .ter materials
        ter_files = [n for n in namelist if n.endswith('.ter') and n.startswith(level_prefix)]
        for ter_path in ter_files:
            try:
                with zf.open(ter_path) as f:
                    ter_data = f.read()

                # Parse .ter header
                import struct
                # binary version 1 byte
                # size 4 bytes
                offset = 1
                size = struct.unpack_from('<I', ter_data, offset)[0]
                offset += 4

                # skip height map (size*size * 2)
                offset += size * size * 2

                # skip layer map (size*size)
                offset += size * size

                # read material count
                if offset + 4 > len(ter_data):
                    ter_issues.append("Truncated .ter file before materialCount")
                else:
                    mat_count = struct.unpack_from('<I', ter_data, offset)[0]
                    offset += 4

                    ter_material_names = []
                    parse_error = False
                    for _ in range(mat_count):
                        if offset + 1 > len(ter_data):
                            ter_issues.append("Truncated .ter material name length")
                            parse_error = True
                            break
                        name_len = struct.unpack_from('B', ter_data, offset)[0]
                        offset += 1
                        if name_len == 0:
                            ter_issues.append("Zero-length .ter material name")
                            parse_error = True
                            break
                        if offset + name_len > len(ter_data):
                            ter_issues.append("Truncated .ter material name string")
                            parse_error = True
                            break
                        name_bytes = ter_data[offset:offset + name_len]
                        offset += name_len
                        try:
                            name_str = name_bytes.decode('utf-8')
                        except UnicodeError:
                            ter_issues.append("Invalid UTF-8 in .ter material name")
                            parse_error = True
                            break
                        ter_material_names.append(name_str)

                    if not parse_error:
                        if offset != len(ter_data):
                            ter_issues.append(f"Unexpected trailing bytes in .ter file: {len(ter_data) - offset} bytes after final material name")
                        for tmat in ter_material_names:
                            if tmat not in terrain_materials:
                                ter_issues.append(f".ter material '{tmat}' has no matching TerrainMaterial.internalName")
            except Exception as e:
                ter_issues.append(f"Error parsing .ter materials: {e}")

        if not ter_issues:
            report.checks.append(ValidationResult(
                check_name="terrain_material_linking",
                passed=True,
                message="Terrain materials correctly linked",
                details={}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="terrain_material_linking",
                passed=False,
                message=f"Terrain material issues: {ter_issues}",
                details={"issues": ter_issues}
            ))

        # Check 18b: DAE material linking validation
        dae_material_issues = []
        dae_files_in_zip = [n for n in namelist if n.endswith('.dae') and n.startswith(level_prefix)]

        if dae_files_in_zip:
            road_mat_file = f"{level_prefix}art/shapes/roads/main.materials.json"
            if road_mat_file not in namelist:
                dae_material_issues.append(f"Missing road main.materials.json at {road_mat_file}")

            if "triworld_road_asphalt" not in ordinary_materials:
                dae_material_issues.append("Missing ordinary Material with mapTo matching 'triworld_road_asphalt'")

        for dae_file in dae_files_in_zip:
            try:
                with zf.open(dae_file) as f:
                    dae_xml = f.read()
                import xml.etree.ElementTree as ET
                dae_root = ET.fromstring(dae_xml)

                prim_symbols = set()
                for elem in dae_root.iter():
                    if elem.tag.endswith('polylist') or elem.tag.endswith('triangles') or elem.tag.endswith('mesh'):
                        mat_attr = elem.attrib.get('material')
                        if mat_attr:
                            prim_symbols.add(mat_attr)

                inst_materials = {}
                for elem in dae_root.iter():
                    if elem.tag.endswith('instance_material'):
                        sym = elem.attrib.get('symbol')
                        tgt = elem.attrib.get('target', '').lstrip('#')
                        if sym:
                            inst_materials[sym] = tgt

                lib_mats = set()
                for elem in dae_root.iter():
                    if elem.tag.endswith('material'):
                        mat_id = elem.attrib.get('id')
                        mat_name = elem.attrib.get('name')
                        if mat_id:
                            lib_mats.add(mat_id)
                        if mat_name:
                            lib_mats.add(mat_name)

                for sym in prim_symbols:
                    if sym not in inst_materials:
                        dae_material_issues.append(f"Collada primitive symbol mismatch: symbol '{sym}' not bound in instance_geometry")
                    else:
                        tgt = inst_materials[sym]
                        if tgt not in lib_mats and f"{tgt}-mat" not in lib_mats:
                            dae_material_issues.append(f"Collada instance_material target mismatch: target '{tgt}' not found in library_materials")

                    if sym in terrain_materials and sym not in ordinary_materials:
                        dae_material_issues.append(f"DAE material symbol '{sym}' resolved via class TerrainMaterial (must resolve via class Material)")
                    elif sym not in ordinary_materials:
                        dae_material_issues.append(f"DAE material symbol '{sym}' has no matching ordinary Material.mapTo")

            except Exception as e:
                dae_material_issues.append(f"Error parsing DAE XML {dae_file}: {e}")

        if not dae_material_issues:
            report.checks.append(ValidationResult(
                check_name="dae_material_linking",
                passed=True,
                message="DAE materials correctly resolved to ordinary Material",
                details={}
            ))
        else:
            report.checks.append(ValidationResult(
                check_name="dae_material_linking",
                passed=False,
                message=f"DAE material linking issues: {dae_material_issues}",
                details={"issues": dae_material_issues}
            ))

# Check 19: DecalRoad position = first node position, improvedSpline=true
        decal_road_position = None
        decal_road_improved_spline = None
        for items_path in items_files:
            try:
                with zf.open(items_path) as f:
                    file_content = f.read().decode('utf-8')
                for line in file_content.strip().split('\n'):
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
    from zipfile import ZipFile

    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        zip_path = Path("artifacts/canary_test.zip")

    stock_assets = None
    italy_zip = Path(r"C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\levels\italy.zip")
    if italy_zip.exists():
        try:
            with ZipFile(italy_zip, 'r') as zf:
                stock_assets = set(zf.namelist())
            print(f"Loaded stock asset allowlist from {italy_zip}")
        except Exception as e:
            print(f"Failed to load stock assets: {e}")
    else:
        print("Local BeamNG 0.38.6 installation not found. Skipping stock asset verification.")

    if zip_path.exists():
        report = validate_zip_structure(zip_path, stock_assets=stock_assets)
        print(report.summary())
        sys.exit(0 if report.all_passed else 1)
    else:
        print(f"ZIP not found: {zip_path}")
        sys.exit(1)
