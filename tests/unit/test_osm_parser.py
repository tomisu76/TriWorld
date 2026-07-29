import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from packages.compiler.osm_parser import parse_osm

def test_parse_osm():
    fixture_path = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'osm', 'test_road.osm')
    network = parse_osm(fixture_path)
    assert len(network.segments) == 1
    segment = network.segments[0]
    assert segment.id == "road_10"
    assert len(segment.centerlineLocalM) == 2
    assert segment.centerlineLocalM[0] == [0.0, 0.0]
    assert segment.centerlineLocalM[1] == [0.001, 0.0]
    assert segment.widthM.total == 7.0

if __name__ == "__main__":
    test_parse_osm()
    print("Test passed")