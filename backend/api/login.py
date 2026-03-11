from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.users.manage_user_profiles import load_user_profile, make_connection
from backend.sessions.session import SearchSession
from backend.sessions.session_tables import (
    make_connection as session_conn,
    make_session_table,
    make_interaction_table,
    make_filters_table,
    make_route_selected_table,
    insert_session,
    insert_interaction,
    insert_filters,
    insert_selected_route,
)
from backend.sessions.search_filters import SearchFilters
from backend.api.routes import register_routes

app = Flask(__name__)
CORS(app)
register_routes(app)

def user_exists(user_id: str) -> bool:
    """Check if a user_id exists in the database."""
    conn = make_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row is not None


@app.route("/api/login", methods=["POST"])
def post_login():
    """Verify user_id. Expects JSON body: {"user_id": "..."}. Creates a new session on success."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "").strip()

    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400

    if not user_exists(user_id):
        return jsonify({"success": False, "error": "User not found"}), 404

    user = load_user_profile(user_id)

    # Create and store a new session for this login
    now = datetime.utcnow()
    conn = session_conn()
    make_session_table(conn)

    # Try to load the last-used filters for this user; fall back to empty defaults
    current_filters = post_filters()
    selected_filters = current_filters or SearchFilters(
        difficulty=None,
        distance=None,
        wheelchair_access=False,
        avoid_steps=False,
        pet_friendly=False,
        urban=False,
    )

    session = SearchSession(
        session_id=None,
        user_id=user_id,
        timestamp=now,
        selected_filters=selected_filters,
    )
    insert_session(conn, session)
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "user_id": user.user_id,
    }), 200


@app.route("/api/filters", methods=["POST"])
def post_filters():
    """Save the user's chosen filters for this session. Expects JSON: user_id, difficulty?, distance?, wheelchair_access?, avoid_steps?, pet_friendly?, urban?."""
    data = request.get_json(silent=True) or {}
    user_id = (data.get("user_id") or "").strip()
    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400

    def parse_bool(key: str, default: bool = False) -> bool:
        v = data.get(key)
        if v is None:
            return default
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)

    filters = SearchFilters(
        difficulty=data.get("difficulty") or None,
        distance=data.get("distance") or None,
        wheelchair_access=parse_bool("wheelchair_access"),
        # avoid_steps=parse_bool("avoid_steps"),
        pet_friendly=parse_bool("pet_friendly"),
        urban=parse_bool("urban"),
    )

    conn = session_conn()
    make_session_table(conn)
    make_interaction_table(conn)
    make_filters_table(conn)

    cur = conn.cursor()
    cur.execute(
        "SELECT session_id FROM search_sessions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    if row is not None:
        session_id = row["session_id"]
    else:
        now = datetime.utcnow()
        default_filters = SearchFilters(
            difficulty=None,
            distance=None,
            wheelchair_access=False,
            # avoid_steps=False,
            pet_friendly=False,
            urban=False,
        )
        session = SearchSession(
            session_id=None,
            user_id=user_id,
            timestamp=now,
            selected_filters=default_filters,
        )
        session_id = insert_session(conn, session)

    now = datetime.utcnow()
    interaction_id = insert_interaction(conn, session_id, now, "filter")
    insert_filters(conn, interaction_id, filters)
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200


@app.route("/api/session/route_selected", methods=["POST"])
def post_route_selected():
    """Record that the user selected a route. Expects JSON: user_id."""
    data = request.get_json(silent=True) or {}
    user_id = (data.get("user_id") or "").strip()
    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400

    conn = session_conn()
    make_session_table(conn)
    make_interaction_table(conn)
    make_route_selected_table(conn)

    cur = conn.cursor()
    cur.execute(
        "SELECT session_id FROM search_sessions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    if row is not None:
        session_id = row["session_id"]
    else:
        now = datetime.utcnow()
        default_filters = SearchFilters(
            difficulty=None,
            distance=None,
            wheelchair_access=False,
            # avoid_steps=False,
            pet_friendly=False,
            urban=False,
        )
        session = SearchSession(
            session_id=None,
            user_id=user_id,
            timestamp=now,
            selected_filters=default_filters,
        )
        session_id = insert_session(conn, session)

    now = datetime.utcnow()
    interaction_id = insert_interaction(conn, session_id, now, "route_selected")
    insert_selected_route(conn, interaction_id, None)
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200