"""Unit tests for the static ZIP validator with negative regression fixtures."""

import tempfile
import zipfile
import json
import hashlib
from pathlib import Path
from packages.compiler.zip_validator import validate_zip_structure, ZipValidationReport
from packages.compiler.synthetic_canary import create_synthetic_canary


def test_valid_canary_passes():
    """A valid canary should pass all checks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "valid.zip"
        create_synthetic_canary(zip_path, "test_level")
        report = validate_zip_structure(zip_path)
        assert report.all_passed, f"Expected all checks to pass, but got failures: {report.failed_checks}"


def create_perpendicular_dae_zip(tmpdir: Path) -> Path:
    """Create a ZIP with DAE road along Y axis but AI DecalRoad along X axis."""
    zip_path = tmpdir / "perpendicular.zip"
    
    # Start with a valid canary and modify it
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        art_dir = level_dir / "art" / "shapes" / "roads"
        art_dir.mkdir(parents=True)
        
        # Create a DAE that runs along Y axis (perpendicular to AI road on X)
        from packages.compiler.beamng_serializers import DaeSerializer
        dae_path = art_dir / "straight_road.dae"
        
        # Positions along Y axis (length in Y, width in X)
        positions = [
            [-3.5, 0.0, 0.0],
            [3.5, 0.0, 0.0],
            [3.5, 500.0, 0.0],
            [-3.5, 500.0, 0.0],
        ]
        normals = [[0.0, 0.0, 1.0]] * 4
        uvs = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
        indices = [0, 1, 2, 0, 2, 3]
        bounds = {'min': [-3.5, 0.0, 0.0], 'max': [3.5, 500.0, 0.0]}
        
        DaeSerializer.write_road_chunk(
            path=dae_path,
            mesh_id="straight_road",
            positions=positions,
            normals=normals,
            uvs=uvs,
            indices=indices,
            material_name="asphalt",
            bounds=bounds,
        )
        
        # Copy other files from a valid canary
        valid_zip = Path(tmpdir) / "valid.zip"
        create_synthetic_canary(valid_zip, "test_level")
        
        with zipfile.ZipFile(valid_zip, 'r') as zf:
            for name in zf.namelist():
                if 'straight_road.dae' not in name:
                    with zf.open(name) as src:
                        dest = staging / name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(src.read())
        
        # Replace the DAE with our perpendicular one
        dest_dae = staging / "levels" / "test_level" / "art" / "shapes" / "roads" / "straight_road.dae"
        dest_dae.write_bytes(dae_path.read_bytes())
        
        # Also need to update items.level.json to move TSStatic to Y=0 (matching DAE along Y)
        items_path = staging / "levels" / "test_level" / "main" / "items.level.json"
        items_content = items_path.read_text()
        lines = items_content.strip().split('\n')
        new_lines = []
        for line in lines:
            if line.strip():
                obj = json.loads(line)
                if obj.get('class') == 'TSStatic':
                    obj['position'] = "0 0 0"
                new_lines.append(json.dumps(obj, separators=(',', ':')))
            else:
                new_lines.append(line)
        items_path.write_text('\n'.join(new_lines))
        
        # Create ZIP
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
    
    return zip_path


def test_perpendicular_dae_fails():
    """ZIP with perpendicular DAE and AI road should fail road_axis_alignment check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_perpendicular_dae_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        # Should fail on road_axis_alignment
        alignment_check = next(c for c in report.checks if c.check_name == "road_axis_alignment")
        assert not alignment_check.passed, "Perpendicular DAE should fail road_axis_alignment"
        assert "dae_direction" in alignment_check.details
        assert alignment_check.details["dae_direction"] == "Y"


