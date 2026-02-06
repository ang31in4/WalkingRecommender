from typing import Dict
from .node import Node
from .edge import Edge


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
            edges[edge_id] = Edge(edge_id=edge_id, start_node=start_node, 
                                  end_node=end_node, way_id=way_id, tags=tags)
            edge_id += 1
    
    return nodes, edges