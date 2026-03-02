from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.users.manage_user_profiles import load_user_profile, make_connection

app = Flask(__name__)
CORS(app)

def user_exists(user_id: str) -> bool:
    """Check if a user_id exists in the database."""
    conn = make_connection()
    cur = conn.cursor()
    row = cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row is not None


@app.route("/api/login", methods=["POST"])
def post_login():
    """Verify user_id. Expects JSON body: {"user_id": "..."}"""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "").strip()

    if not user_id:
        return jsonify({"success": False, "error": "user_id is required"}), 400

    if not user_exists(user_id):
        return jsonify({"success": False, "error": "User not found"}), 404

    user = load_user_profile(user_id)
    return jsonify({
        "success": True,
        "user_id": user.user_id,
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)