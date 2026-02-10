from collections import defaultdict
from ..graph.edge import Edge

def extract_features(tags):
    # starting off with a small set of features, can add more later
    features = set()
    
    # path type
    highway = tags.get("highway")
    if highway in {"footway", "path", "pedestrian"}:
        features.add("path:pedestrian")
    elif highway == "residential":
        features.add("path:residential")
    elif highway == "steps":
        features.add("path:steps")
    
    # lighting
    if tags.get("lit") == "yes":
        features.add("lit")

    # surface type
    surface = tags.get("surface")
    if surface in {"asphalt", "concrete"}:
        features.add("surface:paved")
    elif surface in {"gravel", "dirt", "ground", "sand", "grass"}:
        features.add("surface:unpaved")

    return features

def build_inverted_index(edges: dict[int, Edge]):
    index = defaultdict(set)

    for edge in edges.values():
        features = extract_features(edge.tags)
        for feat in features: 
            index[feat].add(edge.edge_id)

    return index