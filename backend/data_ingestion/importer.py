from typing import Dict
import requests
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

if __name__ == "__main__":
    ingest = DataIngestion()

    # Using 1000m radius to ensure we actually catch some data
    result = ingest.fetch_routes(33.6430, -117.8412, 1000)

    if "elements" in result:
        for element in result["elements"]:
            print(element)
