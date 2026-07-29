import xml.etree.ElementTree as ET
from packages.contracts.road_ir import RoadNetworkIR, RoadSegment, SourceRef, RoadClass, LaneConfig, WidthConfig


def parse_osm(osm_path: str) -> RoadNetworkIR:
    tree = ET.parse(osm_path)
    root = tree.getroot()

    nodes = {}
    for node in root.findall('node'):
        nodes[node.get('id')] = (float(node.get('lon')), float(node.get('lat')))

    segments = []
    for way in root.findall('way'):
        way_id = way.get('id')
        coords = []
        for nd in way.findall('nd'):
            ref = nd.get('ref')
            if ref in nodes:
                coords.append(nodes[ref])

        if coords:
            # Default values - real parser would extract from tags
            segments.append(RoadSegment(
                id=f"road_{way_id}",
                source=SourceRef(wayId=int(way_id)),
                **{"class": RoadClass.RESIDENTIAL},
                direction="both",
                lanes=LaneConfig(forward=1, backward=1, source="default"),
                widthM=WidthConfig(total=7.0, source="default"),
                centerlineLocalM=[[c[0], c[1]] for c in coords],
            ))

    return RoadNetworkIR(segments=segments)