def create_missing_texture_zip(tmpdir: Path) -> Path:
    """Create a ZIP with a material referencing a non-existent texture in a Stage."""
    zip_path = tmpdir / "missing_texture.zip"
    
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        # Create main.materials.json with missing texture (NOT an /levels/italy/ path)
        materials_json = {
            "materials": [
                {
                    "name": "asphalt",
                    "mapTo": "asphalt",
                    "class": "Material",
                    "version": 1.5,
                    "Stages": [{
                        "baseColorMap": "art/shapes/roads/missing_texture.png",
                        "normalMap": "art/shapes/roads/missing_normal.png",
                    }],
                    "annotation": "ASPHALT",
                }
            ]
        }
        (level_dir / "main.materials.json").write_text(json.dumps(materials_json))
        
        # Minimal info.json
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level",
            "version": 1,
            "defaultSpawnPointName": "spawn_001",
            "materialFile": "main.materials.json",
        }))
        
        # Minimal items.level.json with SpawnSphere
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        
        # Environment
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]))
        
        # Empty .ter file (version 9)
        (level_dir / "test_level.ter").write_bytes(b'\x09\x00\x01\x00\x00' + b'\x00' * 256 * 256 * 2 + b'\x00' * 256 * 256 * 2 + b'\x00\x00\x00\x00')
        
        # Create ZIP
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
    
    return zip_path


def test_missing_nested_stage_texture_fails():
    """ZIP with missing nested Stage texture should fail material_textures check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_missing_texture_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        texture_check = next(c for c in report.checks if c.check_name == "material_textures")
        assert not texture_check.passed, "Missing texture should fail material_textures check"
        assert "Missing texture" in texture_check.message


def create_nonexistent_stock_path_zip(tmpdir: Path) -> Path:
    """Create a ZIP with material referencing a stock path that doesn't exist in Italy."""
    zip_path = tmpdir / "nonexistent_stock.zip"
    
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        materials_json = {
            "materials": [
                {
                    "name": "asphalt",
                    "mapTo": "asphalt",
                    "class": "Material",
                    "version": 1.5,
                    "Stages": [{
                        "baseColorMap": "/levels/italy/art/road/this_path_does_not_exist.png",
                    }],
                    "annotation": "ASPHALT",
                }
            ]
        }
        (level_dir / "main.materials.json").write_text(json.dumps(materials_json))
        
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level",
            "version": 1,
            "defaultSpawnPointName": "spawn_001",
            "materialFile": "main.materials.json",
        }))
        
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]))
        
        (level_dir / "test_level.ter").write_bytes(b'\x09\x00\x01\x00\x00' + b'\x00' * 256 * 256 * 2 + b'\x00' * 256 * 256 * 2 + b'\x00\x00\x00\x00')
        
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
    
    return zip_path


def test_nonexistent_stock_path_fails():
    """ZIP with nonexistent /levels/italy stock path should fail material_textures check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_nonexistent_stock_path_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        texture_check = next(c for c in report.checks if c.check_name == "material_textures")
        assert not texture_check.passed, "Nonexistent stock path should fail material_textures check"


def create_duplicate_sky_zip(tmpdir: Path) -> Path:
    """Create a ZIP with duplicate Sky across two items.level.json files."""
    zip_path = tmpdir / "duplicate_sky.zip"
    
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        # main.materials.json
        (level_dir / "main.materials.json").write_text(json.dumps({"materials": []}))
        
        # info.json
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level",
            "version": 1,
            "defaultSpawnPointName": "spawn_001",
            "materialFile": "main.materials.json",
        }))
        
        # main/items.level.json with Sky and Sun
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky", "material": "sky_material"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        
        # main/Environment/items.level.json ALSO with Sky and Sun (DUPLICATE)
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky", "material": "sky_material"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]))
        
        (level_dir / "test_level.ter").write_bytes(b'\x09\x00\x01\x00\x00' + b'\x00' * 256 * 256 * 2 + b'\x00' * 256 * 256 * 2 + b'\x00\x00\x00\x00')
        
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
    
    return zip_path


def test_duplicate_sky_fails():
    """ZIP with duplicate Sky should fail single_sky_sun check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_duplicate_sky_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        sky_check = next(c for c in report.checks if c.check_name == "single_sky_sun")
        assert not sky_check.passed, "Duplicate Sky should fail single_sky_sun check"
        assert sky_check.details.get("sky_count", 0) >= 2


def create_malformed_ter_zip(tmpdir: Path) -> Path:
    """Create a ZIP with malformed .ter file (wrong version)."""
    zip_path = tmpdir / "malformed_ter.zip"
    
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        (level_dir / "main.materials.json").write_text(json.dumps({"materials": []}))
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level", "version": 1, "defaultSpawnPointName": "spawn_001",
            "materialFile": "main.materials.json"
        }))
        
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]))
        
        # .ter with version 1 (wrong)
        (level_dir / "test_level.ter").write_bytes(b'\x01\x00\x01\x00\x00' + b'\x00' * 256 * 256 * 2 + b'\x00' * 256 * 256 + b'\x00\x00\x00\x00')
        
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
    
    return zip_path


