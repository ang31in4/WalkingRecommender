from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.users.manage_user_profiles import load_user_profile, make_connection, update_user_steps
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

    conn = session_conn()
    make_session_table(conn)

    session = SearchSession(
        session_id=None,
        user_id=user_id,
        timestamp=now,
    )

    insert_session(conn, session)
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "user_id": user.user_id,
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

    # Scores come from the client (0..1). Missing values default to 0 in DB insert.
    accessibility_score = data.get("a_score")
    urban_score = data.get("u_score")
    difficulty_score = data.get("d_score")
    safety_score = data.get("s_score")

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
    insert_selected_route(
        conn,
        interaction_id,
        user_id,
        accessibility_score=accessibility_score,
        urban_score=urban_score,
        difficulty_score=difficulty_score,
        safety_score=safety_score,
    )
    print("Inserted route selected")
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200


def get_user_step_goal(user_id: str):
    """GET /api/user/<user_id>/step_goal — returns step_goal and current_step from user db."""
    if not user_id or not user_id.strip():
        return jsonify({"success": False, "error": "user_id is required"}), 400
    user_id = user_id.strip()
    if not get_user(user_id):
        return jsonify({"success": False, "error": "User not found"}), 404
    try:
        user = load_user_profile(user_id)
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to load user profile"}), 500

    print(
        f"[StepGoal] user_id={user_id} current_steps={user.current_steps} step_goal={user.step_goal}"
    )
    return jsonify({
        "success": True,
        "user_id": user_id,
        "step_goal": user.step_goal,
        "current_step": user.current_steps,
    }), 200


def post_user_steps(user_id: str):
    """POST /api/user/<user_id>/steps — body: { \"current_steps\": int }. Updates user's current_step in db."""
    if not user_id or not user_id.strip():
        return jsonify({"success": False, "error": "user_id is required"}), 400
    user_id = user_id.strip()
    if not get_user(user_id):
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json(silent=True) or {}
    try:
        current_steps = int(data.get("current_steps", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "current_steps must be an integer"}), 400
    current_steps = max(0, current_steps)
    try:
        update_user_steps(user_id, current_steps)
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to update steps"}), 500

    print(f"[UpdateSteps] user_id={user_id} current_steps={current_steps}")
    return jsonify({"success": True, "user_id": user_id, "current_step": current_steps}), 200