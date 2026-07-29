import pytest
from packages.contracts.map_request import MapCompilationRequest, MapFrame, AxisConvention, VerticalDatum, RasterConvention, QualityProfile, OutputFlavor, TrafficSide
from packages.contracts.road_ir import RoadNetworkIR, RoadSegment, RoadClass, LaneConfig, WidthConfig, SourceRef
from packages.contracts.civil_ir import CivilRoadIR, Corridor, StationFrame, JunctionPatch, BridgeDeck, TunnelPolicy, EarthworkCorridor
from packages.contracts.job_state import JobStatus, JobEvent, STAGE_WEIGHTS, compute_overall_progress


class TestMapCompilationRequest:
    def test_valid_request(self):
        req = MapCompilationRequest(
            name='test_map',
            center={'lat': 48.7212, 'lon': 18.2576},
            extent={'widthM': 1024, 'heightM': 1024},
            terrainResolutionM=2.0,
        )
        assert req.name == 'test_map'
        assert req.center['lat'] == 48.7212
        assert req.qualityProfile == QualityProfile.DRIVABLE

    def test_invalid_lat(self):
        with pytest.raises(ValueError):
            MapCompilationRequest(
                name='test',
                center={'lat': 91, 'lon': 0},
                extent={'widthM': 100, 'heightM': 100},
            )

    def test_invalid_extent(self):
        with pytest.raises(ValueError):
            MapCompilationRequest(
                name='test',
                center={'lat': 0, 'lon': 0},
                extent={'widthM': -1, 'heightM': 100},
            )


class TestMapFrame:
    def test_valid_map_frame(self):
        frame = MapFrame(
            projectedCrsWkt2='WKT2_STRING',
            projectionChoice='UTM-34N',
            anchorLonLat=[18.2576, 48.7212],
            anchorProjectedM=[0.0, 0.0],
            verticalDatum=VerticalDatum(name='WGS84', normalization='recorded-not-assumed'),
        )
        assert frame.axisConvention.x == 'east'
        assert frame.rasterConvention.row0 == 'north'


class TestRoadNetworkIR:
    def test_valid_segment(self):
        segment = RoadSegment(
            id='road_001',
            source=SourceRef(wayId=12345),
            **{'class': RoadClass.PRIMARY},
            direction='both',
            lanes=LaneConfig(forward=1, backward=1, source='osm:lanes'),
            widthM=WidthConfig(total=7.0, source='lanes*defaultLaneWidth'),
            centerlineLocalM=[[0.0, 0.0], [100.0, 0.0]],
        )
        assert segment.id == 'road_001'
        assert segment.class_ == RoadClass.PRIMARY

    def test_network_with_segments(self):
        segment = RoadSegment(
            id='road_001',
            source=SourceRef(wayId=12345),
            **{'class': RoadClass.PRIMARY},
            direction='both',
            lanes=LaneConfig(forward=1, backward=1, source='osm:lanes'),
            widthM=WidthConfig(total=7.0, source='lanes*defaultLaneWidth'),
            centerlineLocalM=[[0.0, 0.0], [100.0, 0.0]],
        )
        network = RoadNetworkIR(segments=[segment])
        assert len(network.segments) == 1


class TestCivilRoadIR:
    def test_valid_corridor(self):
        frame = StationFrame(
            station=0.0,
            xyz=[0.0, 0.0, 0.0],
            tangent=[1.0, 0.0, 0.0],
            lateral=[0.0, 1.0, 0.0],
            grade=0.0,
            curvature=0.0,
            crossfall={'left': 0.02, 'right': 0.02, 'bank': 0.0},
            crossSection={'crown': [0.0, 0.0, 0.0]},
        )
        corridor = Corridor(
            id='corridor_001',
            stations=[0.0, 100.0],
            frames=[frame],
            sourceSegmentIds=['road_001'],
        )
        assert corridor.id == 'corridor_001'

    def test_civil_road_ir(self):
        civil = CivilRoadIR(
            corridors=[],
            junctionPatches=[],
            bridgeDecks=[],
            tunnelPolicies=[],
            earthworkCorridors=[],
        )
        assert len(civil.corridors) == 0


class TestJobState:
    def test_job_statuses(self):
        assert JobStatus.QUEUED == 'queued'
        assert JobStatus.READY == 'ready'
        assert JobStatus.FAILED == 'failed'

    def test_compute_progress(self):
        # First stage
        progress = compute_overall_progress('validating_request', 0.5)
        assert progress == 0.02 * 0.5
        
        # Last stage
        progress = compute_overall_progress('auditing_zip', 1.0)
        assert progress == 1.0

    def test_stage_weights_sum_to_one(self):
        assert abs(sum(STAGE_WEIGHTS.values()) - 1.0) < 0.001

    def test_job_event(self):
        event = JobEvent(
            jobId='job_001',
            stage='fetching_osm',
            stageProgress=0.5,
            overallProgress=0.1,
            message='Fetching OSM data',
            metrics={'waysFetched': 10},
        )
        assert event.jobId == 'job_001'
        assert event.metrics['waysFetched'] == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])