def test_malformed_ter_tail_fails():
    """ZIP with wrong .ter version should fail ter_version_structure check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_malformed_ter_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        ter_check = next(c for c in report.checks if c.check_name == "ter_version_structure")
        assert not ter_check.passed, "Wrong .ter version should fail ter_version_structure check"


def create_unsafe_path_zip(tmpdir: Path) -> Path:
    """Create a ZIP with unsafe path (traversal)."""
    zip_path = tmpdir / "unsafe_path.zip"
    
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        (level_dir / "main.materials.json").write_text(json.dumps({"materials": []}))
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level", "version": 1, "defaultSpawnPointName": "spawn_001",
            "materialFile": "main.materials.json"
        }))
        
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]))
        
        (level_dir / "test_level.ter").write_bytes(b'\x09\x00\x01\x00\x00' + b'\x00' * 256 * 256 * 2 + b'\x00' * 256 * 256 * 2 + b'\x00\x00\x00\x00')
        
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all staging files
            for f in sorted(staging.rglob('*'), key=lambda p: str(p)):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
            # Add the unsafe file with explicit path containing ..
            info = zipfile.ZipInfo("../evil.txt", date_time=fixed_timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, b"evil")
    
    return zip_path


def test_unsafe_path_fails():
    """ZIP with unsafe path should fail unsafe_paths check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_unsafe_path_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        unsafe_check = next(c for c in report.checks if c.check_name == "unsafe_paths")
        assert not unsafe_check.passed, "Unsafe path should fail unsafe_paths check"


def create_mismatched_spawn_zip(tmpdir: Path) -> Path:
    """Create a ZIP where defaultSpawnPointName doesn't match any SpawnSphere."""
    zip_path = tmpdir / "mismatched_spawn.zip"
    
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        (level_dir / "main.materials.json").write_text(json.dumps({"materials": []}))
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level", "version": 1, "defaultSpawnPointName": "wrong_spawn_name",
            "materialFile": "main.materials.json"
        }))
        
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]))
        
        (level_dir / "test_level.ter").write_bytes(b'\x09\x00\x01\x00\x00' + b'\x00' * 256 * 256 * 2 + b'\x00' * 256 * 256 * 2 + b'\x00\x00\x00\x00')
        
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
    
    return zip_path


def test_mismatched_spawn_name_fails():
    """ZIP with mismatched defaultSpawnPointName should fail spawn_name_match check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_mismatched_spawn_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        spawn_check = next(c for c in report.checks if c.check_name == "spawn_name_match")
        assert not spawn_check.passed, "Mismatched spawn name should fail spawn_name_match check"


def create_invalid_material_wrapper_zip(tmpdir: Path) -> Path:
    """Create a ZIP with invalid material wrapper (not class=Material, missing mapTo/Stages)."""
    zip_path = tmpdir / "invalid_material_wrapper.zip"
    
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)
        
        # Invalid material format - using {"materials": [...]} with wrong schema
        materials_json = {
            "materials": [
                {
                    "name": "asphalt",
                    "diffuseMap": "/levels/italy/art/road/t_asphalt_variation_01_b.color.png",
                    # Missing: class=Material, mapTo, Stages
                }
            ]
        }
        (level_dir / "main.materials.json").write_text(json.dumps(materials_json))
        
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level", "version": 1, "defaultSpawnPointName": "spawn_001",
            "materialFile": "main.materials.json"
        }))
        
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),
        ]))
        
        (level_dir / "test_level.ter").write_bytes(b'\x09\x00\x01\x00\x00' + b'\x00' * 256 * 256 * 2 + b'\x00' * 256 * 256 * 2 + b'\x00\x00\x00\x00')
        
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
    
    return zip_path


def test_invalid_material_wrapper_fails():
    """ZIP with invalid material wrapper/schema should fail material_schema check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_invalid_material_wrapper_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)
        
        schema_check = next(c for c in report.checks if c.check_name == "material_schema")
        assert not schema_check.passed, "Invalid material wrapper should fail material_schema check"


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))