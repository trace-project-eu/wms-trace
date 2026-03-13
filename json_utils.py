import json
import os

def parse_dict_input(data):
    """Parses a dictionary payload directly from the API."""
    poi = data.get("poi", {})
    lat = poi.get("lat")
    lon = poi.get("lon")
    vehicles = data.get("vehicles", [])

    if lat is None or lon is None:
        print("❌ Error: 'lat' or 'lon' missing in POI data.")
        return None, None, None

    return lat, lon, vehicles

def parse_json_input(filepath):
    """Parses a JSON file from disk (for local terminal usage)."""
    if not os.path.exists(filepath):
        print(f"❌ Error: File '{filepath}' not found.")
        return None, None, None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return parse_dict_input(data)
    except json.JSONDecodeError:
        print(f"❌ Error: Failed to decode JSON from '{filepath}'.")
        return None, None, None