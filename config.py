class Config:
    def __init__(self):
        pass

    # Main Overpass API; lz4.overpass-api.de often times out on large OC queries
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    BATCH_SIZE = 1000
