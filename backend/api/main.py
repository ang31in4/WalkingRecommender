from flask import jsonify, request
from flask_cors import CORS

from backend.data_ingestion.graph.persist_data import load_nodes
from backend.routes.route_builder import build_routes, PRESET_PARAMS, routes_to_geojson
from backend.api.login import app

CORS(app)


def _parse_float(value, default):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_bool(value, default):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def _get_route_params():
    """Extract build_routes params from GET query or POST JSON."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
    else:
        data = request.args

    params = dict(PRESET_PARAMS)
    params["latitude"] = _parse_float(data.get("latitude"), params["latitude"])
    params["longitude"] = _parse_float(data.get("longitude"), params["longitude"])
    user_id = data.get("user_id")
    if user_id is not None:
        cleaned_user_id = str(user_id).strip()
        params["user_id"] = cleaned_user_id or None
    min_d = data.get("min_distance_m")
    max_d = data.get("max_distance_m")
    if min_d is not None:
        params["min_distance_m"] = _parse_float(min_d, None)
    if max_d is not None:
        params["max_distance_m"] = _parse_float(max_d, None)
    params["max_routes"] = _parse_int(data.get("max_routes"), params["max_routes"])
    params["max_start_distance_m"] = _parse_float(
        data.get("max_start_distance_m"), params["max_start_distance_m"]
    )
    params["max_attempts"] = _parse_int(data.get("max_attempts"), params["max_attempts"])
    params["max_steps"] = _parse_int(data.get("max_steps"), params["max_steps"])
    params["time_budget_s"] = _parse_float(data.get("time_budget_s"), params["time_budget_s"])
    params["tag_bias"] = _parse_float(data.get("tag_bias"), params["tag_bias"])
    params["distance_bias"] = _parse_float(data.get("distance_bias"), params["distance_bias"])
    params["route_similarity_threshold"] = _parse_float(
        data.get("route_similarity_threshold"), params["route_similarity_threshold"]
    )
    params["edge_reuse_penalty"] = _parse_float(
        data.get("edge_reuse_penalty"), params["edge_reuse_penalty"]
    )
    params["allow_edge_reuse"] = _parse_bool(data.get("allow_edge_reuse"), params["allow_edge_reuse"])

    return params


@app.route("/api/routes", methods=["GET"])
def get_routes():
    try:
        params = _get_route_params()
        routes = build_routes(**params)
        geojson = routes_to_geojson(routes, load_nodes())
        return jsonify(geojson)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/routes", methods=["POST"])
def post_routes():
    try:
        params = _get_route_params()
        routes = build_routes(**params)
        geojson = routes_to_geojson(routes, load_nodes())
        return jsonify(geojson)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)