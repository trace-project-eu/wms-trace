# import json
#
# import requests
# import json_utils
# from json_utils import parse_json_input
#
# api_key = "7bf849c2c869f9f8cbb3bc77be812fd2"
#
# # RSWT thresholds
# RSWT_MAP = {
#     "rain":   [50, 30, 15, 7, 2],    # mm/h
#     "snow":   [5, 3, 2, 1, 0],       # cm/h
#     "wind":   [80, 60, 40, 25, 10],  # km/h
#     "temp":   [(-40,60), (-20,50), (-10,40), (0,30), (5,20)]  # °C
# }
#
# # -------------------------
# # Weather fetching function
# # -------------------------
# def fetch_weather(api_key, lat, lon):
#     """Fetch weather from OpenWeatherMap (example)."""
#     url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
#     response = requests.get(url).json()
#
#     print(response)
#
#     weather = {
#         "rain": response.get("rain", {}).get("1h", 0),
#         "snow": response.get("snow", {}).get("1h", 0),
#         "wind": response.get("wind", {}).get("speed", 0),
#         "temp": response.get("main", {}).get("temp", 18)
#     }
#
#     print(f"\n  Current Weather Conditions for location ({lat:.4f}, {lon:.4f}):\n")
#     print(f"  🌧️ Rain (1h):    {weather['rain']:.1f} mm")
#     print(f"  ❄️ Snow (1h):    {weather['snow']:.1f} cm")
#     print(f"  💨 Wind Speed:   {weather['wind']:.1f} km/h")
#     print(f"  🌡️ Temperature:  {weather['temp']:.1f} °C")
#     print("-" * 45)
#
#     return weather
#
# # -------------------------
# # Vehicle filtering function
# # -------------------------
# def is_vehicle_suitable(vehicle, weather):
#     RSWT = vehicle["RSWT"]
#
#     # Rain
#     rain_limit = RSWT_MAP["rain"][int(RSWT[0])-1]
#     if weather["rain"] > rain_limit:
#         return False
#
#     # Snow
#     snow_limit = RSWT_MAP["snow"][int(RSWT[1])-1]
#     if weather["snow"] > snow_limit:
#         return False
#
#     # Wind
#     wind_limit = RSWT_MAP["wind"][int(RSWT[2])-1]
#     if weather["wind"] > wind_limit:
#         return False
#
#     # Temperature
#     temp_min, temp_max = RSWT_MAP["temp"][int(RSWT[3])-1]
#     if not (temp_min <= weather["temp"] <= temp_max):
#         return False
#
#     return True
#
# # -------------------------
# # Filter fleet
# # -------------------------
# def filter_fleet(json_input):
#     lat, lon, vehicles = parse_json_input(json_input)
#
#     # 1. Fetch current weather
#     weather = fetch_weather(api_key, lat, lon)
#
#     # 2. Filter vehicles
#     # (Assuming is_vehicle_suitable is defined as before)
#     suitable_list = [v for v in vehicles if is_vehicle_suitable(v, weather)]
#
#     # 3. Create the required JSON structure
#     result = {
#         "suitable_vehicles": [v["id"] for v in suitable_list]
#     }
#
#     # Optional: Print for debugging
#     print("Result:", json.dumps(result, indent=4))
#
#     return result
#
# # -------------------------
# # 5. Example usage
# # -------------------------
# if __name__ == "__main__":
#
#     fleet = filter_fleet("input.json")

import json
import os
import time
import math
import re
import base64
from pathlib import Path
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result

import json_utils
from json_utils import parse_json_input
from eo4eu_api_utils import Client

# -------------------------
# EO4EU Credentials & Setup
# -------------------------
EO4EU_URL = 'https://umm-api.apps.eo4eu.eu'
EO4EU_USERNAME = 'apapakot'
EO4EU_PASSWORD = 'Trace@2026'
WORKFLOW_ID = "e25c4288-f84c-4bf9-9e00-73a74510c161"

# RSWT thresholds
RSWT_MAP = {
    "rain": [50, 30, 15, 7, 2],  # mm/h
    "snow": [5, 3, 2, 1, 0],  # cm/h
    "wind": [80, 60, 40, 25, 10],  # km/h
    "temp": [(-40, 60), (-20, 50), (-10, 40), (0, 30), (5, 20)]  # °C
}


# -------------------------
# EO4EU Helper Functions
# -------------------------
def is_none(value):
    return value is None


@retry(retry=retry_if_result(is_none), wait=wait_fixed(2), stop=stop_after_attempt(10))
def get_workflow_status(client: Client, workflow_id):
    try:
        response = client.get_workflow_info(workflow_id)
        return response.get('status')
    except:
        return None


@retry(wait=wait_fixed(2), stop=stop_after_attempt(10), reraise=True)
def connect_to_client(url, username, password):
    return Client(url, username, password)


def update_script_params(script: str, lat: float, lon: float):
    """Updates the date and target points dynamically in the payload scripts."""
    # Update date to today
    script = re.sub(r'date = "\d{8}"', f'date = "{datetime.now().strftime("%Y%m%d")}"', script)
    # Update points array to the requested lat/lon
    script = re.sub(r'points\s*=\s*\[\[.*?\]\]', f'points = [[{lat}, {lon}]]', script)
    return script


