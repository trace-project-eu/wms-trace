import json
import os


def parse_json_input(filepath):
    """
    Parses the JSON file and returns the specific components needed.

    Returns:
        tuple: (lat, lon, vehicles_list) or (None, None, None) on error
    """
    if not os.path.exists(filepath):
        print(f"❌ Error: File '{filepath}' not found.")
        return None, None, None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Extract components safely
        poi = data.get("poi", {})
        lat = poi.get("lat")
        lon = poi.get("lon")
        vehicles = data.get("vehicles", [])

        if lat is None or lon is None:
            print("❌ Error: 'lat' or 'lon' missing in POI data.")
            return None, None, None

        return lat, lon, vehicles

    except json.JSONDecodeError:
        print(f"❌ Error: Failed to decode JSON from '{filepath}'.")
        return None, None, None