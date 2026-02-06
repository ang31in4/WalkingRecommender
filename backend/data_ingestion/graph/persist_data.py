import sqlite3
import json
from pathlib import Path
from .node import Node
from .edge import Edge

DATA_INGESTION_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = DATA_INGESTION_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "walk_routes.db"

def make_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def make_tables():
    conn = make_connection()
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                node_id INTEGER PRIMARY KEY,
                lat REAL NOT NULL,
                lon REAL NOT NULL
                ); """)

    cur.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                edge_id INTEGER PRIMARY KEY,
                start_node INTEGER NOT NULL,
                end_node INTEGER NOT NULL,
                way_id INTEGER NOT NULL,
                tags TEXT NOT NULL
                ); """)

    conn.commit()
    conn.close()

# populates nodes table with nodes
def insert_nodes(nodes: dict[int, Node]):
    conn = make_connection()
    cur = conn.cursor()

    cur.executemany("""
                    INSERT OR REPLACE INTO nodes (node_id, lat, lon)
                    VALUES (?, ?, ?);
                    """,
                    [(n.node_id, n.lat, n.lon) for n in nodes.values()] )

    conn.commit()
    conn.close()

# populates edges table with edges
def insert_edges(edges: dict[int, Edge]):
    conn = make_connection()
    cur = conn.cursor()

    cur.executemany("""
                    INSERT OR REPLACE INTO edges
                    (edge_id, start_node, end_node, way_id, tags)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    [
                        (
                            e.edge_id,
                            e.start_node,
                            e.end_node,
                            e.way_id,
                            json.dumps(e.tags)
                        )
                        for e in edges.values()
                    ]
                )

    conn.commit()
    conn.close()

# use this function after query time to load node information as Node objects
def load_nodes() -> dict[int, Node]:
    conn = make_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM nodes;")
    rows = cur.fetchall()

    conn.close()

    return {
        row["node_id"]: Node(
            node_id=row["node_id"],
            lat=row["lat"],
            lon=row["lon"]
        )
        for row in rows
    }

# use this function after query time to load edge information as Edge objects
def load_edges() -> dict[int, Edge]:
    conn = make_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM edges;")
    rows = cur.fetchall()

    conn.close()

    return {
        row["edge_id"]: Edge(
            edge_id=row["edge_id"],
            start_node=row["start_node"],
            end_node=row["end_node"],
            way_id=row["way_id"],
            tags=json.loads(row["tags"])
        )
        for row in rows
    }