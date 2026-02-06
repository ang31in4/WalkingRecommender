from typing import Dict
from pathlib import Path
import requests
import json
from config import Config

class DataIngestion:
    def __init__(self):
        self.overpass_url = Config.OVERPASS_URL

    def fetch_routes(self, latitude, longitude, radius) -> Dict:
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
        
    def filter_for_walkability(self, routes):
        filtered_routes = []
        walkable_highways = {"footway", "path", "pedestrian",
                             "steps", "residential", "track"}
        
        for element in routes.get("elements", []):
            tags = element.get("tags", {})

            if "highway" not in tags:
                continue
            
            if tags.get("highway") not in walkable_highways:
                continue
            
            if tags.get("access") in ("no", "private"):
                continue
            
            if tags.get("foot") in ("no", "private"):
                continue
            
            if "barrier" in tags:
                continue

            filtered_routes.append(element)

        return {"elements": filtered_routes}

if __name__ == "__main__":
    ingest = DataIngestion()

    # Using 1000m radius to ensure we actually catch some data
    result = ingest.fetch_routes(33.6430, -117.8412, 1000)
    filtered_result = ingest.filter_for_walkability(result)

    # Write walkways to json
    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = BASE_DIR / "backend" / "data_ingestion"
    file_path = DATA_DIR / "walkways.json"

    with open(file_path, "w") as f:
        json.dump(filtered_result, f, indent=2)
