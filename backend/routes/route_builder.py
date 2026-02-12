import json
import math
import random
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
) -> Optional[int]:
    viable_edges = [
        edge_id
        for edge_id in edge_ids
        if edges[edge_id].distance_m <= remaining_distance_m
    ]
    if not viable_edges:
        return None
    return random.choice(viable_edges)


def _build_route_from_start(
    start_node_id: int,
    edges: Dict[int, Edge],
    adjacency: Adjacency,
    min_distance_m: float,
    max_distance_m: float,
    max_steps: int,
) -> Optional[Route]:
    node_ids = [start_node_id]
    edge_ids: List[int] = []
    distance_m = 0.0
    current_node_id = start_node_id

    for _ in range(max_steps):
        next_edge_id = _select_next_edge(
            adjacency.map.get(current_node_id, []),
            edges,
            max_distance_m - distance_m,
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
) -> List[Route]:
    if min_distance_m <= 0:
        raise ValueError("min_distance_m must be positive")
    if max_distance_m <= 0:
        raise ValueError("max_distance_m must be positive")
    if min_distance_m > max_distance_m:
        raise ValueError("min_distance_m cannot exceed max_distance_m")

    nodes = load_nodes()
    edges = load_edges()
    adjacency = Adjacency(edges.values())
    start_nodes = _candidate_start_nodes(
        nodes, latitude, longitude, max_start_distance_m
    )
    if not start_nodes:
        return []

    routes: List[Route] = []
    attempts = 0
    while attempts < max_attempts and len(routes) < max_routes:
        attempts += 1
        start_node_id = random.choice(start_nodes)
        route = _build_route_from_start(
            start_node_id,
            edges,
            adjacency,
            min_distance_m,
            max_distance_m,
            max_steps,
        )
        if route is not None:
            routes.append(route)
    return routes


def routes_to_geojson(
    routes: Sequence[Route],
    nodes: Dict[int, Node],
    route_scores: Optional[Dict[Tuple[int, ...], float]] = None,
) -> dict:
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


PRESET_PARAMS = dict(
    latitude=0.0,
    longitude=0.0,
    min_distance_m=1000.0,
    max_distance_m=2000.0,
    max_routes=100,
    max_start_distance_m=MILES_TO_METERS,
    max_attempts=1000,
    max_steps=200,
)

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
    latitude=33.6430,
    longitude=-117.8412,
    min_distance_m=1000.0,
    max_distance_m=2000.0,
    max_routes=100,
    max_start_distance_m=MILES_TO_METERS,
    max_attempts=1000,
    max_steps=200,
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