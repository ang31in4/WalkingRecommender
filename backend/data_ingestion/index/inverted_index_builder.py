import sqlite3
from pathlib import Path
from ..graph.edge import Edge

DATA_INGESTION_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = DATA_INGESTION_DIR / "index"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "inverted_index.db"

def extract_features(tags):
    features = set()
    
    # path type
    highway = tags.get("highway")
    if highway:
        features.add(highway)
    
    # lighting
    if tags.get("lit") == "yes":
        features.add("lit")

    # surface type
    surface = tags.get("surface")
    if surface:
        features.add(surface)

    # possible trail/hiking info
    # sac_scale: classify hiking trails with regard to the difficulties to be expected
    # note: not many of our edges have this tag
    sac_scale = tags.get("sac_scale")
    if sac_scale:
        features.add(sac_scale)

    # trail_visibility: classification scheme for hiking trails; describes attributes
    # regarding orientation skills required to follow a path
    # using this to simply show that the path is a hiking trail
    trail_visibility = tags.get("trail_visibility")
    if trail_visibility:
        features.add("trail")

    # accessibility
    if tags.get("wheelchair") == "yes":
        features.add("wheelchair")
    
    if tags.get("smoothness") == "good":
        features.add("accessible")
    
    incline = tags.get("incline")
    if incline:
        features.add("incline")

    footway = tags.get("footway")
    if footway == "sidewalk":
        features.add("sidewalk")

    sidewalk = tags.get("sidewalk")
    if sidewalk and sidewalk != "no":
        features.add("sidewalk")

    # pet-friendly
    pet_friendly = tags.get("dog")
    if pet_friendly and pet_friendly != "no":
        features.add("dog")

    return features

# create sqlite table for inverted index
def make_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_edge_features_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edge_features (
            feature TEXT NOT NULL,
            edge_id INTEGER NOT NULL,
            PRIMARY KEY (feature, edge_id),
            FOREIGN KEY (edge_id) REFERENCES edges(edge_id)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edge_features_feature
        ON edge_features(feature);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edge_features_edge
        ON edge_features(edge_id);
    """)

    conn.commit()

def populate_edge_features(conn, edges):
    cursor = conn.cursor()

    rows = []

    for edge in edges.values():
        features = extract_features(edge.tags)
        for feature in features:
            rows.append((feature, edge.edge_id))

    cursor.executemany("""
        INSERT OR IGNORE INTO edge_features (feature, edge_id)
        VALUES (?, ?);
    """, rows)

    conn.commit()