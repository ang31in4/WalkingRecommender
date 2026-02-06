from collections import defaultdict

class Adjacency:
    def __init__(self, edges):
        self.map = defaultdict(list)
        for e in edges:
            self.map[e.start_node].append(e.edge_id)