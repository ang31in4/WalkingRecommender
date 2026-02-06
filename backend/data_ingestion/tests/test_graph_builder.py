from ..graph.graph_builder import build_graph

def test_simple_way():
    ways = {
            "elements": 
            [{
                "id": 1,
                "nodes": [100, 101],
                "geometry": [
                    {"lat": 33.0, "lon": -117.0},
                    {"lat": 33.1, "lon": -117.1}
                ],
                "tags": {"highway": "footway"}
            }]
        }

    nodes, edges = build_graph(ways)

    assert len(nodes) == 2
    assert len(edges) == 1

    edge = list(edges.values())[0]
    assert edge.start_node == 100
    assert edge.end_node == 101
    assert edge.tags["highway"] == "footway"

if __name__ == "__main__":
    test_simple_way()