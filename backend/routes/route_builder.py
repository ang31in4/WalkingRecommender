import json
import heapq
import math
import random
import time
from pathlib import Path
import sqlite3
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from backend.data_ingestion.graph.adjacency import Adjacency
from backend.data_ingestion.graph.edge import Edge
from backend.data_ingestion.graph.node import Node
from backend.data_ingestion.graph.persist_data import load_edges, load_nodes
from backend.users.user_profile import UserProfile
from backend.users.manage_user_profiles import load_user_profile

MILES_TO_METERS = 1609.344
INVERTED_INDEX_PATH = (
    Path(__file__).resolve().parents[1]
    / "data_ingestion"
    / "index"
    / "inverted_index.db"
)

def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6371000
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_m * c

@dataclass(frozen=True)
class Route:
    node_ids: Sequence[int]
    edge_ids: Sequence[int]
    distance_m: float

def _normalize_tags(tags: Optional[Union[str, Sequence[str]]]) -> List[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]
    return [tag.strip() for tag in tags if tag and tag.strip()]

def _load_tag_edge_ids(tag: str, db_path: Path = INVERTED_INDEX_PATH) -> Set[int]:
    if not tag:
        return set()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT edge_id
            FROM edge_features
            WHERE feature = ?
            """,
            (tag,),
        )
        return {row[0] for row in cursor.fetchall()}

def _load_matching_edge_ids(
    tags: Optional[Union[str, Sequence[str]]],
    db_path: Path = INVERTED_INDEX_PATH,
) -> Set[int]:
    normalized_tags = _normalize_tags(tags)
    if not normalized_tags:
        return set()

    matching_edge_ids: Set[int] = set()
    for tag in normalized_tags:
        matching_edge_ids.update(_load_tag_edge_ids(tag, db_path=db_path))
    return matching_edge_ids

def _score_tags_for_user_profile(user_profile: UserProfile) -> List[str]:
    tags: List[str] = []

    if user_profile.requires_wheelchair or user_profile.avoid_steps:
        tags.extend(["accessible", "paved", "sidewalk"])

    if user_profile.bringing_dog:
        tags.extend(["dog_friendly", "trail", "residential"])

    if user_profile.accessibility_weight >= 0.3:
        tags.extend(["paved", "sidewalk"])

    if user_profile.urban_weight >= 0.3:
        tags.extend(["sidewalk", "residential", "lit"])

    if user_profile.safety_weight >= 0.3:
        tags.extend(["lit", "residential"])

    if user_profile.difficulty_weight >= 1.0 and user_profile.max_difficulty is None:
        tags.extend(["trail", "incline", "rough_surface"])
    elif user_profile.difficulty_weight >= 0.3:
        tags.extend(["paved", "sidewalk"])

    if not tags:
        return ["paved", "sidewalk", "residential"]

    return list(dict.fromkeys(tags))


def _score_tags_from_user_id(user_id: str) -> List[str]:
    user_profile = load_user_profile(user_id)
    return _score_tags_for_user_profile(user_profile)

def score_route_for_tag(route: Route, edges: Dict[int, Edge], matching_edge_ids: Set[int]) -> float:
    if route.distance_m <= 0:
        return 0.0

    matched_distance_m = sum(
        edges[edge_id].distance_m
        for edge_id in route.edge_ids
        if edge_id in matching_edge_ids
    )
    return matched_distance_m / route.distance_m


def score_routes_for_tag(
    routes: Sequence[Route],
    tag: Union[str, Sequence[str]],
    edges: Optional[Dict[int, Edge]] = None,
) -> List[Tuple[Route, float]]:
    if edges is None:
        edges = load_edges()

    matching_edge_ids = _load_matching_edge_ids(tag)
    scored_routes = [
        (route, score_route_for_tag(route, edges, matching_edge_ids)) for route in routes
    ]
    return sorted(scored_routes, key=lambda x: x[1], reverse=True)

def score_routes_for_user_profile(
    routes: Sequence[Route],
    user_profile: UserProfile,
    edges: Optional[Dict[int, Edge]] = None,
) -> List[Tuple[Route, float]]:
    from backend.routes.feature_extraction import compute_route_features

    if edges is None:
        edges = load_edges()

    allowed_scored_routes: List[Tuple[Route, float]] = []
    disallowed_scored_routes: List[Tuple[Route, float]] = []
    for route in routes:
        features = compute_route_features(route, edges)
        score = user_profile.score(features)
        if user_profile.allowed(features):
            allowed_scored_routes.append((route, score))
        else:
            disallowed_scored_routes.append((route, score))

    allowed_scored_routes = sorted(allowed_scored_routes, key=lambda x: x[1], reverse=True)

    disallowed_scored_routes = sorted(disallowed_scored_routes, key=lambda x: x[1], reverse=True)
    selected_route_keys = {
        (tuple(route.node_ids), tuple(route.edge_ids), route.distance_m)
        for route, _ in allowed_scored_routes
    }
    combined_scored_routes = allowed_scored_routes[:]

    for route, score in disallowed_scored_routes:
        route_key = (tuple(route.node_ids), tuple(route.edge_ids), route.distance_m)
        if route_key in selected_route_keys:
            continue
        combined_scored_routes.append((route, score))
        selected_route_keys.add(route_key)

    return combined_scored_routes

def _candidate_start_nodes(
    nodes: Dict[int, Node],
    latitude: float,
    longitude: float,
    max_start_distance_m: float,
) -> List[int]:
    return [
        node_id
        for node_id, node in nodes.items()
        if _haversine_distance_m(latitude, longitude, node.lat, node.lon)
        <= max_start_distance_m
    ]


def _select_next_edge(
    edge_ids: Iterable[int],
    edges: Dict[int, Edge],
    remaining_distance_m: float,
    remaining_target_distance_m: Optional[float] = None,
    matching_edge_ids: Optional[Set[int]] = None,
    tag_bias: float = 0.0,
    distance_bias: float = 0.0,
    edge_visit_counts: Optional[Dict[int, int]] = None,
    edge_reuse_penalty: float = 0.0,
    allow_edge_reuse: bool = False,
) -> Optional[int]:
    viable_edges = [
        edge_id
        for edge_id in edge_ids
        if edges[edge_id].distance_m <= remaining_distance_m
    ]
    if not allow_edge_reuse and edge_visit_counts is not None:
        viable_edges = [
            edge_id for edge_id in viable_edges if edge_visit_counts.get(edge_id, 0) == 0
        ]
    if not viable_edges:
        return None
    has_weighted_signals = (
        matching_edge_ids is not None
        or remaining_target_distance_m is not None
        or (edge_visit_counts is not None and edge_reuse_penalty > 0)
        or tag_bias > 0
        or distance_bias > 0
    )
    if not has_weighted_signals:
        return random.choice(viable_edges)

    max_viable_edge_distance = max(edges[edge_id].distance_m for edge_id in viable_edges)
    distance_scale_m = max(max_viable_edge_distance, 1.0)
    weights = []
    for edge_id in viable_edges:
        edge = edges[edge_id]
        weight = 1.0

        if matching_edge_ids is not None and edge_id in matching_edge_ids and tag_bias > 0:
            weight += tag_bias

        if remaining_target_distance_m is not None and distance_bias > 0:
            distance_delta = abs(edge.distance_m - max(remaining_target_distance_m, 0.0))
            closeness = 1.0 - min(distance_delta / distance_scale_m, 1.0)
            weight += distance_bias * closeness

        if edge_visit_counts is not None and edge_reuse_penalty > 0:
            prior_visits = edge_visit_counts.get(edge_id, 0)
            weight /= 1.0 + (edge_reuse_penalty * prior_visits)

        weights.append(max(weight, 0.0001))

    return random.choices(viable_edges, weights=weights, k=1)[0]

def _route_edge_overlap_ratio(candidate_edge_ids: Sequence[int], existing_edge_set: Set[int]) -> float:
    if not candidate_edge_ids:
        return 0.0

    overlap_count = sum(1 for edge_id in candidate_edge_ids if edge_id in existing_edge_set)
    return overlap_count / len(candidate_edge_ids)

def _build_route_from_start(
    start_node_id: int,
    edges: Dict[int, Edge],
    adjacency: Adjacency,
    min_distance_m: float,
    max_distance_m: float,
    max_steps: int,
    matching_edge_ids: Optional[Set[int]] = None,
    tag_bias: float = 0.0,
    distance_bias: float = 0.0,
    edge_reuse_penalty: float = 0.0,
    allow_edge_reuse: bool = False,
) -> Optional[Route]:
    node_ids = [start_node_id]
    edge_ids: List[int] = []
    distance_m = 0.0
    current_node_id = start_node_id
    target_distance_m = (min_distance_m + max_distance_m) / 2
    edge_visit_counts: Dict[int, int] = {}

    target_distance_m = random.uniform(min_distance_m, max_distance_m)

    for _ in range(max_steps):
        next_edge_id = _select_next_edge(
            adjacency.map.get(current_node_id, []),
            edges,
            max_distance_m - distance_m,
            remaining_target_distance_m=target_distance_m - distance_m,
            matching_edge_ids=matching_edge_ids,
            tag_bias=tag_bias,
            distance_bias=distance_bias,
            edge_visit_counts=edge_visit_counts,
            edge_reuse_penalty=edge_reuse_penalty,
            allow_edge_reuse=allow_edge_reuse,
        )
        if next_edge_id is None:
            break
        edge = edges[next_edge_id]
        edge_ids.append(next_edge_id)
        edge_visit_counts[next_edge_id] = edge_visit_counts.get(next_edge_id, 0) + 1
        distance_m += edge.distance_m
        current_node_id = edge.end_node
        node_ids.append(current_node_id)
        if distance_m >= target_distance_m:
            return Route(node_ids=node_ids, edge_ids=edge_ids, distance_m=distance_m)
    return None


def build_routes(
    latitude: float,
    longitude: float,
    min_distance_m: Optional[float] = None,
    max_distance_m: Optional[float] = None,
    max_routes: int = 100,
    max_start_distance_m: float = MILES_TO_METERS,
    max_attempts: int = 1000,
    max_steps: int = 200,
    time_budget_s: Optional[float] = None,
    user_id: Optional[str] = None,
    score_tag: Optional[Union[str, Sequence[str]]] = None,
    tag_bias: float = 3.0,
    distance_bias: float = 1.0,
    route_similarity_threshold: float = 1.0,
    edge_reuse_penalty: float = 2.0,
    allow_edge_reuse: bool = False,
    return_scores: bool = False,
) -> Union[List[Route], List[Tuple[Route, float]]]:
    """Build candidate routes.

    If ``time_budget_s`` is provided, route generation runs until the time budget
    (or ``max_attempts``) is reached. In that mode, ``max_routes`` controls only
    how many routes are returned.
    """
    user_profile: Optional[UserProfile] = None
    if user_id:
        user_profile = load_user_profile(user_id)
        min_distance_m = user_profile.min_length_m
        max_distance_m = user_profile.max_length_m
    if min_distance_m is None:
        min_distance_m = 500.0
    if max_distance_m is None:
        max_distance_m = 3000.0
    if min_distance_m <= 0:
        raise ValueError("min_distance_m must be positive")
    if max_distance_m <= 0:
        raise ValueError("max_distance_m must be positive")
    if min_distance_m > max_distance_m:
        raise ValueError("min_distance_m cannot exceed max_distance_m")
    if time_budget_s is not None and time_budget_s <= 0:
        raise ValueError("time_budget_s must be positive when provided")
    if not 0 < route_similarity_threshold <= 1:
        raise ValueError("route_similarity_threshold must be in the range (0, 1]")
    if edge_reuse_penalty < 0:
        raise ValueError("edge_reuse_penalty must be non-negative")

    nodes = load_nodes()
    edges = load_edges()
    adjacency = Adjacency(edges.values())
    start_nodes = _candidate_start_nodes(
        nodes, latitude, longitude, max_start_distance_m
    )
    if not start_nodes:
        return []

    matching_edge_ids: Optional[Set[int]] = None
    if user_id:
        normalized_score_tags = _score_tags_from_user_id(user_id)
    else:
        normalized_score_tags = _normalize_tags(score_tag)
    if normalized_score_tags:
        matching_edge_ids = _load_matching_edge_ids(normalized_score_tags)

    routes: List[Route] = []
    scored_routes_heap: List[Tuple[float, int, Tuple[int, ...], Route]] = []
    scored_route_keys: Set[Tuple[int, ...]] = set()
    scored_route_edge_sets: Dict[Tuple[int, ...], Set[int]] = {}
    heap_counter = 0
    candidate_route_limit = max_routes
    if user_profile is not None and max_routes > 0:
        candidate_route_limit = min(max(max_routes * 10, 100), 5000)
    attempts = 0
    start_time = time.monotonic()
    while attempts < max_attempts:
        if time_budget_s is not None and (time.monotonic() - start_time) >= time_budget_s:
            break
        if time_budget_s is None and len(routes) >= max_routes:
            break

        attempts += 1
        start_node_id = random.choice(start_nodes)
        route = _build_route_from_start(
            start_node_id,
            edges,
            adjacency,
            min_distance_m,
            max_distance_m,
            max_steps,
            matching_edge_ids=matching_edge_ids,
            tag_bias=tag_bias,
            distance_bias=distance_bias,
            edge_reuse_penalty=edge_reuse_penalty,
            allow_edge_reuse=allow_edge_reuse,
        )
        if route is not None:
            if user_profile is not None:
                routes.append(route)
            elif normalized_score_tags and matching_edge_ids is not None:
                route_key = tuple(route.edge_ids)
                if route_key in scored_route_keys:
                    continue

                route_edge_set = set(route.edge_ids)
                if route_similarity_threshold < 1.0 and any(
                    _route_edge_overlap_ratio(route.edge_ids, existing_edge_set)
                    >= route_similarity_threshold
                    for existing_edge_set in scored_route_edge_sets.values()
                ):
                    continue

                score = score_route_for_tag(route, edges, matching_edge_ids)
                if candidate_route_limit > 0:
                    if len(scored_routes_heap) < candidate_route_limit:
                        heapq.heappush(scored_routes_heap, (score, heap_counter, route_key, route))
                        scored_route_keys.add(route_key)
                        scored_route_edge_sets[route_key] = route_edge_set
                        heap_counter += 1
                    elif score > scored_routes_heap[0][0]:
                        _, _, evicted_key, _ = heapq.heapreplace(
                            scored_routes_heap, (score, heap_counter, route_key, route)
                        )
                        scored_route_keys.remove(evicted_key)
                        scored_route_edge_sets.pop(evicted_key, None)
                        scored_route_keys.add(route_key)
                        scored_route_edge_sets[route_key] = route_edge_set
                        heap_counter += 1
            else:
                routes.append(route)

    if user_profile is not None:
        candidate_routes = routes
    elif normalized_score_tags and matching_edge_ids is not None:
        candidate_routes = [
            route
            for _, _, _, route in sorted(
                scored_routes_heap,
                key=lambda x: x[0],
                reverse=True,
            )
        ]
    elif time_budget_s is not None:
        candidate_routes = routes[:max_routes]
    else:
        candidate_routes = routes

    if user_profile is not None:
        profile_scored_routes = score_routes_for_user_profile(
            candidate_routes,
            user_profile=user_profile,
            edges=edges,
        )
        final_routes = [route for route, _ in profile_scored_routes[:max_routes]]
    else:
        final_routes = candidate_routes[:max_routes]

    scored_routes = (
        score_routes_for_tag(final_routes, tag=normalized_score_tags, edges=edges)
        if normalized_score_tags
        else [(route, 0.0) for route in final_routes]
    )

    if return_scores:
        return scored_routes

    if normalized_score_tags:
        return [route for route, _ in scored_routes]
    return final_routes


def _preferred_street_name(edge_ids: Sequence[int], edges: Dict[int, Edge], reverse: bool = False) -> Optional[str]:
    ordered_edge_ids = reversed(edge_ids) if reverse else edge_ids
    for edge_id in ordered_edge_ids:
        edge = edges.get(edge_id)
        if edge is None:
            continue
        street_name = edge.tags.get("name") if isinstance(edge.tags, dict) else None
        if street_name:
            return street_name
    return None


def _route_name(
    route: Route,
    index: int,
    edges: Dict[int, Edge],
) -> str:
    distance_miles = route.distance_m / MILES_TO_METERS
    start_street = _preferred_street_name(route.edge_ids, edges)
    end_street = _preferred_street_name(route.edge_ids, edges, reverse=True)

    if start_street and end_street:
        if start_street == end_street:
            return f"{start_street} Loop ({distance_miles:.2f} mi)"
        return f"{start_street} to {end_street} ({distance_miles:.2f} mi)"

    if start_street:
        return f"{start_street} Route ({distance_miles:.2f} mi)"

    return f"Route {index} ({distance_miles:.2f} mi)"

def routes_to_geojson(
    routes: Sequence[Route],
    nodes: Dict[int, Node],
    route_scores: Optional[Dict[Tuple[int, ...], float]] = None,
    slim: bool = False,
    coord_stride: int = 1,
) -> dict:
    from .feature_extraction import compute_route_features
    
    features = []
    edges = load_edges()
    coord_stride = max(1, int(coord_stride))

    for index, route in enumerate(routes, start=1):
        # extract feature information
        route_features = compute_route_features(route, edges)
        
        difficulty = None
        if route_features.difficulty_score <= 0.3:
            difficulty = "easy"
        elif route_features.difficulty_score <= 0.5:
            difficulty = "moderate"
        else:
            difficulty = "hard"

        pet_friendly = (route_features.dog_friendly_ratio >= 0.6)
        accessible = (route_features.accessibility_score >= 0.5)
        urban = (route_features.urban_score >= 0.5)

        node_ids = list(route.node_ids)
        if coord_stride > 1 and len(node_ids) > 2:
            sampled = node_ids[::coord_stride]
            if len(sampled) >= 2:
                node_ids = sampled

        coordinates = [[nodes[node_id].lon, nodes[node_id].lat] for node_id in node_ids]

        # Payload minimization: the iOS client only needs geometry + a few properties.
        # Large arrays like `edge_ids`/`node_ids` and per-route score fields can easily
        # blow up the JSON response size.
        properties = {
            "name": _route_name(route, index, edges),
            "length_mi": route.distance_m / MILES_TO_METERS,
            "difficulty": difficulty,
            "pet_friendly": pet_friendly,
            "wheelchair_accessible": accessible,
            "urban": urban,
        }

        if not slim:
            properties.update(
                {
                    "distance_m": route.distance_m,
                    "edge_ids": list(route.edge_ids),
                    "node_ids": list(route.node_ids),
                    "u_score": route_features.urban_score,
                    "a_score": route_features.accessibility_score,
                    "d_score": route_features.difficulty_score,
                    "s_score": route_features.safety_score,
                }
            )
            if route_scores is not None:
                properties["tag_score"] = route_scores.get(tuple(route.edge_ids), 0.0)

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": properties,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def write_routes_geojson(
    routes: Sequence[Route],
    path: Optional[Path] = None,
    route_scores: Optional[Dict[Tuple[int, ...], float]] = None,
) -> Path:
    nodes = load_nodes()
    geojson = routes_to_geojson(routes, nodes, route_scores=route_scores)
    if path is None:
        path = Path(__file__).resolve().parent / "routes.geojson"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(geojson, handle, indent=2)
    return path

def write_scored_routes(
    scored_routes: List[Tuple[Route, float]],
    path: Optional[Path] = None,
) -> Path:
    """Write a list of (route, score) to a GeoJSON file with scores in properties."""
    if not scored_routes:
        raise ValueError("scored_routes must not be empty")
    routes = [route for route, _ in scored_routes]
    route_scores = {tuple(route.edge_ids): score for route, score in scored_routes}
    if path is None:
        path = Path(__file__).resolve().parent / "scored_routes.geojson"
    return write_routes_geojson(routes, path=path, route_scores=route_scores)


def print_routes(routes: List[Route], nodes: Dict[int, Node], limit: int = 10) -> None:
    if not routes:
        print("No routes found.")
        return

    for i, r in enumerate(routes[:limit]):
        miles = r.distance_m / MILES_TO_METERS
        print(f"Route {i}: {r.distance_m:.1f} m ({miles:.3f} miles)")
        print(f"  nodes={len(r.node_ids)} edges={len(r.edge_ids)}")
        print(f"  node_ids: {r.node_ids[:20]}{' ...' if len(r.node_ids) > 20 else ''}")
        print(f"  edge_ids: {r.edge_ids[:20]}{' ...' if len(r.edge_ids) > 20 else ''}")
        print()

PRESET_PARAMS = dict(
    # USER INFO
    user_id="Ada_Lovelace", # Get tags and distance restrictions from user_id

    # USER LOCATION (currently UCI campus)
    latitude=33.646117,
    longitude=-117.843058,

    # Route generation parameters
    max_start_distance_m=250.0, # How far starting point can be from user location
    max_routes=1000000, # Number of routes to return (after scoring and/or time budget)
    max_attempts=1000000, # Upper bound on generation attempts (loop iterations trying random starts/routes)
    max_steps=2000000, # Max edges/hops per single route construction attempt before giving up.
    time_budget_s=None,  # no time limit; generate until max_routes or max_attempts

    # Tag-based scoring parameters
    tag_bias=1.0, # Weight bonus when selecting candidate edges that match score_tag.
    distance_bias=1.0, # Weight bonus for edges whose length is closer to the remaining target distance.
    route_similarity_threshold=0.5, # How similar routes can be before being considered a duplicate (0.0 = no similarity allowed, 1.0 = identical routes only
    edge_reuse_penalty=2.0, # Used only when allow_edge_reuse=True; higher values make repeated edges less likely.
    allow_edge_reuse=False, # Prevents using the same edge twice within a single generated route.
)

if __name__ == "__main__":
    print("Generating routes...")
    scored_routes = build_routes(**PRESET_PARAMS, return_scores=True)
    print("Done scoring routes...")

    # Write all scored routes to file (default: scored_routes.geojson in route_builder directory)
    if scored_routes:
        out_path = write_scored_routes(scored_routes)
        print(f"Wrote {len(scored_routes)} scored routes to {out_path}")

    # Top-n for preview / print
    top_n = 200  # !! test actual look of a route
    top_scored_routes = scored_routes[:top_n]
    top_routes = [route for route, _ in top_scored_routes]
    route_scores = {tuple(route.edge_ids): score for route, score in top_scored_routes}
    write_routes_geojson(top_routes, route_scores=route_scores)

    #nodes = load_nodes()
    #print_routes(top_routes, nodes, limit=top_n)