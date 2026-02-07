import math
from typing import Dict
from .node import Node
from .edge import Edge

def _haversine_distance_m(lat1, lon1, lat2, lon2):
    radius_m = 6371000
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_m * c


def build_graph(ways):
    nodes: Dict[int, Node] = {}
    edges: Dict[int, Edge] = {}
    edge_id = 1

    for way in ways["elements"]:
        node_ids = way["nodes"]
        geometry = way["geometry"]
        tags = way["tags"]
        way_id = way["id"]

        # make nodes
        for node_id, point in zip(node_ids, geometry):
            if node_id not in nodes:
                nodes[node_id] = Node(node_id=node_id, 
                                      lat=point["lat"], 
                                      lon=point["lon"])
        
        # make edges
        for i in range(len(node_ids)-1):
            start_node = node_ids[i]
            end_node = node_ids[i+1]
            start_point = geometry[i]
            end_point = geometry[i + 1]
            distance_m = _haversine_distance_m(
                start_point["lat"],
                start_point["lon"],
                end_point["lat"],
                end_point["lon"],
            )
            edges[edge_id] = Edge(edge_id=edge_id, start_node=start_node, 
                                  end_node=end_node, distance_m=distance_m, way_id=way_id, tags=tags)
            edge_id += 1
    
    return nodes, edges