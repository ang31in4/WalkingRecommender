import sqlite3
from pathlib import Path
from .session import SearchSession
from .search_filters import SearchFilters
from ..routes.route_features import RouteFeatures

DATA_INGESTION_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = DATA_INGESTION_DIR / "sessions"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "search_sessions.db"

def make_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def make_session_table(conn):
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS search_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );""")

def make_interaction_table(conn):
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS session_interaction (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp DATETIME,
                type TEXT,
                FOREIGN KEY (session_id) REFERENCES search_sessions(session_id)
                );""")

def make_filters_table(conn):
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS session_filters (
                interaction_id INTEGER PRIMARY KEY,
                difficulty TEXT,
                distance TEXT,
                wheelchair_access INTEGER,
                avoid_steps INTEGER,
                pet_friendly INTEGER,
                urban INTEGER,
                FOREIGN KEY (interaction_id) REFERENCES session_interaction(interaction_id)
                );""")
    # Add urban column for DBs created before this change
    try:
        cur.execute("ALTER TABLE session_filters ADD COLUMN urban INTEGER DEFAULT 0")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise

def make_route_selected_table(conn):
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS session_route_selected (
                interaction_id INTEGER PRIMARY KEY,
                accessibility_score REAL,
                urban_score REAL,
                difficulty_score REAL,
                safety_score REAL,
                FOREIGN KEY (interaction_id) REFERENCES session_interaction(interaction_id)
                );""")

# insertion functions
def insert_session(conn, session:SearchSession):
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO search_sessions (user_id, timestamp)
                VALUES (?, ?)
                """, 
                (session.user_id, session.timestamp)
                )
    
    session_id = cur.lastrowid

    return session_id    

def insert_interaction(conn, session_id, timestamp, type):
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO session_interaction (
                session_id,
                timestamp,
                type
                )
                VALUES (?, ?, ?);
                """,
                (
                    session_id,
                    timestamp,
                    type
                )
            )
    interaction_id = cur.lastrowid
    
    return interaction_id

def insert_filters(conn, interaction_id, filters:SearchFilters):
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO session_filters (
                    interaction_id,
                    difficulty,
                    distance,
                    wheelchair_access,
                    pet_friendly,
                    urban
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    interaction_id,
                    filters.difficulty,
                    filters.distance,
                    int(filters.wheelchair_access),
                    # int(filters.avoid_steps),
                    int(filters.pet_friendly),
                    int(filters.urban),
                )
            )

def insert_selected_route(conn, interaction_id: int, route: RouteFeatures | None = None) -> None:
    """Insert one row into session_route_selected. If route is None, scores are 0."""
    cur = conn.cursor()
    if route is None:
        cur.execute(
            """
            INSERT INTO session_route_selected (
                interaction_id,
                accessibility_score,
                urban_score,
                difficulty_score,
                safety_score
            )
            VALUES (?, 0, 0, 0, 0);
            """,
            (interaction_id,),
        )
    else:
        cur.execute(
            """
            INSERT INTO session_route_selected (
                interaction_id,
                accessibility_score,
                urban_score,
                difficulty_score,
                safety_score
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                interaction_id,
                route.accessibility_score,
                route.urban_score,
                route.difficulty_score,
                route.safety_score,
            ),
        )
