
from flask import jsonify, request, g, json

from backend.api.login import post_login
from backend.data_ingestion.graph.persist_data import load_nodes
from backend.routes.route_builder import build_routes, routes_to_geojson, MILES_TO_METERS
from backend.users.manage_user_profiles import load_user_profile


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


# def _get_route_params():
#     if request.method == "POST":
#         data = request.get_json(silent=True) or {}
#     else:
#         data = request.args
#
#     params = dict(PRESET_PARAMS)
#     params["latitude"] = _parse_float(data.get("latitude"), params["latitude"])
#     params["longitude"] = _parse_float(data.get("longitude"), params["longitude"])
#     user_id = data.get("user_id")
#     if user_id is not None:
#         cleaned_user_id = str(user_id).strip()
#         params["user_id"] = cleaned_user_id or None
#     min_d = data.get("min_distance_m")
#     max_d = data.get("max_distance_m")
#     if min_d is not None:
#         params["min_distance_m"] = _parse_float(min_d, None)
#     if max_d is not None:
#         params["max_distance_m"] = _parse_float(max_d, None)
#     params["max_routes"] = _parse_int(data.get("max_routes"), params["max_routes"])
#     params["max_start_distance_m"] = _parse_float(
#         data.get("max_start_distance_m"), params["max_start_distance_m"]
#     )
#     params["max_attempts"] = _parse_int(data.get("max_attempts"), params["max_attempts"])
#     params["max_steps"] = _parse_int(data.get("max_steps"), params["max_steps"])
#     params["time_budget_s"] = _parse_float(data.get("time_budget_s"), params["time_budget_s"])
#     params["tag_bias"] = _parse_float(data.get("tag_bias"), params["tag_bias"])
#     params["distance_bias"] = _parse_float(data.get("distance_bias"), params["distance_bias"])
#     params["route_similarity_threshold"] = _parse_float(
#         data.get("route_similarity_threshold"), params["route_similarity_threshold"]
#     )
#     params["edge_reuse_penalty"] = _parse_float(
#         data.get("edge_reuse_penalty"), params["edge_reuse_penalty"]
#     )
#     params["allow_edge_reuse"] = _parse_bool(data.get("allow_edge_reuse"), params["allow_edge_reuse"])
#
#     return params

# get the long and lat to generate routes
def get_routes():
    data = request.get_json(silent=True) or {}
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    user_id = (data.get("user_id") or "").strip() or None

    if not latitude or not longitude:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    try:
        max_routes = _parse_int(data.get("max_routes"), 60)
        params = {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "user_id": user_id,
            "max_routes": max_routes,
        }

        scored_routes = build_routes(**params, return_scores=True)
        routes = [route for route, _ in scored_routes]
        route_scores = {tuple(route.edge_ids): score for route, score in scored_routes}

        # iOS client has a small max response size; keep the GeoJSON lightweight.
        geojson = routes_to_geojson(
            routes,
            load_nodes(),
            route_scores=route_scores,
            slim=True,
            coord_stride=2,
        )

        return jsonify(geojson), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


# # call when saving a custom routes to database
# def post_routes():
#     try:
#
#         data = request.get_json(silent=True) or {}
#         latitude = data.get("latitude")
#         longitude = data.get("longitude")
#
#         if latitude is None or longitude is None:
#             return jsonify({"error": "latitude and longitude are required"}), 400
#
#         user_id = g.user.user_id if g.user else None
#
#         params = {
#             "latitude": float(latitude),
#             "longitude": float(longitude),
#             "user_id": user_id,
#
#             "max_routes": data.get("max_routes", 100),
#             "max_start_distance_m": data.get("max_start_distance_m", MILES_TO_METERS),
#             "max_attempts": data.get("max_attempts", 1000),
#             "max_steps": data.get("max_steps", 200),
#             "time_budget_s": data.get("time_budget_s"),
#             "score_tag": data.get("score_tag"),
#             "tag_bias": data.get("tag_bias", 3.0),
#             "distance_bias": data.get("distance_bias", 1.0),
#             "route_similarity_threshold": data.get("route_similarity_threshold", 1.0),
#             "edge_reuse_penalty": data.get("edge_reuse_penalty", 2.0),
#             "allow_edge_reuse": data.get("allow_edge_reuse", False),
#         }
#
#         scored_routes = build_routes(**params, return_scores=True) # built routes -> filter by user -> show routes
#         routes = [route for route, _ in scored_routes]
#         route_scores = {tuple(route.edge_ids): score for route, score in scored_routes}
#         geojson = routes_to_geojson(routes, load_nodes(), route_scores=route_scores)
#
#         with open("routes_output.geojson", "w") as f:
#             json.dump(geojson, f, indent=2)
#         print("GeoJSON saved to routes_output.geojson")
#         return jsonify(geojson)
#     except ValueError as e:
#         return jsonify({"error": str(e)}), 400
#
#
