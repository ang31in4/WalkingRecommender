from typing import Dict
from pathlib import Path
import requests
import json
from config import Config

class DataIngestion:
    def __init__(self):
        self.overpass_url = Config.OVERPASS_URL

    def fetch_routes(self, latitude, longitude, radius) -> Dict:
        """
        Fetch walkways around a certain coordinate.
        """
        query = f"""
                [out:json];
                (
                    way(around:{radius},{latitude},{longitude})["highway"~"footway|path|pedestrian|steps|track|residential|sidewalk"];
                    way(around:{radius},{latitude},{longitude})["foot"~"yes|designated"];
                    way(around:{radius},{latitude},{longitude})["access"!~"no|private"];
                );
                out body geom;
                """
        try:
            response = requests.post(self.overpass_url, data = {'data':query}, timeout= 60 )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e)
            return {}
        
    def fetch_irvine_walkways(self) -> Dict:
        """
        Fetch walkways in all of Irvine
        """
        query = """
                [out:json][timeout:180];
                area["name"="Irvine"]["boundary"="administrative"]["admin_level"="8"]->.irvine;
                ( 
                way(area.irvine)["highway"~"footway|path|pedestrian|steps|track|residential|sidewalk"]; 
                way(area.irvine)["foot"~"yes|designated"]; 
                way(area.irvine)["access"!~"no|private"]; 
                ); 
                out body geom;
                """
        try:
            response = requests.post(self.overpass_url, data={"data": query}, timeout=180)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e)
            return {}
        
    def filter_for_walkability(self, routes):
        filtered = []

        walkable_highways = {
            "footway", "path", "pedestrian", "steps", "corridor",
            "residential", "living_street", "service", "unclassified",
            "tertiary", "secondary", "primary",
            "track", "cycleway",
        }

        hard_exclude = {"motorway", "motorway_link", "construction"}
        deny = {"no", "private"}

        for el in routes.get("elements", []):
            tags = el.get("tags", {})
            hwy = tags.get("highway")
            if not hwy:
                continue

            if hwy in hard_exclude:
                continue

            # Optional: trunk is often sketchy to walk; only allow if explicitly walkable
            if hwy in {"trunk", "trunk_link"} and tags.get("foot") not in {"yes", "designated"}:
                continue

            if hwy not in walkable_highways:
                continue

            if tags.get("access") in deny:
                continue
            if tags.get("foot") in deny:
                continue

            # Optional: drop “proposed”/“abandoned” style states if present
            if tags.get("highway") == "proposed":
                continue

            filtered.append(el)

        return {"elements": filtered}

def overpass_to_geojson(elements):
    features = []

    for el in elements:
        if el.get("type") != "way":
            continue

        geometry = el.get("geometry")
        if not geometry or len(geometry) < 2:
            continue

        coords = [[pt["lon"], pt["lat"]] for pt in geometry]

        features.append({
            "type": "Feature",
            "properties": el.get("tags", {}),
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

if __name__ == "__main__":
    ingest = DataIngestion()

    # Using 1000m radius to ensure we actually catch some data
    # result = ingest.fetch_routes(33.6430, -117.8412, 1000)
    # filtered_result = ingest.filter_for_walkability(result)
    result = ingest.fetch_irvine_walkways()
    filtered_result = ingest.filter_for_walkability(result)

    # Write walkways to json
    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = BASE_DIR / "backend" / "data_ingestion"
    file_path = DATA_DIR / "data" / "irvine_walkways.json"

    with open(file_path, "w") as f:
        json.dump(filtered_result, f, indent=2)


