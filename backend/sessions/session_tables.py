import sqlite3
from pathlib import Path
from .session import SearchSession
from .search_filters import SearchFilters
from typing import Optional
from ..learning.update_profile import update_user_table

DATA_INGESTION_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = DATA_INGESTION_DIR / "sessions"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "search_sessions.db"

def make_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
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

def insert_selected_route(
    conn,
    interaction_id: int,
    user_id: str,
    accessibility_score: Optional[float] = None,
    urban_score: Optional[float] = None,
    difficulty_score: Optional[float] = None,
    safety_score: Optional[float] = None,
) -> None:
    """Insert one row into session_route_selected.

    The iOS client sends precomputed scores (0..1). If any value is missing,
    it defaults to 0.0.
    """
    cur = conn.cursor()
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
            float(accessibility_score) if accessibility_score is not None else 0.0,
            float(urban_score) if urban_score is not None else 0.0,
            float(difficulty_score) if difficulty_score is not None else 0.0,
            float(safety_score) if safety_score is not None else 0.0,
        ),
    )

    # Update the user's personal weights using the route feature scores we received.
    # Note: do not use truthiness checks here; scores can legitimately be 0.0.
    if all(
        v is not None for v in (accessibility_score, urban_score, difficulty_score, safety_score)
    ):
        try:
            update_user_table(
                user_id,
                float(accessibility_score),  # type: ignore[arg-type]
                float(urban_score),  # type: ignore[arg-type]
                float(difficulty_score),  # type: ignore[arg-type]
                float(safety_score),  # type: ignore[arg-type]
            )
        except Exception as e:
            print("User update failed:", e)


def clear_search_sessions(conn):
    cur = conn.cursor()
    
    # Drop tables
    cur.execute("DROP TABLE IF EXISTS session_route_selected;")
    cur.execute("DROP TABLE IF EXISTS session_filters;")
    cur.execute("DROP TABLE IF EXISTS session_interaction;")
    cur.execute("DROP TABLE IF EXISTS search_sessions;")

    conn.commit()

    # Recreate tables
    make_session_table(conn)
    make_interaction_table(conn)
    make_filters_table(conn)
    make_route_selected_table(conn)

    conn.commit()