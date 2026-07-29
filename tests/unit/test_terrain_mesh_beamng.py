import pytest
from packages.contracts import (
    TerrainIR, DemArtifact, VerticalDatumType,
    MeshIR, Submesh,
    TSStaticItem, DecalRoadItem, TerrainBlockItem, BeamNGTargetIR,
)


class TestTerrainIR:
    def test_dem_artifact(self):
        dem = DemArtifact(
            path="/tmp/dem.tif",
            crs="EPSG:4326",
            verticalDatum=VerticalDatumType.ELLIPSOIDAL,
            resolution=30.0,
            nodata=-32768.0,
            bbox=[0, 0, 1000, 1000],
            hash="abc123",
        )
        assert dem.verticalDatum == VerticalDatumType.ELLIPSOIDAL

    def test_terrain_ir(self):
        dem = DemArtifact(
            path="/tmp/dem.tif",
            crs="EPSG:4326",
            verticalDatum=VerticalDatumType.ELLIPSOIDAL,
            resolution=30.0,
            nodata=-32768.0,
            bbox=[0, 0, 1000, 1000],
            hash="abc123",
        )
        terrain = TerrainIR(
            originalDem=dem,
            nodataMask="/tmp/nodata.tif",
            normalizedDem="/tmp/normalized.tif",
            formationTarget="/tmp/formation.tif",
            cutFillDelta="/tmp/cutfill.tif",
            finalDem="/tmp/final.tif",
            materialMasks={"grass": "/tmp/grass.tif"},
            transform={"crs": "EPSG:32634", "affine": [1, 0, 0, 0, -1, 0]},
            statistics={"min": 0, "max": 100, "mean": 50},
        )
        assert terrain.originalDem.path == "/tmp/dem.tif"
        assert terrain.materialMasks["grass"] == "/tmp/grass.tif"


class TestMeshIR:
    def test_submesh(self):
        submesh = Submesh(
            name="road_surface",
            materialSlot=0,
            indexStart=0,
            indexCount=6,
        )
        assert submesh.indexCount == 6

    def test_mesh_ir(self):
        mesh = MeshIR(
            id="road_chunk_001",
            positions=[[0, 0, 0], [10, 0, 0], [10, 7, 0], [0, 7, 0]],
            normals=[[0, 0, 1]] * 4,
            uv0=[[0, 0], [1, 0], [1, 1], [0, 1]],
            indices=[0, 1, 2, 0, 2, 3],
            materialSlots=["asphalt"],
            submeshes=[Submesh(name="surface", materialSlot=0, indexStart=0, indexCount=6)],
            collisionClass="road_surface",
            lodClass="a300",
            bounds={"min": [0, 0, 0], "max": [10, 7, 0]},
            sourceIds=["road_001"],
        )
        assert len(mesh.positions) == 4
        assert len(mesh.indices) == 6


class TestBeamNGTargetIR:
    def test_tsstatic_item(self):
        item = TSStaticItem(
            name="road_chunk_001",
            position=[100, 200, 0],
            rotation=[0, 0, 0, 1],
            shapeName="art/shapes/roads/road_chunk_001.dae",
        )
        assert item.collisionType == "Collision Mesh"

    def test_decalroad_item(self):
        item = DecalRoadItem(
            name="ai_road_001",
            position=[0, 0, 0],
            rotation=[0, 0, 0, 1],
            nodes=[[0, 0, 0, 3.5], [100, 0, 0, 3.5]],
            drivability=1.0,
            oneWay=False,
            material="asphalt",
        )
        assert len(item.nodes) == 2
        assert item.nodes[0][3] == 3.5  # halfWidth

    def test_terrain_block(self):
        block = TerrainBlockItem(
            name="terrain",
            position=[0, 0, 0],
            rotation=[0, 0, 0, 1],
            scale=[1, 1, 1],
            terrainFile="levels/test/test.ter",
            squareSize=2.0,
            maxHeight=500.0,
        )
        assert block.squareSize == 2.0

    def test_beamng_target_ir(self):
        terrain_block = TerrainBlockItem(
            name="terrain",
            position=[0, 0, 0],
            rotation=[0, 0, 0, 1],
            scale=[1, 1, 1],
            terrainFile="levels/test/test.ter",
            squareSize=2.0,
            maxHeight=500.0,
        )
        target = BeamNGTargetIR(
            terrainBlock=terrain_block,
            tsstatics=[],
            decalRoads=[],
            materials={"asphalt": {"mapTo": "asphalt"}},
            textures=[],
            spawnPoints=[],
            environment={},
        )
        assert target.terrainBlock.terrainFile == "levels/test/test.ter"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])