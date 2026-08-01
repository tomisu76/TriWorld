import tempfile
import zipfile
import hashlib
import json
from pathlib import Path

from packages.compiler.synthetic_canary import create_synthetic_canary


def test_create_synthetic_canary():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_zip = Path(tmpdir) / "test_canary.zip"
        file_hashes = create_synthetic_canary(output_zip, "test_level")
        
        # Check that the zip file was created
        assert output_zip.exists()
        
        # Check that the zip is not empty
        assert output_zip.stat().st_size > 0
        
        # Check that the returned hashes are non-empty
        assert len(file_hashes) > 0
        
        # Optionally, check a few known files exist in the zip
        with zipfile.ZipFile(output_zip, 'r') as zf:
            namelist = zf.namelist()
            # Check for expected files
            assert "levels/test_level/info.json" in namelist
            assert "levels/test_level/test_level.ter" in namelist
            assert "levels/test_level/art/shapes/roads/straight_road.dae" in namelist
            assert "levels/test_level/main/items.level.json" in namelist
            assert "levels/test_level/main/MissionGroup/items.level.json" in namelist
            assert "levels/test_level/main/MissionGroup/Level_objects/items.level.json" in namelist
            assert "levels/test_level/main/MissionGroup/PlayerDropPoints/items.level.json" in namelist
            assert "levels/test_level/main/MissionGroup/Spawnpoints/items.level.json" not in namelist
            assert "levels/test_level/main/MissionGroup/spawnpoints/items.level.json" not in namelist
            assert "levels/test_level/main/MissionGroup/Roads/items.level.json" in namelist
            assert "levels/test_level/main/MissionGroup/AI/items.level.json" in namelist
            assert "levels/test_level/reports/build-manifest.json" in namelist
            assert "levels/test_level/reports/validation.json" in namelist

            # Check MissionGroup items.level.json for PlayerDropPoints SimGroup
            mg_content = zf.read("levels/test_level/main/MissionGroup/items.level.json").decode("utf-8")
            assert '"name":"PlayerDropPoints"' in mg_content or '"name": "PlayerDropPoints"' in mg_content
            assert '"name":"Spawnpoints"' not in mg_content and '"name": "Spawnpoints"' not in mg_content
            assert '"name":"spawnpoints"' not in mg_content and '"name": "spawnpoints"' not in mg_content

            # Check PlayerDropPoints/items.level.json for SpawnSphere
            pdp_content = zf.read("levels/test_level/main/MissionGroup/PlayerDropPoints/items.level.json").decode("utf-8")
            pdp_obj = json.loads(pdp_content)
            assert pdp_obj["class"] == "SpawnSphere"
            assert pdp_obj["name"] == "spawn_001"
            assert pdp_obj["__parent"] == "PlayerDropPoints"
            assert pdp_obj["position"] == [50.0, 250.0, 0.5]
            
            # Validate JSON files
            info_json = json.loads(zf.read("levels/test_level/info.json"))
            assert info_json["title"] == "TriWorld Phase 2 Canary"
            assert info_json["authors"] == "TriWorld"
            assert "version" not in info_json  # legacy field removed
            assert "name" not in info_json     # legacy field removed
            assert "author" not in info_json   # legacy field removed
            assert "previewImage" not in info_json  # legacy field removed
            assert "missionFile" not in info_json   # legacy field removed
            assert "previews" in info_json
            assert info_json["previews"] == ["preview.png"]
            
            validation_json = json.loads(zf.read("levels/test_level/reports/validation.json"))
            assert validation_json["structural_validation"] == "passed"
            assert validation_json["beamng_runtime_validation"] == "not_run"
            # Gates: some are not_applicable for synthetic canary, some passed
            assert validation_json["gates"]["terrain"] == "passed"
            assert validation_json["gates"]["beamngTarget"] == "passed"
            assert validation_json["gates"]["assets"] == "passed"
            assert validation_json["gates"]["licenses"] == "passed"
            assert validation_json["gates"]["ir"] == "not_applicable"
            assert validation_json["gates"]["civil"] == "not_applicable"
            assert validation_json["gates"]["mesh"] == "not_applicable"
            assert validation_json["gates"]["zip"] == "not_run"
            
            manifest = json.loads(zf.read("levels/test_level/reports/build-manifest.json"))
            assert manifest["requestHash"] == "synthetic_canary"
            assert manifest["compilerVersion"] == "0.1.0"
            assert manifest["seed"] == 184467
            assert manifest["projection"]["crs"] == "LOCAL"
            assert manifest["projection"]["squareSize"] == 2.0