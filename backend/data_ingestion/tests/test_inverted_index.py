from ..graph.persist_data import load_edges
from ..index.inverted_index_builder import (make_connection, 
                                          create_edge_features_table, populate_edge_features)

def index_for_irvine():
    edges = load_edges()
    conn = make_connection()
    create_edge_features_table(conn)
    populate_edge_features(conn, edges)

if __name__ == "__main__":
    index_for_irvine()