import uuid
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

def get_user(user_id: str) -> bool:
    conn = make_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row is not None

def post_login():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "").strip()

    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400

    if not get_user(user_id):
        return jsonify({"success": False, "error": "User not found"}), 404

    user = load_user_profile(user_id)
    if user is None:
        return jsonify({"success": False, "error": "Failed to load user profile"}), 500

    now = datetime.utcnow()
    session_token = str(uuid.uuid4())

    conn = session_conn()
    make_session_table(conn)

    session = SearchSession(
        session_id=None,
        user_id=user_id,
        timestamp=now,
        session_token = session_token,
    )

    insert_session(conn, session)
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "user_id": user.user_id,
        "session_token": session_token,
        "profile": {
            "requires_wheelchair": user.requires_wheelchair,
            "avoid_steps": user.avoid_steps,
            "min_length_m": user.min_length_m,
            "max_length_m": user.max_length_m,
            "max_difficulty": user.max_difficulty,
            "bringing_dog": user.bringing_dog,
            "accessibility_weight": user.accessibility_weight,
            "urban_weight": user.urban_weight,
            "difficulty_weight": user.difficulty_weight,
            "safety_weight": user.safety_weight
        }
    }), 200

def post_route_selected():
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
        )
        session_id = insert_session(conn, session)

    now = datetime.utcnow()
    interaction_id = insert_interaction(conn, session_id, now, "route_selected")
    insert_selected_route(conn, interaction_id, None)
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200