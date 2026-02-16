from .route_builder import Route
from .route_features import RouteFeatures
from ..data_ingestion.graph.edge import Edge

'''
input: Route object and dictionary of edges
output: RouteFeatures object
The function assigns a ratio for each feature of a route 
which is relative to the length of the route.
We can use these features in scoring and compare those scores with personal models.
'''
def compute_route_features(route:Route, edges:dict[int, Edge]) -> RouteFeatures:
    total = route.distance_m

    sidewalk = lit = residential = trail = paved = accessible = steps = 0.0
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
        
        if t.get("highway") in ("footway", "path"):
            trail += d
        
        if t.get("surface") in ("asphalt", "concrete", "paved"):
            paved += d
        
        if (t.get("wheelchair") == "yes" 
            or t.get("smoothness") == "good"):
            accessible += d
        
        if t.get("highway") == "steps":
            steps += d

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
        trail_ratio=trail / total,
        paved_ratio=paved / total,
        accessible_ratio=accessible / total,
        steps_ratio=steps / total,
        avg_incline=(incline_sum / incline_count) if incline_count else None,
    )