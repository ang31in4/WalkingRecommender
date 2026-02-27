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
                avoid_steps INTEGER,
                
                min_length_m REAL,
                max_length_m REAL,
                max_difficulty REAL,
                
                bringing_dog INTEGER,

                accessibility_weight REAL,
                urban_weight REAL,
                relaxed_weight REAL,
                difficulty_weight REAL,
                safety_weight REAL
                ); """)

    conn.commit()
    conn.close()

def insert_user_profile(user:UserProfile):
    conn = make_connection()
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO users (
                    user_id,
                    requires_wheelchair,
                    avoid_steps,
                    min_length_m,
                    max_length_m,
                    max_difficulty,
                    bringing_dog,
                    accessibility_weight,
                    urban_weight,
                    relaxed_weight,
                    difficulty_weight,
                    safety_weight
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    user.user_id,
                    int(user.requires_wheelchair),
                    int(user.avoid_steps),
                    user.min_length_m,
                    user.max_length_m,
                    user.max_difficulty,
                    int(user.bringing_dog),
                    user.accessibility_weight,
                    user.urban_weight,
                    user.relaxed_weight,
                    user.difficulty_weight,
                    user.safety_weight
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

    conn.commit()
    conn.close()

    return UserProfile(
        user_id=row["user_id"],
        requires_wheelchair=bool(row["requires_wheelchair"]),
        avoid_steps=bool(row["avoid_steps"]),
        min_length_m=row["min_length_m"],
        max_length_m=row["max_length_m"],
        max_difficulty=row["max_difficulty"],
        bringing_dog=bool(row["bringing_dog"]),
        accessibility_weight=row["accessibility_weight"],
        urban_weight=row["urban_weight"],
        relaxed_weight=row["relaxed_weight"],
        difficulty_weight=row["difficulty_weight"],
        safety_weight=row["safety_weight"]
    )

'''
Use this function to modify or create a user profile.
Takes a new or updated UserProfile as input. If the user exists, it will update the info.
If the user does not exist, it will add it to the table.
'''
def save_user_profile(user: UserProfile):
    conn = make_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (
            user_id,
            requires_wheelchair,
            avoid_steps,
            min_length_m,
            max_length_m,
            max_difficulty,
            bringing_dog,
            accessibility_weight,
            urban_weight,
            relaxed_weight,
            difficulty_weight,
            safety_weight
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            requires_wheelchair = excluded.requires_wheelchair,
            avoid_steps = excluded.avoid_steps,
            min_length_m = excluded.min_length_m,
            max_length_m = excluded.max_length_m,
            max_difficulty = excluded.max_difficulty,
            bringing_dog = excluded.bringing_dog,
            accessibility_weight = excluded.accessibility_weight,
            urban_weight = excluded.urban_weight,
            relaxed_weight = excluded.relaxed_weight,
            difficulty_weight = excluded.difficulty_weight,
            safety_weight = excluded.safety_weight;
    """,
    (
        user.user_id,
        int(user.requires_wheelchair),
        int(user.avoid_steps),
        user.min_length_m,
        user.max_length_m,
        user.max_difficulty,
        int(user.bringing_dog),
        user.accessibility_weight,
        user.urban_weight,
        user.relaxed_weight,
        user.difficulty_weight,
        user.safety_weight
    ))

    conn.commit()
    conn.close()