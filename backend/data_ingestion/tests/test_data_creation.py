import json
from pathlib import Path

from ..importer import DataIngestion
from ..graph.graph_builder import build_graph
from ..graph.persist_data import (make_tables, insert_nodes, insert_edges, load_edges)
from ..index.inverted_index_builder import (
    make_connection as idx_conn,
    create_edge_features_table,
    populate_edge_features,
)

def test_irvine():
    ingest = DataIngestion()

    print("Get OSM data")
    raw = ingest.fetch_irvine_walkways()
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
    
def test_basic():
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


def test_oc_county():
    """
    Fetch walkways for all of Orange County, build graph, persist to DB.
    Run: python -m backend.data_ingestion.tests.test_data_creation
    """
    ingest = DataIngestion()

    print("Fetching OSM data for Orange County (this may take several minutes)...")
    raw = ingest.fetch_oc_county_walkways()
    ways = ingest.filter_for_walkability(raw)

    n_elements = len(ways.get("elements", []))
    print(f"Filtered to {n_elements} walkable ways")

    print("Building graph...")
    nodes, edges = build_graph(ways)

    print(f"Built {len(nodes)} nodes")
    print(f"Built {len(edges)} edges")

    print("Creating database tables")
    make_tables()

    print("Populating nodes")
    insert_nodes(nodes)

    print("Populating edges")
    insert_edges(edges)

    print("Building inverted index for tag-based scoring...")
    conn = idx_conn()
    create_edge_features_table(conn)
    populate_edge_features(conn, edges)
    conn.close()

    print("Orange County graph ready. Restart the backend API to use it.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "oc":
        test_oc_county()
    else:
        test_irvine()