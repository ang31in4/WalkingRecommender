from .route_builder import Route
from .route_features import RouteFeatures
from ..data_ingestion.graph.edge import Edge

# whether a path is "dog-friendly" is more complex than simply using the "dog" tag
def edge_dog_score(edge):
    score = 0.0
    t = edge.tags

    if (t.get("sidewalk") and t["sidewalk"] != "no"
        or t.get("footway") and t["footway"] == "sidewalk"):
        score += 0.3
    
    if t.get("highway") in ("footway", "path"):
        score += 0.3

    if t.get("highway") == "residential":
        score += 0.2
    
    if t.get("highway") in ("primary", "secondary"):
        score -= 0.4
    
    if t.get("dog") != "no":
        score += 0.2

    return max(0.0, min(1.0, score))

'''
input: Route object and dictionary of edges
output: RouteFeatures object
The function assigns a ratio for each feature of a route 
which is relative to the length of the route.
We can use these features in scoring and compare those scores with personal models.
'''
def compute_route_features(route:Route, edges:dict[int, Edge]) -> RouteFeatures:
    total = route.distance_m

    sidewalk = lit = residential = major_road = trail = paved = rough = accessible = steps = dog = 0.0
    incline_sum = 0.0
    incline_count = 0

    for eid in route.edge_ids:
        e = edges[eid]
        d = e.distance_m
        t = e.tags

        if (t.get("sidewalk") and t["sidewalk"] != "no"
            or t.get("footway") and t["footway"] == "sidewalk"):
            sidewalk += d
        
        if t.get("lit") == "yes":
            lit += d
        
        if t.get("highway") == "residential":
            residential += d
            major_road += d
        
        if t.get("highway") in ("primary", "secondary"):
            major_road += d

        if t.get("highway") in ("footway", "path"):
            trail += d
        
        if t.get("surface") in ("asphalt", "concrete", "paved", "bricks"):
            paved += d

        if (t.get("surface") in ("gravel", "dirt", "sand", "unpaved")
            or t.get("smoothness") == "bad"):
            rough += d
        
        if (t.get("wheelchair") == "yes" 
            or t.get("smoothness") == "good"):
            accessible += d
        
        if t.get("highway") == "steps":
            steps += d

        dog_score = edge_dog_score(e)
        if dog_score >= 0.6:
            dog += d
        
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