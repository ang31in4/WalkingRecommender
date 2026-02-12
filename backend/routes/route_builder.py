import json
import math
import random
import time
from pathlib import Path
import sqlite3
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from backend.data_ingestion.graph.adjacency import Adjacency
from backend.data_ingestion.graph.edge import Edge
from backend.data_ingestion.graph.node import Node
from backend.data_ingestion.graph.persist_data import load_edges, load_nodes

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
    tag: str,
    edges: Optional[Dict[int, Edge]] = None,
) -> List[Tuple[Route, float]]:
    if edges is None:
        edges = load_edges()

    matching_edge_ids = _load_tag_edge_ids(tag)
    scored_routes = [
        (route, score_route_for_tag(route, edges, matching_edge_ids)) for route in routes
    ]
    return sorted(scored_routes, key=lambda x: x[1], reverse=True)


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
) -> Optional[int]:
    viable_edges = [
        edge_id
        for edge_id in edge_ids
        if edges[edge_id].distance_m <= remaining_distance_m
    ]
    if not viable_edges:
        return None
    if (
        matching_edge_ids is None
        and remaining_target_distance_m is None
        or (tag_bias <= 0 and distance_bias <= 0)
    ):
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

        weights.append(max(weight, 0.0001))

    return random.choices(viable_edges, weights=weights, k=1)[0]


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
) -> Optional[Route]:
    node_ids = [start_node_id]
    edge_ids: List[int] = []
    distance_m = 0.0
    current_node_id = start_node_id
    target_distance_m = (min_distance_m + max_distance_m) / 2

    for _ in range(max_steps):
        next_edge_id = _select_next_edge(
            adjacency.map.get(current_node_id, []),
            edges,
            max_distance_m - distance_m,
            remaining_target_distance_m=target_distance_m - distance_m,
            matching_edge_ids=matching_edge_ids,
            tag_bias=tag_bias,
            distance_bias=distance_bias,
        )
        if next_edge_id is None:
            break
        edge = edges[next_edge_id]
        edge_ids.append(next_edge_id)
        distance_m += edge.distance_m
        current_node_id = edge.end_node
        node_ids.append(current_node_id)
        if distance_m >= min_distance_m:
            return Route(node_ids=node_ids, edge_ids=edge_ids, distance_m=distance_m)
    return None


def build_routes(
    latitude: float,
    longitude: float,
    min_distance_m: float,
    max_distance_m: float,
    max_routes: int = 100,
    max_start_distance_m: float = MILES_TO_METERS,
    max_attempts: int = 1000,
    max_steps: int = 200,
    time_budget_s: Optional[float] = None,
    score_tag: Optional[str] = None,
    tag_bias: float = 3.0,
    distance_bias: float = 1.0,
) -> List[Route]:
    """Build candidate routes.

    If ``time_budget_s`` is provided, route generation runs until the time budget
    (or ``max_attempts``) is reached. In that mode, ``max_routes`` controls only
    how many routes are returned.
    """
    if min_distance_m <= 0:
        raise ValueError("min_distance_m must be positive")
    if max_distance_m <= 0:
        raise ValueError("max_distance_m must be positive")
    if min_distance_m > max_distance_m:
        raise ValueError("min_distance_m cannot exceed max_distance_m")
    if time_budget_s is not None and time_budget_s <= 0:
        raise ValueError("time_budget_s must be positive when provided")

    nodes = load_nodes()
    edges = load_edges()
    adjacency = Adjacency(edges.values())
    start_nodes = _candidate_start_nodes(
        nodes, latitude, longitude, max_start_distance_m
    )
    if not start_nodes:
        return []

    matching_edge_ids: Optional[Set[int]] = None
    if score_tag:
        matching_edge_ids = _load_tag_edge_ids(score_tag)

    routes: List[Route] = []
    scored_routes: List[Tuple[Route, float]] = []
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
        )
        if route is not None:
            if score_tag and matching_edge_ids is not None:
                score = score_route_for_tag(route, edges, matching_edge_ids)
                scored_routes.append((route, score))
                scored_routes.sort(key=lambda x: x[1], reverse=True)
                scored_routes = scored_routes[:max_routes]
            else:
                routes.append(route)

    if score_tag and matching_edge_ids is not None:
        return [route for route, _ in scored_routes]
    if time_budget_s is not None:
        return routes[:max_routes]
    return routes


def routes_to_geojson(routes: Sequence[Route],
                      nodes: Dict[int, Node],
                      route_scores: Optional[Dict[Tuple[int, ...], float]] = None,) -> dict:
    features = []
    for route in routes:
        coordinates = [
            [nodes[node_id].lon, nodes[node_id].lat] for node_id in route.node_ids
        ]
        properties = {
            "distance_m": route.distance_m,
            "edge_ids": list(route.edge_ids),
            "node_ids": list(route.node_ids),
        }
        if route_scores is not None:
            properties["tag_score"] = route_scores.get(tuple(route.edge_ids), 0.0)

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "distance_m": route.distance_m,
                    "edge_ids": list(route.edge_ids),
                    "node_ids": list(route.node_ids),
                },
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
    # Test location is currently UCI campus (can adjust later)
    latitude=33.6430,
    longitude=-117.8412,
    min_distance_m=1000.0,
    max_distance_m=2000.0,
    max_routes=1000000,
    max_start_distance_m=MILES_TO_METERS,
    max_attempts=1000000,
    max_steps=20000,
    time_budget_s=30.0,
    score_tag="grass",
    tag_bias=3.0,
    distance_bias=1.0,
)

if __name__ == "__main__":
    routes = build_routes(**PRESET_PARAMS)
    scored_routes = score_routes_for_tag(routes, tag="grass")

    top_n = 10
    top_scored_routes = scored_routes[:top_n]
    top_routes = [route for route, _ in top_scored_routes]
    route_scores = {tuple(route.edge_ids): score for route, score in top_scored_routes}

    write_routes_geojson(top_routes, route_scores=route_scores)

    # Load nodes so we can optionally print coordinates
    nodes = load_nodes()
    print_routes(top_routes, nodes, limit=top_n)
    