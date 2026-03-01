from flask import Flask, jsonify, request, abort, make_response
from flask_cors import CORS

from backend.data_ingestion.graph.persist_data import load_nodes
from backend.routes.route_builder import build_routes, PRESET_PARAMS, routes_to_geojson
from backend.routes.route_features import RouteFeatures

app = Flask(__name__)
CORS(app)

@app.route("/api/routes", methods=["GET"])
def get_routes():
    routes = routes_to_geojson(build_routes(**PRESET_PARAMS), load_nodes())
    return jsonify(routes)

@app.route("/api/routes", methods=["POST"])
def post_routes():
    route_data = request.get_json()
    return jsonify({"status":"success", "routes": route_data})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)