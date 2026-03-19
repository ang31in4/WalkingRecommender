from flask import Flask
from flask_cors import CORS

from backend.api.login import post_login, post_route_selected, get_user, get_user_step_goal, post_user_steps
from backend.api.routes import get_routes

app = Flask(__name__)
CORS(app)

def map_api(app):
    app.add_url_rule("/api/login", view_func=post_login, methods=["POST"])
    app.add_url_rule("/api/login", view_func=get_user, methods=["GET"])
    app.add_url_rule("/api/routes", view_func=get_routes, methods=["GET", "POST"])
    app.add_url_rule("/api/session/route_selected", view_func=post_route_selected, methods=["POST"])
    app.add_url_rule("/api/user/<user_id>/step_goal", view_func=get_user_step_goal, methods=["GET"])
    app.add_url_rule("/api/user/<user_id>/steps", view_func=post_user_steps, methods=["POST"])


map_api(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)