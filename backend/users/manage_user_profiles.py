import sqlite3
from pathlib import Path
from .user_profile import UserProfile

DATA_INGESTION_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = DATA_INGESTION_DIR / "users"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "users.db"

def make_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def make_table():
    conn = make_connection()
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,

                requires_wheelchair INTEGER,

                accessibility_weight REAL,
                urban_weight REAL,
                relaxed_weight REAL
                ); """)

    conn.commit()
    conn.close()

def insert_user_profile(user:UserProfile):
    conn = make_connection()
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO users 
                (user_id, requires_wheelchair, accessibility_weight, urban_weight, relaxed_weight)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    user.user_id,
                    user.requires_wheelchair,
                    user.accessibility_weight,
                    user.urban_weight,
                    user.relaxed_weight
                )
            )

    conn.commit()
    conn.close()

def load_user_profile(user_id: str) -> UserProfile:
    conn = make_connection()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()

    return UserProfile(
        user_id=row["user_id"],
        requires_wheelchair=bool(row["requires_wheelchair"]),
        accessibility_weight=row["accessibility_weight"],
        urban_weight=row["urban_weight"],
        relaxed_weight=row["relaxed_weight"],
    )