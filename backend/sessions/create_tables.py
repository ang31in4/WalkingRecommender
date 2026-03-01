from .session_tables import (make_connection, 
                            make_session_table, 
                            make_interaction_table, 
                            make_filters_table, 
                            make_route_selected_table)

def create_all_tables():
    conn = make_connection()
    
    make_session_table(conn)
    make_interaction_table(conn)
    make_filters_table(conn)
    make_route_selected_table(conn)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_all_tables()