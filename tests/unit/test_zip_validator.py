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
            "asphalt": {
                "name": "asphalt",
                "mapTo": "asphalt",
                "class": "Material",
                "version": 1.5,
                "Stages": [{
                    "baseColorMap": "art/shapes/roads/missing_texture.png",
                    "normalMap": "art/shapes/roads/missing_normal.png"
                }],
                "annotation": "ASPHALT"
            }
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
        report = validate_zip_structure(zip_path, stock_assets=set())

        texture_check = next(c for c in report.checks if c.check_name == "material_textures")
        assert not texture_check.passed, "Missing texture should fail material_textures check"
        assert "Missing" in texture_check.message


def create_nonexistent_stock_path_zip(tmpdir: Path) -> Path:
    """Create a ZIP with material referencing a stock path that doesn't exist in Italy."""
    zip_path = tmpdir / "nonexistent_stock.zip"

    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)

        materials_json = {
            "asphalt": {
                "name": "asphalt",
                "mapTo": "asphalt",
                "class": "Material",
                "version": 1.5,
                "Stages": [{
                    "baseColorMap": "art/shapes/roads/missing_texture.png",
                    "normalMap": "art/shapes/roads/missing_normal.png"
                }],
                "annotation": "ASPHALT"
            }
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
        report = validate_zip_structure(zip_path, stock_assets=set())

        texture_check = next(c for c in report.checks if c.check_name == "material_textures")
        assert not texture_check.passed, "Nonexistent stock path should fail material_textures check"


def create_duplicate_sky_zip(output_dir: Path) -> Path:
    zip_path = output_dir / "duplicate_sky.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Create minimal valid zip structure but with duplicate ScatterSky
        zf.writestr("levels/test/info.json", json.dumps({
            "title": "Test", "authors": "Test", "previews": ["p.png"], "defaultSpawnPointName": "s1"
        }))
        zf.writestr("levels/test/p.png", "dummy")
        zf.writestr("levels/test/test.ter", b"\x09" + b"\x00"*20)
        zf.writestr("levels/test/test.terrain.json", json.dumps({"version": 9}))
        zf.writestr("levels/test/main.materials.json", json.dumps({"materials": []}))

        # main/items.level.json with 2 ScatterSky objects
        items = [
            json.dumps({"class": "ScatterSky", "name": "sky1"}),
            json.dumps({"class": "ScatterSky", "name": "sky2"}),
            json.dumps({"class": "TimeOfDay", "name": "tod"}),
            json.dumps({"class": "TerrainBlock", "name": "ter"}),
            json.dumps({"class": "LevelInfo", "name": "li", "globalEnviromentMap": "BNG_Sky_02_cubemap"}),
            json.dumps({"class": "SpawnSphere", "name": "s1", "dataBlock": "SpawnSphereMarker"})
        ]
        zf.writestr("levels/test/main/items.level.json", "\n".join(items))
    return zip_path


def test_duplicate_env_objects_fails():
    """ZIP with duplicate Sky should fail single_sky_sun check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_duplicate_sky_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)

        sky_check = next(c for c in report.checks if c.check_name == "single_env_objects")
        assert not sky_check.passed, "Duplicate Sky should fail single_sky_sun check"
        assert sky_check.details.get("ScatterSky", 0) >= 2


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


def create_simgroupend_zip(tmpdir: Path) -> Path:
    """Create a ZIP with SimGroupEnd objects (should fail no_simgroupend check)."""
    zip_path = tmpdir / "simgroupend.zip"

    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)

        (level_dir / "main.materials.json").write_text(json.dumps({"materials": []}))
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level", "version": 1, "defaultSpawnPointName": "spawn_001",
            "materialFile": "main.materials.json"
        }))

        # Valid scene graph but WITH SimGroupEnd entries
        items_lines = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"}),
            json.dumps({"class": "TerrainBlock", "name": "Terrain", "position": "0 0 0", "terrainFile": "test_level.ter"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints"}),
            json.dumps({"class": "SpawnSphere", "name": "spawn_001", "position": "0 0 0.5", "dataBlock": "SpawnSphereMarker"}),
            json.dumps({"class": "SimGroupEnd"}),  # INVALID - SimGroupEnd not recognized by BeamNG 0.38.6
            json.dumps({"class": "SimGroupEnd"}),  # INVALID - SimGroupEnd not recognized by BeamNG 0.38.6
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(items_lines))
        (level_dir / "main" / "Environment" / "items.level.json").parent.mkdir(parents=True)
        (level_dir / "main" / "Environment" / "items.level.json").write_text('\n'.join([
            json.dumps({"class": "SimGroup", "name": "Environment"}),
            json.dumps({"class": "Sky", "name": "Sky"}),
            json.dumps({"class": "Sun", "name": "Sun"}),
            json.dumps({"class": "SimGroupEnd"}),  # INVALID - SimGroupEnd not recognized by BeamNG 0.38.6
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


def test_simgroupend_fails():
    """ZIP with SimGroupEnd should fail no_simgroupend check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_simgroupend_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)

        simgroupend_check = next(c for c in report.checks if c.check_name == "no_simgroupend")
        assert not simgroupend_check.passed, "SimGroupEnd should fail no_simgroupend check"
        assert simgroupend_check.details.get("count", 0) >= 1

        # The overall validation should fail because of SimGroupEnd
        assert not report.all_passed, "Overall validation should fail when SimGroupEnd is present"


