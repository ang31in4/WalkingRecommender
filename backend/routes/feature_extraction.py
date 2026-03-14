from .route_builder import Route
from .route_features import RouteFeatures
from ..data_ingestion.graph.edge import Edge

# whether a path is "dog-friendly" is more complex than simply using the "dog" tag
def edge_dog_score(edge):
    score = 0.1  # base assumption: most places are somewhat dog-walkable
    t = edge.tags

    hw = t.get("highway")

    # sidewalks or pedestrian areas
    if (t.get("sidewalk") not in ("no", None)
        or t.get("footway") == "sidewalk"
        or hw in ("footway", "pedestrian", "path")):
        score += 0.35

    # residential streets usually good for dogs
    if hw in ("residential", "living_street", "service"):
        score += 0.25

    # parks / green spaces
    if t.get("leisure") in ("park", "dog_park"):
        score += 0.35

    # trails
    if hw in ("path", "track"):
        score += 0.2

    # major roads penalty (softer)
    if hw in ("primary", "secondary", "trunk"):
        score -= 0.25

    # explicit dog restriction
    if t.get("dog") == "no":
        score -= 0.4

    return max(0.0, min(1.0, score))


'''
input: Route object and dictionary of edges
output: RouteFeatures object
The function assigns a ratio for each feature of a route 
which is relative to the length of the route.
We can use these features in scoring and compare those scores with personal models.
'''
def compute_route_features(route: Route, edges: dict[int, Edge]) -> RouteFeatures:
    total = route.distance_m

    sidewalk = lit = residential = major_road = trail = paved = rough = accessible = steps = dog = 0.0
    incline_sum = 0.0
    incline_count = 0

    for eid in route.edge_ids:
        e = edges[eid]
        d = e.distance_m
        t = e.tags

        hw = t.get("highway")
        surface = t.get("surface")

        # sidewalks
        if (
            t.get("sidewalk") not in ("no", None)
            or t.get("footway") == "sidewalk"
            or hw in ("footway", "pedestrian")
        ):
            sidewalk += d

        # lighting (assume residential areas are often lit)
        if t.get("lit") == "yes" or hw in ("residential", "living_street"):
            lit += d

        # residential environments
        if hw in ("residential", "living_street", "service"):
            residential += d

        # major roads
        if hw in ("primary", "secondary", "trunk", "tertiary"):
            major_road += d

        # trails / walking paths
        if hw in ("footway", "path", "track"):
            trail += d

        # paved surfaces
        if surface in ("asphalt", "concrete", "paved", "bricks") or hw in ("residential", "service"):
            paved += d

        # rough terrain
        if (
            surface in ("gravel", "dirt", "sand", "ground", "unpaved")
            or t.get("smoothness") in ("bad", "very_bad")
        ):
            rough += d

        # accessibility
        if (
            t.get("wheelchair") == "yes"
            or t.get("smoothness") in ("excellent", "good")
            or hw in ("footway", "pedestrian")
        ):
            accessible += d

        # steps
        if hw == "steps":
            steps += d

        # dog friendliness
        if edge_dog_score(e) >= 0.3:
            dog += d

        # incline
        if "incline" in t:
            try:
                incline_sum += float(t["incline"].strip("%")) / 100
                incline_count += 1
            except ValueError:
                pass

    return RouteFeatures(
        length_m=total,
        sidewalk_ratio=sidewalk / total,
        lit_ratio=lit / total,
        residential_ratio=residential / total,
        major_road_ratio=major_road / total,
        trail_ratio=trail / total,
        paved_ratio=paved / total,
        rough_surface_ratio=rough / total,
        accessible_ratio=accessible / total,
        steps_ratio=steps / total,
        dog_friendly_ratio=dog / total,
        avg_incline=(incline_sum / incline_count) if incline_count else None,
    )