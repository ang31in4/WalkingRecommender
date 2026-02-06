from ..importer import DataIngestion
from ..graph.graph_builder import build_graph
from ..graph.persist_data import (make_tables, insert_nodes, insert_edges)

def main():
    ingest = DataIngestion()

    print("Get OSM data")
    raw = ingest.fetch_routes(33.6430, -117.8412, 500)
    ways = ingest.filter_for_walkability(raw)

    print("Build graph")
    nodes, edges = build_graph(ways)

    print(f"Built {len(nodes)} nodes")
    print(f"Built {len(edges)} edges")

    print("Creating database tables")
    make_tables()

    print("Populate nodes")
    insert_nodes(nodes)

    print("Populate edges")
    insert_edges(edges)

    print("Test complete")

if __name__ == "__main__":
    main()