def test_valid_canary_passes_no_simgroupend():
    """A valid canary generated by the fixed generator should pass no_simgroupend check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "valid.zip"
        create_synthetic_canary(zip_path, "test_level")
        report = validate_zip_structure(zip_path)

        simgroupend_check = next(c for c in report.checks if c.check_name == "no_simgroupend")
        assert simgroupend_check.passed, f"Fixed generator should not produce SimGroupEnd: {simgroupend_check.message}"


def create_bad_metadata_zip(tmpdir: Path) -> Path:
    """Create a ZIP with bad info.json metadata: legacy fields, empty missionFile, missing required fields."""
    zip_path = tmpdir / "bad_metadata.zip"

    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)

        (level_dir / "main.materials.json").write_text(json.dumps({"materials": []}))

        # BAD info.json: legacy fields, empty missionFile, missing title/authors/previews, mismatched spawn
        (level_dir / "info.json").write_text(json.dumps({
            "name": "test_level",                    # LEGACY - should be 'title'
            "version": 1,
            "author": "TriWorld",                    # LEGACY - should be 'authors'
            "defaultSpawnPointName": "wrong_spawn",  # MISMATCH
            "previewImage": "preview.png",           # LEGACY - should be 'previews' array
            "missionFile": "",                       # EMPTY - should be omitted
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


def test_bad_metadata_fails():
    """ZIP with bad info.json metadata should fail info_json_metadata_schema check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_bad_metadata_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)

        metadata_check = next(c for c in report.checks if c.check_name == "info_json_metadata_schema")
        assert not metadata_check.passed, "Bad metadata should fail info_json_metadata_schema check"
        issues = metadata_check.details.get("issues", [])
        assert any("Missing or empty 'title' field" in i for i in issues), "Should flag missing title"
        assert any("Missing or empty 'authors' field" in i for i in issues), "Should flag missing authors"
        assert any("Missing or empty 'previews' array" in i for i in issues), "Should flag missing previews"
        assert any("Legacy field 'name'" in i for i in issues), "Should flag legacy 'name' field"
        assert any("Legacy field 'author'" in i for i in issues), "Should flag legacy 'author' field"
        assert any("Legacy field 'previewImage'" in i for i in issues), "Should flag legacy 'previewImage' field"
        assert any("'missionFile' is empty string" in i for i in issues), "Should flag empty missionFile"
        assert any("defaultSpawnPointName 'wrong_spawn' not found" in i for i in issues), "Should flag mismatched spawn"

        # Overall validation should fail
        assert not report.all_passed, "Overall validation should fail when metadata is bad"