# -------------------------
# Weather fetching function (EO4EU)
# -------------------------
def fetch_weather_eo4eu(lat, lon):
    """Executes EO4EU workflow, waits for completion, and parses output for the POI."""
    print(f"\n🌍 Connecting to EO4EU API for coordinates ({lat}, {lon})...")
    client = connect_to_client(EO4EU_URL, EO4EU_USERNAME, EO4EU_PASSWORD)

    # 1. Read and dynamically update the Polytope payload scripts
    pl_script = Path('pl.py').read_text(encoding='utf-8')
    sfc_script = Path('sfc.py').read_text(encoding='utf-8')

    updated_pl = update_script_params(pl_script, lat, lon)
    updated_sfc = update_script_params(sfc_script, lat, lon)

    # 2. Encode and update workflow
    encoded_scripts = [
        base64.b64encode(s.encode("ascii")).decode("ascii")
        for s in [updated_pl, updated_sfc]
    ]

    client.workflow_update(WORKFLOW_ID, {"query": encoded_scripts, "meta": " "})
    client.workflow_start(WORKFLOW_ID)
    print("⏳ Workflow updated and started. Waiting for completion...")

    # 3. Wait for completion
    while True:
        status = get_workflow_status(client, WORKFLOW_ID)
        if status == 'COMPLETED':
            print("✅ Workflow COMPLETED.")
            break
        elif status in ['FAILED', 'ERROR']:
            print(f"❌ Workflow failed with status: {status}")
            return None
        print(f"   Status: {status}. Sleeping 10s...")
        time.sleep(10)

    # 4. Fetch the results from S3
    # NOTE: You will need to replace `download_from_s3` with the actual method
    # provided by `eo4eu_api_utils.Client` to fetch files locally.
    bucket_contents = client.list_s3_bucket(WORKFLOW_ID)
    print(f"📦 S3 Contents: {bucket_contents}")

    # client.download_file_from_s3(WORKFLOW_ID, "ClimateDT_sfc_...", "local_sfc.json")
    # client.download_file_from_s3(WORKFLOW_ID, "ClimateDT_pl_...", "local_pl.json")

    # 5. Parse the Climate-DT JSON Data (MOCK EXTRACTION)
    # The extraction logic heavily depends on Polytope's JSON output structure.
    # Below maps the parameters you requested in pl.py and sfc.py:
    # Param 130: Temp (Kelvin)
    # Param 131: U wind (m/s)
    # Param 132: V wind (m/s)
    # Param 144: Snowfall (m of water eq) -> Convert to cm
    # Param 228: Total Precipitation (m) -> Convert to mm

    # with open("local_sfc.json", "r") as f: sfc_data = json.load(f)
    # with open("local_pl.json", "r") as f: pl_data = json.load(f)

    # Mocking parsed values for demonstration:
    temp_k = 291.15  # extracted from param 130
    u_wind = 5.0  # extracted from param 131
    v_wind = 2.0  # extracted from param 132
    total_precip_m = 0.01  # extracted from param 228
    snowfall_m = 0.00  # extracted from param 144

    # Unit conversions for RSWT mapping
    temp_c = temp_k - 273.15
    wind_speed_kmh = math.sqrt(u_wind ** 2 + v_wind ** 2) * 3.6
    rain_mmh = (total_precip_m - snowfall_m) * 1000  # simplified approx
    snow_cmh = snowfall_m * 100  # simplified approx

    weather = {
        "rain": rain_mmh,
        "snow": snow_cmh,
        "wind": wind_speed_kmh,
        "temp": temp_c
    }

    print(f"\n  Current Climate-DT Conditions for location ({lat:.4f}, {lon:.4f}):\n")
    print(f"  🌧️ Rain:         {weather['rain']:.1f} mm/h")
    print(f"  ❄️ Snow:         {weather['snow']:.1f} cm/h")
    print(f"  💨 Wind Speed:   {weather['wind']:.1f} km/h")
    print(f"  🌡️ Temperature:  {weather['temp']:.1f} °C")
    print("-" * 45)

    return weather


# -------------------------
# Vehicle filtering function
# -------------------------
def is_vehicle_suitable(vehicle, weather):
    RSWT = vehicle["RSWT"]

    # Rain
    rain_limit = RSWT_MAP["rain"][int(RSWT[0]) - 1]
    if weather["rain"] > rain_limit: return False

    # Snow
    snow_limit = RSWT_MAP["snow"][int(RSWT[1]) - 1]
    if weather["snow"] > snow_limit: return False

    # Wind
    wind_limit = RSWT_MAP["wind"][int(RSWT[2]) - 1]
    if weather["wind"] > wind_limit: return False

    # Temperature
    temp_min, temp_max = RSWT_MAP["temp"][int(RSWT[3]) - 1]
    if not (temp_min <= weather["temp"] <= temp_max): return False

    return True


# -------------------------
# Filter fleet
# -------------------------
def filter_fleet(json_input):
    lat, lon, vehicles = parse_json_input(json_input)
    if lat is None or lon is None:
        return {"error": "Invalid POI"}

    # 1. Fetch current weather via EO4EU Workflow
    weather = fetch_weather_eo4eu(lat, lon)
    if not weather:
        return {"error": "Failed to fetch weather from EO4EU"}

    # 2. Filter vehicles
    suitable_list = [v for v in vehicles if is_vehicle_suitable(v, weather)]

    # 3. Create the required JSON structure
    result = {"suitable_vehicles": [v["id"] for v in suitable_list]}

    print("Result:", json.dumps(result, indent=4))
    return result


if __name__ == "__main__":
    fleet = filter_fleet("input.json")