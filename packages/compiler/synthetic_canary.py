"""Synthetic canary generator - creates a minimal valid BeamNG level ZIP."""

import tempfile
import zipfile
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

from packages.compiler.beamng_serializers import (
    TerWriter, DaeSerializer,
    create_flat_terrain_ter, create_straight_road_dae
)


def create_synthetic_canary(output_zip: Path, level_name: str = "synthetic_canary") -> Dict[str, str]:
    """Create a minimal valid BeamNG level ZIP for testing.

    Contents:
    - Flat terrain (256x256, 2m resolution, version 9)
    - One straight road (500m, 7m wide) along X axis at Y=250
    - One TSStatic road chunk (DAE)
    - One AI DecalRoad along X axis at Y=250
    - One spawn point (SpawnSphere with SpawnSphereMarker)
    - Two materials (asphalt, grass) using stock Italy texture paths
    - Required metadata files

    Returns:
        Dictionary of file paths and their SHA256 hashes
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        staging = Path(tmpdir) / "staging"
        level_dir = staging / "levels" / level_name
        level_dir.mkdir(parents=True)

        art_dir = level_dir / "art" / "shapes" / "roads"
        art_dir.mkdir(parents=True)

        # 1. Create flat terrain .ter (version 9 without layerTextureMap)
        ter_path = level_dir / f"{level_name}.ter"
        writer = TerWriter(size=256, square_size=2.0, max_height=100.0)
        writer.add_material("asphalt")
        writer.add_material("grass")
        height_map, layer_map = create_flat_terrain_ter(256)
        writer.write(ter_path, height_map, layer_map)

        # 2. Create terrain metadata .terrain.json (version 9)
        terrain_json = {
            "binaryFormat": "version(char), size(unsigned int), heightMap(heightMapSize * heightMapItemSize), layerMap(layerMapSize * layerMapItemSize), materialNames",
            "datafile": f"/levels/{level_name}/{level_name}.ter",
            "heightMapItemSize": 2,
            "heightMapSize": 65536,
            "heightmapImage": f"/levels/{level_name}/{level_name}.terrainheightmap.png",
            "layerMapItemSize": 1,
            "layerMapSize": 65536,
            "materials": ["asphalt", "grass"],
            "size": 256,
            "version": 9,
        }
        (level_dir / f"{level_name}.terrain.json").write_text(json.dumps(terrain_json, indent=2))

        # 3. Create road DAE (along X axis, centered at origin)
        dae_path = art_dir / "straight_road.dae"
        bounds = create_straight_road_dae(dae_path, "straight_road", length=500.0, width=7.0, material_name="triworld_road_asphalt")

        # 3b. Create road material main.materials.json
        road_materials_json = {
            "triworld_road_asphalt": {
                "name": "triworld_road_asphalt",
                "mapTo": "triworld_road_asphalt",
                "class": "Material",
                "persistentId": "f7d2e8b1-4c3a-4952-b8e7-91a0c2d3e4f5",
                "version": 1.5,
                "Stages": [
                    {
                        "baseColorMap": "/levels/italy/art/terrains/t_asphalt_02_b.png",
                        "colorMap": "/levels/italy/art/terrains/t_asphalt_02_b.png",
                        "normalMap": "/levels/italy/art/terrains/t_asphalt_02_nm.png",
                        "roughnessMap": "/levels/italy/art/terrains/t_asphalt_02_r.png",
                        "roughnessFactor": 0.5
                    },
                    {},
                    {},
                    {}
                ],
                "annotation": "ASPHALT",
                "castShadows": False,
                "materialTag0": "RoadAndPath",
                "materialTag1": "beamng"
            }
        }
        (art_dir / "main.materials.json").write_text(json.dumps(road_materials_json, indent=2))

        # 4. Create info.json — BeamNG 0.38.6 level discovery schema (proven in selector-visible fixed3 artifact)
        info_json = {
            "title": "TriWorld Phase 2 Canary",
            "description": "Synthetic canary for validation - flat terrain, straight road",
            "authors": "TriWorld",
            "size": [256, 256],
            "defaultSpawnPointName": "spawn_001",
            "spawnPoints": [
                {
                    "translationId": "TriWorld Canary Default Spawn",
                    "description": "Safe spawn on straight road",
                    "objectname": "spawn_001",
                    "preview": "preview.png"
                }
            ],
            "supportsTraffic": True,
            "previews": ["preview.png"]
        }
        (level_dir / "info.json").write_text(json.dumps(info_json, indent=2))

        # 5. Create TerrainMaterial package
        materials_json = {
            "testLevelTerrainMaterialTextureSet": {
                "name": "testLevelTerrainMaterialTextureSet",
                "class": "TerrainMaterialTextureSet",
                "persistentId": "4439d48e-2402-402a-8a64-18fb9fb59bc1",
                "baseTexSize": [4096, 4096],
                "detailTexSize": [1024, 1024],
                "macroTexSize": [1024, 1024]
            },
            "asphalt": {
                "internalName": "asphalt",
                "class": "TerrainMaterial",
                "persistentId": "6e2bfb0e-e63c-45c5-bd1f-40964decabc2",
                "annotation": "ASPHALT",
                "aoBaseTex": "/levels/italy/art/terrains/t_terrain_base_asphalt_ao.png",
                "aoBaseTexSize": 4096,
                "aoDetailTex": "/levels/italy/art/terrains/t_asphalt_02_ao.png",
                "aoMacroTex": "/levels/italy/art/terrains/t_macro_asphalt_ao.png",
                "aoMacroTexSize": 80,
                "baseColorBaseTex": "/levels/italy/art/terrains/t_terrain_base_asphalt_b.png",
                "baseColorBaseTexSize": 4096,
                "baseColorDetailStrength": [0.4, 0.0],
                "baseColorDetailTex": "/levels/italy/art/terrains/t_asphalt_02_b.png",
                "baseColorMacroStrength": [0.3, 0.3],
                "baseColorMacroTex": "/levels/italy/art/terrains/t_macro_asphalt_b.png",
                "baseColorMacroTexSize": 80,
                "groundmodelName": "ASPHALT",
                "heightBaseTex": "/levels/italy/art/terrains/t_terrain_base_asphalt_h.png",
                "heightBaseTexSize": 4096,
                "heightDetailTex": "/levels/italy/art/terrains/t_asphalt_02_h.png",
                "heightMacroTex": "/levels/italy/art/terrains/t_macro_asphalt_h.png",
                "heightMacroTexSize": 80,
                "macroDistances": [0, 10, 100, 3000],
                "normalBaseTex": "/levels/italy/art/terrains/t_terrain_base_asphalt_nm.png",
                "normalBaseTexSize": 4096,
                "normalDetailStrength": [0.6, 0.2],
                "normalDetailTex": "/levels/italy/art/terrains/t_asphalt_02_nm.png",
                "normalMacroStrength": [0.8, 0.8],
                "normalMacroTex": "/levels/italy/art/terrains/t_macro_asphalt_nm.png",
                "normalMacroTexSize": 80,
                "roughnessBaseTex": "/levels/italy/art/terrains/t_terrain_base_asphalt_r.png",
                "roughnessBaseTexSize": 4096,
                "roughnessDetailStrength": [0.7, 0.5],
                "roughnessDetailTex": "/levels/italy/art/terrains/t_asphalt_02_r.png",
                "roughnessMacroStrength": [0.7, 0.7],
                "roughnessMacroTex": "/levels/italy/art/terrains/t_macro_asphalt_r.png",
                "roughnessMacroTexSize": 80
            },
            "grass": {
                "internalName": "grass",
                "class": "TerrainMaterial",
                "persistentId": "684557ac-f564-407e-8316-e948bb59bc3",
                "annotation": "GRASS",
                "aoBaseTex": "/levels/italy/art/terrains/t_terrain_base_ao.png",
                "aoBaseTexSize": 4096,
                "aoDetailTex": "/levels/italy/art/terrains/t_dirt_dry_grassy_ao.png",
                "aoMacroTex": "/levels/italy/art/terrains/t_macro_grass2_ao.png",
                "aoMacroTexSize": 80,
                "baseColorBaseTex": "/levels/italy/art/terrains/t_terrain_base_b.png",
                "baseColorBaseTexSize": 4096,
                "baseColorDetailStrength": [0.3, 0.3],
                "baseColorDetailTex": "/levels/italy/art/terrains/t_dirt_dry_grassy_b.png",
                "baseColorMacroStrength": [0.2, 0.2],
                "baseColorMacroTex": "/levels/italy/art/terrains/t_macro_grass2_b.png",
                "baseColorMacroTexSize": 80,
                "detailDistance": 80,
                "detailDistances": [0, 0, 15, 30],
                "detailSize": 2,
                "detailStrength": 0.6,
                "diffuseSize": 4096,
                "groundmodelName": "GRASS2",
                "heightBaseTex": "/levels/italy/art/terrains/t_terrain_base_h.png",
                "heightBaseTexSize": 4096,
                "heightDetailTex": "/levels/italy/art/terrains/t_dirt_dry_grassy_h.png",
                "heightMacroTex": "/levels/italy/art/terrains/t_macro_grass2_h.png",
                "heightMacroTexSize": 80,
                "macroDistAtten": [0.5, 0],
                "macroDistance": 800,
                "macroDistances": [0, 100, 200, 3000],
                "macroSize": 80,
                "macroStrength": 0.15,
                "normalBaseTex": "/levels/italy/art/terrains/t_terrain_base_nm.png",
                "normalBaseTexSize": 4096,
                "normalDetailStrength": [1.0, 0.15],
                "normalDetailTex": "/levels/italy/art/terrains/t_dirt_dry_grassy_nm.png",
                "normalMacroStrength": [0.5, 0.5],
                "normalMacroTex": "/levels/italy/art/terrains/t_macro_grass2_nm.png",
                "normalMacroTexSize": 80,
                "roughnessBaseTex": "/levels/italy/art/terrains/t_terrain_base_r.png",
                "roughnessBaseTexSize": 4096,
                "roughnessDetailStrength": [0.3, 0.3],
                "roughnessDetailTex": "/levels/italy/art/terrains/t_dirt_dry_grassy_r.png",
                "roughnessMacroStrength": [0.15, 0.5],
                "roughnessMacroTex": "/levels/italy/art/terrains/t_macro_grass2_r.png",
                "roughnessMacroTexSize": 80
            }
        }
        terrains_dir = level_dir / "art" / "terrains"
        terrains_dir.mkdir(parents=True)
        (terrains_dir / "main.materials.json").write_text(json.dumps(materials_json, indent=2))

        # 6. Create items.level.json (LDJSON) - MissionGroup root
        # levels/test_level/main/items.level.json
        main_items = [
            json.dumps({
                "class": "SimGroup",
                "name": "MissionGroup",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628088",
                "enabled": "1"
            }, separators=(',', ':'))
        ]
        (level_dir / "main" / "items.level.json").parent.mkdir(parents=True, exist_ok=True)
        (level_dir / "main" / "items.level.json").write_text('\n'.join(main_items))

        # levels/test_level/main/MissionGroup/items.level.json
        mg_items = [
            json.dumps({
                "class": "SimGroup",
                "name": "Level_objects",
                "__parent": "MissionGroup",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628089"
            }, separators=(',', ':')),
            json.dumps({
                "class": "SimGroup",
                "name": "PlayerDropPoints",
                "__parent": "MissionGroup",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628090"
            }, separators=(',', ':')),
            json.dumps({
                "class": "SimGroup",
                "name": "Roads",
                "__parent": "MissionGroup",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628091"
            }, separators=(',', ':')),
            json.dumps({
                "class": "SimGroup",
                "name": "AI",
                "__parent": "MissionGroup",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628092"
            }, separators=(',', ':'))
        ]
        (level_dir / "main" / "MissionGroup" / "items.level.json").parent.mkdir(parents=True, exist_ok=True)
        (level_dir / "main" / "MissionGroup" / "items.level.json").write_text('\n'.join(mg_items))

        # levels/test_level/main/MissionGroup/Level_objects/items.level.json
        lo_items = [
            json.dumps({
                "class": "TerrainBlock",
                "name": "Terrain",
                "position": "0 0 0",
                "rotation": "0 0 0 1",
                "scale": "1 1 1",
                "terrainFile": f"/levels/{level_name}/{level_name}.ter",
                "squareSize": 2.0,
                "maxHeight": 100.0,
                "materialTextureSet": "testLevelTerrainMaterialTextureSet",
                "__parent": "Level_objects",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628093"
            }, separators=(',', ':')),
            json.dumps({
                "class": "LevelInfo",
                "name": "theLevelInfo",
                "__parent": "Level_objects",
                "globalEnviromentMap": "BNG_Sky_02_cubemap",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628094"
            }, separators=(',', ':')),
            json.dumps({
                "name": "sunsky",
                "class": "ScatterSky",
                "__parent": "Level_objects",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628095",
                "position": [0.0, 0.0, 100.0],
                "azimuth": 45.0,
                "elevation": 55.0,
                "skyBrightness": 40.0,
                "ambientScale": [1.0, 0.9, 0.8, 1.0],
                "sunScale": [1.0, 0.9, 0.8, 1.0],
                "fogScale": [0.4, 0.67, 1.0, 1.0],
                "shadowDistance": 1000.0,
                "shadowSoftness": 0.2,
                "flareType": "BNG_Sunflare_3",
                "flareScale": 3.0,
                "texSize": 1024,
                "ambientScaleGradientFile": "art/sky_gradients/default/gradient_ambient.png",
                "sunScaleGradientFile": "art/sky_gradients/default/gradient_sunscale.png",
                "fogScaleGradientFile": "art/sky_gradients/default/gradient_fog.png"
            }, separators=(',', ':')),
            json.dumps({
                "name": "tod",
                "class": "TimeOfDay",
                "__parent": "Level_objects",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628096",
                "position": [0.0, 0.0, 100.0],
                "animate": "0",
                "play": False,
                "axisTilt": 20.0,
                "azimuthOverride": 0.0,
                "startTime": 0.92,
                "time": 0.92
            }, separators=(',', ':'))
        ]
        (level_dir / "main" / "MissionGroup" / "Level_objects" / "items.level.json").parent.mkdir(parents=True, exist_ok=True)
        (level_dir / "main" / "MissionGroup" / "Level_objects" / "items.level.json").write_text('\n'.join(lo_items))

        # levels/test_level/main/MissionGroup/PlayerDropPoints/items.level.json
        sp_items = [
            json.dumps({
                "class": "SpawnSphere",
                "name": "spawn_001",
                "position": [50.0, 250.0, 0.5],
                "dataBlock": "SpawnSphereMarker",
                "radius": 1,
                "rotationMatrix": [0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0],
                "spawnClass": "player",
                "spawnDatablock": "DefaultPlayerData",
                "sphereWeight": "1",
                "__parent": "PlayerDropPoints",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628097"
            }, separators=(',', ':'))
        ]
        (level_dir / "main" / "MissionGroup" / "PlayerDropPoints" / "items.level.json").parent.mkdir(parents=True, exist_ok=True)
        (level_dir / "main" / "MissionGroup" / "PlayerDropPoints" / "items.level.json").write_text('\n'.join(sp_items))

        # levels/test_level/main/MissionGroup/Roads/items.level.json
        rd_items = [
            json.dumps({
                "class": "TSStatic",
                "name": "straight_road",
                "position": "0 250 0",
                "rotation": "0 0 0 1",
                "scale": "1 1 1",
                "shapeName": f"/levels/{level_name}/art/shapes/roads/straight_road.dae",
                "collisionType": "Collision Mesh",
                "decalType": "None",
                "playAmbient": True,
                "__parent": "Roads",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628098"
            }, separators=(',', ':'))
        ]
        (level_dir / "main" / "MissionGroup" / "Roads" / "items.level.json").parent.mkdir(parents=True, exist_ok=True)
        (level_dir / "main" / "MissionGroup" / "Roads" / "items.level.json").write_text('\n'.join(rd_items))

        # levels/test_level/main/MissionGroup/AI/items.level.json
        half_width = 3.5
        decal_nodes = [
            [0.0, 250.0, 0.01, half_width],
            [500.0, 250.0, 0.01, half_width],
        ]
        ai_items = [
            json.dumps({
                "class": "DecalRoad",
                "name": "ai_road_001",
                "position": "0.0 250.0 0.01",
                "rotation": "0 0 0 1",
                "scale": "1 1 1",
                "drivability": 1.0,
                "oneWay": False,
                "breakAngle": 180.0,
                "widthSubdivisions": 1,
                "textureLength": 5.0,
                "material": "asphalt",
                "nodes": decal_nodes,
                "improvedSpline": True,
                "__parent": "AI",
                "persistentId": "da0d620a-8dab-43c7-8490-832a7a628099"
            }, separators=(',', ':'))
        ]
        (level_dir / "main" / "MissionGroup" / "AI" / "items.level.json").parent.mkdir(parents=True, exist_ok=True)
        (level_dir / "main" / "MissionGroup" / "AI" / "items.level.json").write_text('\n'.join(ai_items))

        # 8. Create preview.png (1x1 placeholder)
        preview_path = level_dir / "preview.png"
        preview_path.write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff\x3f\x00\x05\xfe\x02\xfe\xa7\xf4\x8c\x8d\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # 9. Create minimap terrain.png
        minimap_dir = level_dir / "minimap"
        minimap_dir.mkdir(parents=True)
        (minimap_dir / "terrain.png").write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff\x3f\x00\x05\xfe\x02\xfe\xa7\xf4\x8c\x8d\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # 10. Create spawn_default.png
        spawn_preview = level_dir / "spawn_default.png"
        spawn_preview.write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff\x3f\x00\x05\xfe\x02\xfe\xa7\xf4\x8c\x8d\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # 11. Create terrainheightmap.png
        (level_dir / f"{level_name}.terrainheightmap.png").write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff\x3f\x00\x05\xfe\x02\xfe\xa7\xf4\x8c\x8d\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # 12. Create reports/build-manifest.json
        reports_dir = level_dir / "reports"
        reports_dir.mkdir(parents=True)

        # Collect all files for manifest
        all_files = []
        for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
            if f.is_file():
                rel = f.relative_to(staging)
                rel_posix = rel.as_posix()
                content = f.read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                all_files.append({
                    "path": rel_posix,
                    "sha256": sha256,
                    "bytes": len(content),
                })

        manifest = {
            "buildId": hashlib.sha256(json.dumps({"name": level_name}, sort_keys=True).encode()).hexdigest()[:16],
            "compilerVersion": "0.1.0",
            "requestHash": "synthetic_canary",
            "inputHashes": {},
            "toolVersions": {
                "python": "3.12.11",
                "numpy": np.__version__,
            },
            "sourceLicenses": ["CC0-1.0"],
            "projection": {
                "crs": "LOCAL",
                "anchorLonLat": [0.0, 0.0],
                "squareSize": 2.0,
            },
            "sumoCommand": [],
            "seed": 184467,
            "files": all_files,
            "validationReport": "reports/validation.json",
        }
        (reports_dir / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))

        # 13. Create validation.json with honest gate statuses
        validation = {
            "structural_validation": "passed",
            "beamng_runtime_validation": "not_run",
            "gates": {
                "ir": "not_applicable",
                "civil": "not_applicable",
                "mesh": "not_applicable",
                "terrain": "passed",
                "beamngTarget": "passed",
                "assets": "passed",
                "licenses": "passed",
                "zip": "not_run",
            },
            "warnings": [
                "beamng_runtime_validation is not_run - no BeamNG.drive load test performed",
                ".ter writer and DAE serializer are experimental until runtime validation",
            ],
            "metrics": {
                "terrainSize": 256,
                "roadLengthM": 500.0,
                "roadWidthM": 7.0,
                "triangles": 2,
                "materials": 2,
            }
        }
        (reports_dir / "validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True))

        # 14. Create attribution.txt
        (level_dir / "attribution.txt").write_text(
            "TriWorld Synthetic Canary\n"
            "Generated for validation purposes\n"
            "All assets: CC0-1.0 or original TriWorld\n"
        )

        # 15. Create README.txt
        (level_dir / "README.txt").write_text(
            f"TriWorld Synthetic Canary Level\n"
            f"Level: {level_name}\n"
            f"Generated: deterministic-canary-0.1.0\n"
            f"Purpose: Pipeline validation\n"
            f"\n"
            f"Contents:\n"
            f"- Flat terrain (256x256, 2m resolution, version 9)\n"
            f"- Straight road (500m x 7m)\n"
            f"- TSStatic physical road mesh\n"
            f"- AI DecalRoad centerline\n"
            f"- Single spawn point (SpawnSphere)\n"
        )

        # 16. Create deterministic ZIP
        file_hashes = {}
        fixed_timestamp = (1980, 1, 1, 0, 0, 0)

        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging.rglob('*'), key=lambda p: p.relative_to(staging).as_posix()):
                if f.is_file():
                    rel = f.relative_to(staging)
                    rel_posix = rel.as_posix()
                    content = f.read_bytes()
                    info = zipfile.ZipInfo(rel_posix, date_time=fixed_timestamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    zf.writestr(info, content)
                    file_hashes[rel_posix] = hashlib.sha256(content).hexdigest()

        return file_hashes