def create_good_metadata_zip(tmpdir: Path) -> Path:
    """Create a ZIP with good info.json metadata matching the BeamNG 0.38.6 schema."""
    zip_path = tmpdir / "good_metadata.zip"

    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir) / "staging"
        level_dir = staging / "levels" / "test_level"
        level_dir.mkdir(parents=True)

        (level_dir / "main.materials.json").write_text(json.dumps({"materials": []}))

        # GOOD info.json: correct schema
        (level_dir / "info.json").write_text(json.dumps({
            "title": "Test Level",
            "description": "Test level",
            "authors": "Test Author",
            "size": [256, 256],
            "defaultSpawnPointName": "spawn_001",
            "spawnPoints": [{
                "translationId": "Test Spawn",
                "description": "Test spawn",
                "objectname": "spawn_001",
                "preview": "preview.png"
            }],
            "supportsTraffic": True,
            "previews": ["preview.png"]
        }))

        # Create preview.png placeholder
        (level_dir / "preview.png").write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\xf4\x8c\x8d\x00\x00\x00\x00IEND\xaeB`\x82'
        )

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


def test_good_metadata_passes():
    """ZIP with good info.json metadata should pass info_json_metadata_schema check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_good_metadata_zip(Path(tmpdir))
        report = validate_zip_structure(zip_path)

        metadata_check = next(c for c in report.checks if c.check_name == "info_json_metadata_schema")
        assert metadata_check.passed, f"Good metadata should pass: {metadata_check.message}"

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))


def create_base_valid_zip(zip_path: Path):
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("levels/test/info.json", json.dumps({
            "title": "Test", "authors": "Test", "previews": ["p.png"], "defaultSpawnPointName": "s1"
        }))
        zf.writestr("levels/test/p.png", "dummy")

        # Binary ter with 1 material "asphalt"
        import struct
        ter_data = bytearray()
        ter_data += struct.pack('B', 9) # version
        ter_data += struct.pack('<I', 2) # size
        ter_data += b'\x00' * (2*2*2) # height map
        ter_data += b'\x00' * (2*2) # layer map
        ter_data += struct.pack('<I', 1) # mat count
        name_bytes = b'asphalt'
        ter_data += struct.pack('<I', len(name_bytes))
        ter_data += name_bytes

        zf.writestr("levels/test/test.ter", bytes(ter_data))
        zf.writestr("levels/test/test.terrain.json", json.dumps({"version": 9}))

        mat_json = {
            "testLevelTerrainMaterialTextureSet": {
                "name": "testLevelTerrainMaterialTextureSet",
                "class": "TerrainMaterialTextureSet",
                "persistentId": "4439d48e-2402-402a-8a64-18fb9fb59bac",
                "baseTexSize": [4096, 4096]
            },
            "asphalt": {
                "internalName": "asphalt",
                "class": "TerrainMaterial",
                "persistentId": "6e2bfb0e-e63c-45c5-bd1f-40964decabe4",
                "groundmodelName": "ASPHALT",
                "baseColorBaseTex": "t_asphalt_02_b.png"
            }
        }
        zf.writestr("levels/test/art/terrains/main.materials.json", json.dumps(mat_json))

        # Valid B2 Hierarchy
        items_main = [
            json.dumps({"class": "SimGroup", "name": "MissionGroup"})
        ]
        items_missiongroup = [
            json.dumps({"class": "SimGroup", "name": "Level_objects", "__parent": "MissionGroup"}),
            json.dumps({"class": "SimGroup", "name": "Spawnpoints", "__parent": "MissionGroup"})
        ]
        items_level_objects = [
            json.dumps({"class": "LevelInfo", "name": "li", "globalEnviromentMap": "BNG_Sky_02_cubemap", "__parent": "Level_objects"}),
            json.dumps({"class": "ScatterSky", "name": "sky1", "__parent": "Level_objects"}),
            json.dumps({"class": "TimeOfDay", "name": "tod", "__parent": "Level_objects"}),
            json.dumps({"class": "TerrainBlock", "name": "ter", "__parent": "Level_objects", "materialTextureSet": "testLevelTerrainMaterialTextureSet"})
        ]
        items_spawnpoints = [
            json.dumps({"class": "SpawnSphere", "name": "s1", "dataBlock": "SpawnSphereMarker", "position": [0.0, 250.0, 0.5], "rotationMatrix": [0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0], "__parent": "Spawnpoints"})
        ]

        zf.writestr("levels/test/main/items.level.json", "\n".join(items_main))
        zf.writestr("levels/test/main/MissionGroup/items.level.json", "\n".join(items_missiongroup))
        zf.writestr("levels/test/main/MissionGroup/Level_objects/items.level.json", "\n".join(items_level_objects))
        zf.writestr("levels/test/main/MissionGroup/Spawnpoints/items.level.json", "\n".join(items_spawnpoints))

def test_valid_exact_b2_hierarchy_passes():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)
        report = validate_zip_structure(zip_path)

        env_check = next(c for c in report.checks if c.check_name == "single_env_objects")
        assert env_check.passed, f"Valid B2 hierarchy should pass single_env_objects: {env_check.message}"

        struct_check = next(c for c in report.checks if c.check_name == "nested_simgroup_directory_structure")
        assert struct_check.passed, f"Valid B2 hierarchy should pass nested_simgroup_directory_structure: {struct_check.message}"


def test_missing_nested_child_items_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item != "levels/test/main/MissionGroup/Spawnpoints/items.level.json":
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        struct_check = next(c for c in report.checks if c.check_name == "nested_simgroup_directory_structure")
        assert not struct_check.passed, "Missing nested items.level.json should fail"
        assert any("misses" in m for m in struct_check.details.get("missing", []))

def test_flat_spawnpoints_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("levels/test/info.json", json.dumps({"title": "Test", "authors": "Test", "previews": ["p.png"], "defaultSpawnPointName": "s1"}))
            zf.writestr("levels/test/p.png", "dummy")
            zf.writestr("levels/test/test.ter", b"\x09" + b"\x00"*20)
            zf.writestr("levels/test/test.terrain.json", json.dumps({"version": 9}))
            zf.writestr("levels/test/main.materials.json", json.dumps({"materials": []}))

            items_main = [
                json.dumps({"class": "SimGroup", "name": "MissionGroup"})
            ]
            items_missiongroup = [
                json.dumps({"class": "SimGroup", "name": "Level_objects", "__parent": "MissionGroup"}),
                json.dumps({"class": "SimGroup", "name": "Spawnpoints", "__parent": "MissionGroup"})
            ]
            items_level_objects = [
                json.dumps({"class": "LevelInfo", "name": "li", "globalEnviromentMap": "BNG_Sky_02_cubemap", "__parent": "Level_objects"}),
                json.dumps({"class": "ScatterSky", "name": "sky1", "__parent": "Level_objects"}),
                json.dumps({"class": "TimeOfDay", "name": "tod", "__parent": "Level_objects"}),
                json.dumps({"class": "TerrainBlock", "name": "ter", "__parent": "Level_objects"})
            ]
            items_spawnpoints = [
                json.dumps({"class": "SpawnSphere", "name": "s1", "dataBlock": "SpawnSphereMarker", "__parent": "Spawnpoints"})
            ]

            zf.writestr("levels/test/main/items.level.json", "\n".join(items_main))
            zf.writestr("levels/test/main/MissionGroup/items.level.json", "\n".join(items_missiongroup))
            zf.writestr("levels/test/main/MissionGroup/Level_objects/items.level.json", "\n".join(items_level_objects))
            # Put Spawnpoints at main/Spawnpoints instead of main/MissionGroup/Spawnpoints
            zf.writestr("levels/test/main/Spawnpoints/items.level.json", "\n".join(items_spawnpoints))

        report = validate_zip_structure(zip_path)
        struct_check = next(c for c in report.checks if c.check_name == "nested_simgroup_directory_structure")
        assert not struct_check.passed, "Flat spawnpoints when parent is MissionGroup should fail"


def test_missing_parent_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        # Modify Level_objects items to remove __parent from ScatterSky
        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        # parse lines, remove __parent from ScatterSky specifically
                        lines = content.split('\n')
                        new_lines = []
                        for l in lines:
                            obj = json.loads(l)
                            if obj.get('class') == 'ScatterSky':
                                del obj['__parent']
                            new_lines.append(json.dumps(obj))
                        zf.writestr(item, '\n'.join(new_lines))
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        struct_check = next(c for c in report.checks if c.check_name == "nested_simgroup_directory_structure")
        assert not struct_check.passed, "Missing __parent should fail"
        assert any("missing __parent" in e for e in struct_check.details.get("parent_errors", []))

def test_incorrect_parent_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content.replace('"__parent": "Level_objects"', '"__parent": "WrongGroup"')
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        struct_check = next(c for c in report.checks if c.check_name == "nested_simgroup_directory_structure")
        assert not struct_check.passed, "Incorrect __parent should fail"

def test_object_in_wrong_physical_directory_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Spawnpoints/items.level.json":
                        # Move this items.level.json to a wrong physical directory but keep __parent="Spawnpoints"
                        zf.writestr("levels/test/main/MissionGroup/WrongDir/items.level.json", zf_old.read(item))
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        struct_check = next(c for c in report.checks if c.check_name == "nested_simgroup_directory_structure")
        assert not struct_check.passed, "Object in wrong physical directory fails"


def test_duplicate_scattersky_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content + '\n' + json.dumps({"class": "ScatterSky", "name": "sky2", "__parent": "Level_objects"})
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        env_check = next(c for c in report.checks if c.check_name == "single_env_objects")
        assert not env_check.passed, "Duplicate ScatterSky fails"

def test_legacy_sky_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content + '\n' + json.dumps({"class": "Sky", "name": "olds", "__parent": "Level_objects"})
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        env_check = next(c for c in report.checks if c.check_name == "single_env_objects")
        assert not env_check.passed, "Legacy Sky fails"

def test_legacy_sun_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content + '\n' + json.dumps({"class": "Sun", "name": "oldsun", "__parent": "Level_objects"})
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        env_check = next(c for c in report.checks if c.check_name == "single_env_objects")
        assert not env_check.passed, "Legacy Sun fails"


def test_missing_levelinfo_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        lines = [l for l in content.split('\n') if 'LevelInfo' not in l]
                        zf.writestr(item, '\n'.join(lines))
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        env_check = next(c for c in report.checks if c.check_name == "single_env_objects")
        assert not env_check.passed, "Missing LevelInfo fails"

def test_missing_global_env_map_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)

        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content.replace('"globalEnviromentMap": "BNG_Sky_02_cubemap"', '"globalEnviromentMap": ""')
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))

        report = validate_zip_structure(zip_path2)
        env_check = next(c for c in report.checks if c.check_name == "single_env_objects")
        assert not env_check.passed, "Missing globalEnviromentMap fails"


def test_spawnsphere_string_position_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)
        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Spawnpoints/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content.replace('"position":[0.0,250.0,0.5]', '"position":"0 250 0.5"').replace('"position": [0.0, 250.0, 0.5]', '"position": "0 250 0.5"')
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))
        report = validate_zip_structure(zip_path2)
        spawn_check = next(c for c in report.checks if c.check_name == "spawn_sphere_datablock")
        assert not spawn_check.passed, "String position for SpawnSphere should fail"


def test_spawnsphere_malformed_position_array_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)
        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Spawnpoints/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content.replace('[0.0, 250.0, 0.5]', '[0.0, 250.0]').replace('[0.0,250.0,0.5]', '[0.0,250.0]')
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))
        report = validate_zip_structure(zip_path2)
        spawn_check = next(c for c in report.checks if c.check_name == "spawn_sphere_datablock")
        assert not spawn_check.passed, "Malformed position array for SpawnSphere should fail"


def test_spawnsphere_string_rotation_matrix_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)
        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Spawnpoints/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content.replace('[0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0]', '"0 1 0 0 -1 0 0 0 1"').replace('[0.0,1.0,0.0,0.0,-1.0,0.0,0.0,0.0,1.0]', '"0 1 0 0 -1 0 0 0 1"')
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))
        report = validate_zip_structure(zip_path2)
        spawn_check = next(c for c in report.checks if c.check_name == "spawn_sphere_datablock")
        assert not spawn_check.passed, "String rotationMatrix for SpawnSphere should fail"


def test_spawnsphere_malformed_rotation_matrix_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)
        zip_path2 = Path(tmpdir) / "test2.zip"
        with zipfile.ZipFile(zip_path2, 'w') as zf:
            with zipfile.ZipFile(zip_path, 'r') as zf_old:
                for item in zf_old.namelist():
                    if item == "levels/test/main/MissionGroup/Spawnpoints/items.level.json":
                        content = zf_old.read(item).decode('utf-8')
                        new_content = content.replace('[0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0]', '[0.0, 1.0, 0.0]').replace('[0.0,1.0,0.0,0.0,-1.0,0.0,0.0,0.0,1.0]', '[0.0,1.0,0.0]')
                        zf.writestr(item, new_content)
                    else:
                        zf.writestr(item, zf_old.read(item))
        report = validate_zip_structure(zip_path2)
        spawn_check = next(c for c in report.checks if c.check_name == "spawn_sphere_datablock")
        assert not spawn_check.passed, "Malformed rotationMatrix for SpawnSphere should fail"


def test_exact_b21_spawnsphere_passes():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        create_base_valid_zip(zip_path)
        report = validate_zip_structure(zip_path)
        spawn_check = next(c for c in report.checks if c.check_name == "spawn_sphere_datablock")
        assert spawn_check.passed, f"Exact B2.1 SpawnSphere should pass: {spawn_check.message}"





def build_daylight_zip(zip_path, sky_dict, tod_dict):
    import zipfile
    import json
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("levels/test/info.json", json.dumps({
            "title": "Test", "authors": "Test", "previews": ["p.png"], "defaultSpawnPointName": "s1"
        }))
        zf.writestr("levels/test/p.png", "dummy")
        zf.writestr("levels/test/test.ter", b"\x09" + b"\x00"*20)
        zf.writestr("levels/test/test.terrain.json", json.dumps({"version": 9}))
        zf.writestr("levels/test/main.materials.json", json.dumps({"materials": []}))

        # main
        zf.writestr("levels/test/main/items.level.json", '{"class": "SimGroup", "name": "MissionGroup"}')
        zf.writestr("levels/test/main/MissionGroup/items.level.json", '{"class": "SimGroup", "name": "Level_objects", "__parent": "MissionGroup"}\n{"class": "SimGroup", "name": "Spawnpoints", "__parent": "MissionGroup"}')

        # Spawnpoints
        zf.writestr("levels/test/main/MissionGroup/Spawnpoints/items.level.json", '{"class": "SpawnSphere", "name": "s1", "position": [0,0,0], "rotationMatrix": [1,0,0,0,1,0,0,0,1], "dataBlock": "SpawnSphereMarker", "__parent": "Spawnpoints"}')

        # Level_objects
        lo_items = [
            '{"class": "LevelInfo", "name": "theLevelInfo", "__parent": "Level_objects", "globalEnviromentMap": "BNG_Sky_02_cubemap", "persistentId": "id"}',
            '{"class": "TerrainBlock", "name": "Terrain", "__parent": "Level_objects", "terrainFile": "/levels/test/test.ter", "position": "0 0 0", "rotation": "0 0 0 1", "scale": "1 1 1", "squareSize": 2.0, "maxHeight": 100.0, "materials": "asphalt"}',
            json.dumps(sky_dict),
            json.dumps(tod_dict)
        ]
        zf.writestr("levels/test/main/MissionGroup/Level_objects/items.level.json", "\n".join(lo_items))

def test_daylight_config_passes(tmp_path):
    zip_path = tmp_path / "test.zip"
    sky = {"name": "sunsky", "class": "ScatterSky", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "azimuth": 45.0, "elevation": 55.0, "skyBrightness": 40.0, "ambientScale": [1.0, 0.9, 0.8, 1.0], "sunScale": [1.0, 0.9, 0.8, 1.0], "fogScale": [0.4, 0.67, 1.0, 1.0], "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png", "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png", "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"}
    tod = {"name": "tod", "class": "TimeOfDay", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "animate": "0", "play": False, "axisTilt": 20.0, "azimuthOverride": 0.0, "startTime": 0.92, "time": 0.92}
    build_daylight_zip(zip_path, sky, tod)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "daylight_configuration")
    assert check.passed

def test_daylight_missing_sky_brightness(tmp_path):
    zip_path = tmp_path / "test.zip"
    sky = {"name": "sunsky", "class": "ScatterSky", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "azimuth": 45.0, "elevation": 55.0, "ambientScale": [1.0, 0.9, 0.8, 1.0], "sunScale": [1.0, 0.9, 0.8, 1.0], "fogScale": [0.4, 0.67, 1.0, 1.0], "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png", "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png", "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"}
    tod = {"name": "tod", "class": "TimeOfDay", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "animate": "0", "play": False, "axisTilt": 20.0, "azimuthOverride": 0.0, "startTime": 0.92, "time": 0.92}
    build_daylight_zip(zip_path, sky, tod)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "daylight_configuration")
    assert not check.passed
    assert "ScatterSky skyBrightness is missing" in check.message

def test_daylight_zero_sky_brightness(tmp_path):
    zip_path = tmp_path / "test.zip"
    sky = {"name": "sunsky", "class": "ScatterSky", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "azimuth": 45.0, "elevation": 55.0, "skyBrightness": 0, "ambientScale": [1.0, 0.9, 0.8, 1.0], "sunScale": [1.0, 0.9, 0.8, 1.0], "fogScale": [0.4, 0.67, 1.0, 1.0], "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png", "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png", "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"}
    tod = {"name": "tod", "class": "TimeOfDay", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "animate": "0", "play": False, "axisTilt": 20.0, "azimuthOverride": 0.0, "startTime": 0.92, "time": 0.92}
    build_daylight_zip(zip_path, sky, tod)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "daylight_configuration")
    assert not check.passed
    assert "ScatterSky skyBrightness must be positive" in check.message

def test_daylight_malformed_sunscale(tmp_path):
    zip_path = tmp_path / "test.zip"
    sky = {"name": "sunsky", "class": "ScatterSky", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "azimuth": 45.0, "elevation": 55.0, "skyBrightness": 40.0, "ambientScale": [1.0, 0.9, 0.8, 1.0], "sunScale": [1.0, 0.9, 0.8], "fogScale": [0.4, 0.67, 1.0, 1.0], "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png", "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png", "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"}
    tod = {"name": "tod", "class": "TimeOfDay", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "animate": "0", "play": False, "axisTilt": 20.0, "azimuthOverride": 0.0, "startTime": 0.92, "time": 0.92}
    build_daylight_zip(zip_path, sky, tod)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "daylight_configuration")
    assert not check.passed
    assert "sunScale must be a numeric array of 4 finite values" in check.message

def test_daylight_invalid_elevation(tmp_path):
    zip_path = tmp_path / "test.zip"
    sky = {"name": "sunsky", "class": "ScatterSky", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "azimuth": 45.0, "elevation": 10.0, "skyBrightness": 40.0, "ambientScale": [1.0, 0.9, 0.8, 1.0], "sunScale": [1.0, 0.9, 0.8, 1.0], "fogScale": [0.4, 0.67, 1.0, 1.0], "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png", "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png", "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"}
    tod = {"name": "tod", "class": "TimeOfDay", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "animate": "0", "play": False, "axisTilt": 20.0, "azimuthOverride": 0.0, "startTime": 0.92, "time": 0.92}
    build_daylight_zip(zip_path, sky, tod)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "daylight_configuration")
    assert not check.passed
    assert "elevation must be between 30 and 80" in check.message

def test_daylight_invalid_tod_range(tmp_path):
    zip_path = tmp_path / "test.zip"
    sky = {"name": "sunsky", "class": "ScatterSky", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "azimuth": 45.0, "elevation": 55.0, "skyBrightness": 40.0, "ambientScale": [1.0, 0.9, 0.8, 1.0], "sunScale": [1.0, 0.9, 0.8, 1.0], "fogScale": [0.4, 0.67, 1.0, 1.0], "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png", "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png", "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"}
    tod = {"name": "tod", "class": "TimeOfDay", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "animate": "0", "play": False, "axisTilt": 20.0, "azimuthOverride": 0.0, "startTime": 1.5, "time": 1.5}
    build_daylight_zip(zip_path, sky, tod)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "daylight_configuration")
    assert not check.passed
    assert "TimeOfDay time must be between 0 and 1" in check.message

def test_daylight_mismatched_time(tmp_path):
    zip_path = tmp_path / "test.zip"
    sky = {"name": "sunsky", "class": "ScatterSky", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "azimuth": 45.0, "elevation": 55.0, "skyBrightness": 40.0, "ambientScale": [1.0, 0.9, 0.8, 1.0], "sunScale": [1.0, 0.9, 0.8, 1.0], "fogScale": [0.4, 0.67, 1.0, 1.0], "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png", "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png", "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"}
    tod = {"name": "tod", "class": "TimeOfDay", "__parent": "Level_objects", "position": [0.0, 0.0, 100.0], "animate": "0", "play": False, "axisTilt": 20.0, "azimuthOverride": 0.0, "startTime": 0.92, "time": 0.9}
    build_daylight_zip(zip_path, sky, tod)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "daylight_configuration")
    assert not check.passed
    assert "must equal startTime" in check.message

def build_custom_material_zip(zip_path, modify_callback):
    create_base_valid_zip(zip_path)
    import zipfile
    import json

    # Read existing zip, write new
    tmp_path = zip_path.with_suffix('.tmp.zip')
    with zipfile.ZipFile(zip_path, 'r') as zin, zipfile.ZipFile(tmp_path, 'w') as zout:
        for item in zin.infolist():
            if item.filename == "levels/test/art/terrains/main.materials.json":
                mat_data = json.loads(zin.read(item.filename))
                mat_data = modify_callback("mat", mat_data)
                zout.writestr(item, json.dumps(mat_data))
            elif item.filename == "levels/test/main/MissionGroup/Level_objects/items.level.json":
                lines = zin.read(item.filename).decode('utf-8').split('\n')
                new_lines = []
                for line in lines:
                    if line.strip():
                        obj = json.loads(line)
                        if obj.get('class') == 'TerrainBlock':
                            obj = modify_callback("ter", obj)
                        new_lines.append(json.dumps(obj))
                zout.writestr(item, "\n".join(new_lines))
            else:
                zout.writestr(item, zin.read(item.filename))

    import shutil
    shutil.move(str(tmp_path), str(zip_path))

def test_top_level_materials_wrapper_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "mat":
            return {"materials": [data["asphalt"]]}
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not check.passed
    assert "list wrapper" in check.message

def test_missing_terrainmaterialtextureset_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "mat":
            del data["testLevelTerrainMaterialTextureSet"]
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not check.passed
    assert "not defined" in check.message

def test_unresolved_materialtextureset_reference_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "ter":
            data["materialTextureSet"] = "InvalidSet"
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not check.passed

def test_ordinary_material_used_as_terrain_layer_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "mat":
            data["asphalt"]["class"] = "Material"
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not check.passed
    assert "has no matching" in check.message

def test_missing_ter_material_match_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "mat":
            data["asphalt"]["internalName"] = "different_name"
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not check.passed

def test_case_mismatch_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "mat":
            data["asphalt"]["internalName"] = "Asphalt"
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not check.passed

def test_duplicate_internalname_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "mat":
            data["asphalt2"] = dict(data["asphalt"])
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not check.passed
    assert "Duplicate TerrainMaterial" in check.message

def test_missing_groundmodelname_fails(tmp_path):
    zip_path = tmp_path / "test.zip"
    def modify(type_, data):
        if type_ == "mat":
            del data["asphalt"]["groundmodelName"]
        return data
    build_custom_material_zip(zip_path, modify)
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not check.passed
    assert "missing groundmodelName" in check.message


def test_ter_v9_no_layer_texture_map_passes(tmp_path):
    zip_path = tmp_path / "valid_v9.zip"
    create_synthetic_canary(zip_path, "test_level")
    report = validate_zip_structure(zip_path)
    check = next(c for c in report.checks if c.check_name == "ter_version_structure")
    assert check.passed
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert link_check.passed


def test_ter_inserted_layer_texture_map_fails(tmp_path):
    zip_path = tmp_path / "inserted_layer_tex.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")

    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                import struct
                version = content[0]
                size = struct.unpack_from('<I', content, 1)[0]
                hdr_len = 1 + 4 + (size * size * 2) + (size * size)
                extra_bytes = b'\x00' * (size * size)
                content = content[:hdr_len] + extra_bytes + content[hdr_len:]
            zf_out.writestr(item, content)

    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed
    assert ("Unexpected trailing bytes" in link_check.message or "has no matching" in link_check.message or "Error" in link_check.message)


def test_ter_material_count_offset_and_table(tmp_path):
    zip_path = tmp_path / "valid_table.zip"
    create_synthetic_canary(zip_path, "test_level")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        content = zf.read("levels/test_level/test_level.ter")
    import struct
    version = content[0]
    assert version == 9
    size = struct.unpack_from('<I', content, 1)[0]
    expected_offset = 1 + 4 + (size * size * 2) + (size * size)
    mat_count = struct.unpack_from('<I', content, expected_offset)[0]
    assert mat_count == 2
    offset = expected_offset + 4
    names = []
    for _ in range(mat_count):
        nlen = struct.unpack_from('B', content, offset)[0]  # u8 length prefix!
        offset += 1
        nstr = content[offset:offset+nlen].decode('utf-8')
        offset += nlen
        names.append(nstr)
    assert names == ["asphalt", "grass"]
    assert offset == len(content)


def test_old_u32_name_length_encoding_fails(tmp_path):
    # Old B1.1a u32 name length encoding (e.g. 07 00 00 00 asphalt) should fail
    zip_path = tmp_path / "old_u32.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                import struct
                size = struct.unpack_from('<I', content, 1)[0]
                hdr_len = 1 + 4 + (size * size * 2) + (size * size)
                # Re-encode tail using old u32 length prefix
                new_ter = bytearray(content[:hdr_len])
                new_ter += struct.pack('<I', 2) # mat_count
                new_ter += struct.pack('<I', 7) + b'asphalt'
                new_ter += struct.pack('<I', 5) + b'grass'
                content = bytes(new_ter)
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed


def test_ter_zero_length_name_fails(tmp_path):
    zip_path = tmp_path / "zero_len.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                import struct
                size = struct.unpack_from('<I', content, 1)[0]
                hdr_len = 1 + 4 + (size * size * 2) + (size * size)
                new_ter = bytearray(content[:hdr_len])
                new_ter += struct.pack('<I', 1) # mat_count
                new_ter += struct.pack('B', 0)  # zero-length name!
                content = bytes(new_ter)
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed
    assert "Zero-length" in link_check.message or "Error" in link_check.message


def test_ter_invalid_utf8_fails(tmp_path):
    zip_path = tmp_path / "invalid_utf8.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                import struct
                size = struct.unpack_from('<I', content, 1)[0]
                hdr_len = 1 + 4 + (size * size * 2) + (size * size)
                new_ter = bytearray(content[:hdr_len])
                new_ter += struct.pack('<I', 1) # mat_count
                invalid_bytes = b'\xff\xfe\xfd'
                new_ter += struct.pack('B', len(invalid_bytes)) + invalid_bytes
                content = bytes(new_ter)
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed
    assert "Invalid UTF-8" in link_check.message or "Error" in link_check.message


def test_ter_truncated_material_count_fails(tmp_path):
    zip_path = tmp_path / "trunc_mc.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                import struct
                size = struct.unpack_from('<I', content, 1)[0]
                hdr_len = 1 + 4 + (size * size * 2) + (size * size)
                content = content[:hdr_len + 4] # mat count written, but no name_len byte
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed
    assert "Truncated" in link_check.message


def test_ter_truncated_material_name_length_fails(tmp_path):
    zip_path = tmp_path / "trunc_len.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                import struct
                size = struct.unpack_from('<I', content, 1)[0]
                hdr_len = 1 + 4 + (size * size * 2) + (size * size)
                content = content[:hdr_len + 4 + 1 + 2] # only 2 bytes of asphalt name
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed
    assert "Truncated" in link_check.message


def test_ter_truncated_material_string_fails(tmp_path):
    zip_path = tmp_path / "trunc_str.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                import struct
                size = struct.unpack_from('<I', content, 1)[0]
                hdr_len = 1 + 4 + (size * size * 2) + (size * size)
                content = content[:hdr_len + 4 + 4 + 2]
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed
    assert "Truncated" in link_check.message


def test_ter_trailing_bytes_fail(tmp_path):
    zip_path = tmp_path / "trailing.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.ter'):
                content = content + b'extra_garbage'
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    link_check = next(c for c in report.checks if c.check_name == "terrain_material_linking")
    assert not link_check.passed
    assert "Unexpected trailing bytes" in link_check.message


def test_ter_name_length_255_and_256(tmp_path):
    from packages.compiler.beamng_serializers import TerWriter, create_flat_terrain_ter
    import pytest
    ter_file = tmp_path / "test_255.ter"
    writer = TerWriter(size=128)
    name255 = "a" * 255
    writer.add_material(name255)
    hm, lm = create_flat_terrain_ter(128)
    writer.write(ter_file, hm, lm)
    assert ter_file.exists()

    writer2 = TerWriter(size=128)
    name256 = "a" * 256
    writer2.add_material(name256)
    with pytest.raises(ValueError, match="exceeds maximum"):
        writer2.write(ter_file, hm, lm)


def test_ter_name_length_255_and_256(tmp_path):
    from packages.compiler.beamng_serializers import TerWriter, create_flat_terrain_ter
    import pytest
    ter_file = tmp_path / "test_255.ter"
    writer = TerWriter(size=128)
    name255 = "a" * 255
    writer.add_material(name255)
    hm, lm = create_flat_terrain_ter(128)
    writer.write(ter_file, hm, lm)
    assert ter_file.exists()

    writer2 = TerWriter(size=128)
    name256 = "a" * 256
    writer2.add_material(name256)
    with pytest.raises(ValueError, match="exceeds maximum"):
        writer2.write(ter_file, hm, lm)


def test_stock_derived_material_table_fixture():
    # Fixture tail: 02 00 00 00 07 asphalt 05 grass
    import struct
    tail = struct.pack('<I', 2) + struct.pack('B', 7) + b'asphalt' + struct.pack('B', 5) + b'grass'
    assert len(tail) == 18
    mat_count = struct.unpack_from('<I', tail, 0)[0]
    assert mat_count == 2
    offset = 4
    names = []
    for _ in range(mat_count):
        nlen = struct.unpack_from('B', tail, offset)[0]
        offset += 1
        nstr = tail[offset:offset+nlen].decode('utf-8')
        offset += nlen
        names.append(nstr)
    assert names == ["asphalt", "grass"]
    assert offset == len(tail)


def test_exact_b12_dae_material_package_passes(tmp_path):
    zip_path = tmp_path / "valid_b12.zip"
    create_synthetic_canary(zip_path, "test_level")
    report = validate_zip_structure(zip_path)
    dae_check = next(c for c in report.checks if c.check_name == "dae_material_linking")
    assert dae_check.passed, f"Expected dae_material_linking to pass: {dae_check.message}"
    mat_check = next(c for c in report.checks if c.check_name == "material_schema")
    assert mat_check.passed, f"Expected material_schema to pass: {mat_check.message}"


def test_missing_road_main_materials_json_fails(tmp_path):
    zip_path = tmp_path / "no_road_mat.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            if "art/shapes/roads/main.materials.json" not in item.filename:
                zf_out.writestr(item, zf_in.read(item.filename))
    report = validate_zip_structure(zip_path)
    dae_check = next(c for c in report.checks if c.check_name == "dae_material_linking")
    assert not dae_check.passed
    assert "Missing road main.materials.json" in dae_check.message


def test_missing_ordinary_material_fails(tmp_path):
    zip_path = tmp_path / "no_ord_mat.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                content = json.dumps({}).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    dae_check = next(c for c in report.checks if c.check_name == "dae_material_linking")
    assert not dae_check.passed


def test_class_terrainmaterial_used_for_dae_fails(tmp_path):
    zip_path = tmp_path / "tm_for_dae.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                mat_data["triworld_road_asphalt"]["class"] = "TerrainMaterial"
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    dae_check = next(c for c in report.checks if c.check_name == "dae_material_linking")
    assert not dae_check.passed
    assert "class TerrainMaterial" in dae_check.message or "Missing ordinary Material" in dae_check.message


def test_mapto_mismatch_fails(tmp_path):
    zip_path = tmp_path / "mapto_mismatch.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                mat_data["triworld_road_asphalt"]["mapTo"] = "different_mapto"
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    dae_check = next(c for c in report.checks if c.check_name == "dae_material_linking")
    assert not dae_check.passed


def test_duplicate_mapto_fails(tmp_path):
    zip_path = tmp_path / "dup_mapto.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                mat_data["triworld_road_asphalt_2"] = dict(mat_data["triworld_road_asphalt"])
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    mat_check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not mat_check.passed
    assert "Duplicate ordinary Material.mapTo" in mat_check.message


def test_missing_stages_fails(tmp_path):
    zip_path = tmp_path / "no_stages.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                del mat_data["triworld_road_asphalt"]["Stages"]
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    mat_check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not mat_check.passed
    assert "missing or empty Stages" in mat_check.message


def test_missing_basecolormap_fails(tmp_path):
    zip_path = tmp_path / "no_bcm.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                del mat_data["triworld_road_asphalt"]["Stages"][0]["baseColorMap"]
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    mat_check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not mat_check.passed
    assert "missing baseColorMap" in mat_check.message


def test_missing_normalmap_fails(tmp_path):
    zip_path = tmp_path / "no_nm.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                del mat_data["triworld_road_asphalt"]["Stages"][0]["normalMap"]
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    mat_check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not mat_check.passed
    assert "missing normalMap" in mat_check.message


def test_missing_roughnessmap_fails(tmp_path):
    zip_path = tmp_path / "no_rm.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                del mat_data["triworld_road_asphalt"]["Stages"][0]["roughnessMap"]
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    mat_check = next(c for c in report.checks if c.check_name == "material_schema")
    assert not mat_check.passed
    assert "missing roughnessMap" in mat_check.message


def test_missing_stock_texture_fails(tmp_path):
    zip_path = tmp_path / "bad_stock_tex.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                mat_data["triworld_road_asphalt"]["Stages"][0]["baseColorMap"] = "/levels/italy/nonexistent_texture.png"
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    stock_assets = set(["levels/italy/art/terrains/t_asphalt_02_b.png", "levels/italy/art/terrains/t_asphalt_02_nm.png", "levels/italy/art/terrains/t_asphalt_02_r.png"])
    report = validate_zip_structure(zip_path, stock_assets=stock_assets)
    tex_check = next(c for c in report.checks if c.check_name == "material_textures")
    assert not tex_check.passed


def test_collada_primitive_symbol_mismatch_fails(tmp_path):
    zip_path = tmp_path / "dae_sym_mismatch.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.dae'):
                content = content.replace(b'material="triworld_road_asphalt"', b'material="unbound_symbol"')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    dae_check = next(c for c in report.checks if c.check_name == "dae_material_linking")
    assert not dae_check.passed
    assert "Collada primitive symbol mismatch" in dae_check.message or "no matching ordinary Material" in dae_check.message


def test_collada_instance_material_target_mismatch_fails(tmp_path):
    zip_path = tmp_path / "dae_tgt_mismatch.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if item.filename.endswith('.dae'):
                content = content.replace(b'target="#triworld_road_asphalt-mat"', b'target="#missing_mat_target"')
            zf_out.writestr(item, content)
    report = validate_zip_structure(zip_path)
    dae_check = next(c for c in report.checks if c.check_name == "dae_material_linking")
    assert not dae_check.passed
    assert "Collada instance_material target mismatch" in dae_check.message


def test_stock_texture_png_link_resolution_passes(tmp_path):
    zip_path = tmp_path / "png_link.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                mat_data["triworld_road_asphalt"]["Stages"][0]["baseColorMap"] = "/levels/italy/art/terrains/test_texture.png"
                mat_data["triworld_road_asphalt"]["Stages"][0]["normalMap"] = "/levels/italy/art/terrains/test_normal.png"
                mat_data["triworld_road_asphalt"]["Stages"][0]["roughnessMap"] = "/levels/italy/art/terrains/test_roughness.png"
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    stock_assets = set([
        "levels/italy/art/terrains/test_texture.png.link",
        "levels/italy/art/terrains/test_normal.png.link",
        "levels/italy/art/terrains/test_roughness.png.link",
        "levels/italy/art/terrains/t_terrain_base_asphalt_ao.png",
        "levels/italy/art/terrains/t_asphalt_02_ao.png",
        "levels/italy/art/terrains/t_macro_asphalt_ao.png",
        "levels/italy/art/terrains/t_terrain_base_asphalt_b.png",
        "levels/italy/art/terrains/t_asphalt_02_b.png",
        "levels/italy/art/terrains/t_macro_asphalt_b.png",
        "levels/italy/art/terrains/t_terrain_base_asphalt_h.png",
        "levels/italy/art/terrains/t_asphalt_02_h.png",
        "levels/italy/art/terrains/t_macro_asphalt_h.png",
        "levels/italy/art/terrains/t_terrain_base_asphalt_nm.png",
        "levels/italy/art/terrains/t_asphalt_02_nm.png",
        "levels/italy/art/terrains/t_macro_asphalt_nm.png",
        "levels/italy/art/terrains/t_terrain_base_asphalt_r.png",
        "levels/italy/art/terrains/t_asphalt_02_r.png",
        "levels/italy/art/terrains/t_macro_asphalt_r.png",
        "levels/italy/art/terrains/t_terrain_base_ao.png",
        "levels/italy/art/terrains/t_dirt_dry_grassy_ao.png.link",
        "levels/italy/art/terrains/t_macro_grass2_ao.png",
        "levels/italy/art/terrains/t_terrain_base_b.png",
        "levels/italy/art/terrains/t_dirt_dry_grassy_b.png.link",
        "levels/italy/art/terrains/t_macro_grass2_b.png",
        "levels/italy/art/terrains/t_terrain_base_h.png",
        "levels/italy/art/terrains/t_dirt_dry_grassy_h.png.link",
        "levels/italy/art/terrains/t_macro_grass2_h.png",
        "levels/italy/art/terrains/t_terrain_base_nm.png",
        "levels/italy/art/terrains/t_dirt_dry_grassy_nm.png.link",
        "levels/italy/art/terrains/t_macro_grass2_nm.png",
        "levels/italy/art/terrains/t_terrain_base_r.png",
        "levels/italy/art/terrains/t_dirt_dry_grassy_r.png.link",
        "levels/italy/art/terrains/t_macro_grass2_r.png"
    ])
    report = validate_zip_structure(zip_path, stock_assets=stock_assets)
    tex_check = next(c for c in report.checks if c.check_name == "material_textures")
    assert tex_check.passed, f"Expected material_textures to pass with .png.link in stock_assets: {tex_check.message}"


def test_genuinely_missing_stock_texture_fails(tmp_path):
    zip_path = tmp_path / "genuinely_missing.zip"
    valid_zip = tmp_path / "valid.zip"
    create_synthetic_canary(valid_zip, "test_level")
    with zipfile.ZipFile(valid_zip, 'r') as zf_in, zipfile.ZipFile(zip_path, 'w') as zf_out:
        for item in zf_in.infolist():
            content = zf_in.read(item.filename)
            if "art/shapes/roads/main.materials.json" in item.filename:
                mat_data = json.loads(content)
                mat_data["triworld_road_asphalt"]["Stages"][0]["baseColorMap"] = "/levels/italy/art/terrains/completely_missing_texture.png"
                content = json.dumps(mat_data).encode('utf-8')
            zf_out.writestr(item, content)
    stock_assets = set([
        "levels/italy/art/terrains/t_asphalt_02_b.png",
        "levels/italy/art/terrains/t_asphalt_02_nm.png",
        "levels/italy/art/terrains/t_asphalt_02_r.png"
    ])
    report = validate_zip_structure(zip_path, stock_assets=stock_assets)
    tex_check = next(c for c in report.checks if c.check_name == "material_textures")
    assert not tex_check.passed
    assert "completely_missing_texture.png" in str(tex_check.details.get("missing", []))
