from typing import Dict
from pathlib import Path
import requests
import pandas as pd
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
    
    # reformatting results into a dataframe to make it easy to 
    # add fields later and create the logical view
    def make_dataframe(self, routes):
        ways = []

        # not keeping 'type' because they're all ways
        for element in routes.get("elements", []):
            row = {
                "id": element.get("id"),
                "bounds": element.get("bounds"),
                "geometry": element.get("geometry"),
                "tags": element.get("tags")
            }
            ways.append(row)
        
        return pd.DataFrame(ways)

if __name__ == "__main__":
    ingest = DataIngestion()

    # Using 1000m radius to ensure we actually catch some data
    result = ingest.fetch_routes(33.6430, -117.8412, 1000)
    filtered_result = ingest.filter_for_walkability(result)
    df = ingest.make_dataframe(filtered_result)

    # Write walkways to json
    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = BASE_DIR / "backend" / "data"
    file_path = DATA_DIR / "walkways.json"

    records = df.to_dict(orient="records")

    with open(file_path, "w") as f:
        json.dump(records, f, indent=2)
