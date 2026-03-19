from .sessions.session_tables import (make_connection, clear_search_sessions)
from .users.test_users import reset_test_users

if __name__ == "__main__":
    conn = make_connection()
    clear_search_sessions(conn)
    conn.close()
    
    reset_test_users()
