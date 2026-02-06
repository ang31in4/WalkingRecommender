from .node import Node

class Edge:
    def __init__(self, edge_id, start_node, end_node, way_id, tags):
        self.edge_id = edge_id
        self.start_node: Node = start_node
        self.end_node: Node = end_node
        self.way_id = way_id
        self.tags = tags