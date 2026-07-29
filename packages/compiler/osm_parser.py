import xml.etree.ElementTree as ET
from packages.contracts.road_ir import RoadNetworkIR, RoadSegmentIR

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
            segments.append(RoadSegmentIR(id=way_id, centerline=coords))
            
    return RoadNetworkIR(segments=segments)
