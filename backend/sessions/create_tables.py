import sys
from pathlib import Path

# When run as script (e.g. python create_tables.py), project root may not be on path
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from backend.sessions.session_tables import (
    make_connection,
    make_session_table,
    make_interaction_table,
    make_filters_table,
    make_route_selected_table,
    DB_PATH,
)


def create_all_tables():
    conn = make_connection()
    make_session_table(conn)
    make_interaction_table(conn)
    make_filters_table(conn)
    make_route_selected_table(conn)
    conn.commit()

    # Verify: list all tables in this database
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()

    print("Database path:", DB_PATH)
    print("Tables in database:", tables)
    if not tables:
        print("Warning: no tables found. Check that you are opening this file in your DB browser:")
        print(" ", DB_PATH)


if __name__ == "__main__":
    create_all_tables()