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
                interaction_id INTEGER PRIMARY KEY,
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
                FOREIGN KEY (interaction_id) REFERENCES session_interaction(interaction_id)
                );""")

def make_route_selected_table(conn):
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE session_route_selected (
                interaction_id INTEGER PRIMARY KEY,
                accessibility_score REAL,
                urban_score REAL,
                relaxed_score REAL,
                difficulty_score REAL,
                safety_score REAL,
                FOREIGN KEY (interaction_id) REFERENCES session_interaction(interaction_id)
                );""")

# insertion functions
def insert_session(conn, session:SearchSession):
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO sessions (user_id, timestamp)
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

def insert_filters(conn, interaction_id, filters:SearchFilters):
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO session_filters (
                    interaction_id,
                    difficulty,
                    distance,
                    wheelchair_access,
                    avoid_steps,
                    pet_friendly
                )
                VALUES (?, ?, ? ,? , ?, ?);
                """, 
                (
                    interaction_id,
                    filters.difficulty,
                    filters.distance,
                    int(filters.wheelchair_access),
                    int(filters.avoid_steps),
                    int(filters.pet_friendly)
                )
            )

def insert_selected_route(conn, interaction_id, route:RouteFeatures):
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO session_route_selected (
                    interaction_id,
                    accessibility_score,
                    urban_score,
                    relaxed_score,
                    difficulty_score,
                    safety_score
                )
                VALUES (?, ?, ? ,? , ?, ?);
                """, 
                (
                    interaction_id,
                    route.accessibility_score,
                    route.urban_score,
                    route.relaxed_walk_score,
                    route.difficulty_score,
                    route.safety_score
                )
            )