import base64
import time
import math
import json
import os
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result
from eo4eu_api_utils import Client

# -------------------------
# Configuration
# -------------------------
EO4EU_URL = 'https://umm-api.apps.eo4eu.eu'
EO4EU_USERNAME = 'apapakot'
EO4EU_PASSWORD = 'Trace@2026'
WORKFLOW_ID = "f61488fb-9d1a-4bad-ad5b-dd2b1b95db88"


# -------------------------
# Helpers
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


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# -------------------------
# Dynamic Script Generators
# -------------------------
def generate_polytope_script(levtype, param, points, levelist=None):
    current_date = datetime.now().strftime("%Y%m%d")

    script = f"""from polytope.api import Client
import os

client = Client(address='polytope.lumi.apps.dte.destination-earth.eu', 
                user_email=os.environ.get('DESTINY_USER_EMAIL'), 
                user_key=os.environ.get('DESTINY_API_KEY'))

client.revoke('all')

request = {{
    "activity": "ScenarioMIP",
    "experiment": "SSP3-7.0",
    "class": "d1",
    "dataset": "climate-dt",
    "date": "{current_date}",
    "expver": "0001",
    "generation": "1",
    "levtype": "{levtype}",
    "model": "IFS-NEMO",
    "param": "{param}",
    "realization": "1",
    "resolution": "standard",
    "stream": "clte",
    "time": "0000/1800",
    "type": "fc",
"""
    if levelist:
        script += f'    "levelist": "{levelist}",\n'

    script += f"""    "feature": {{
        "type": "boundingbox",
        "points": {points},
    }}
}}

files = client.retrieve('destination-earth', request, output_file="ClimateDT_{levtype}_{current_date}.json")
"""
    return script, current_date


def fetch_json_from_urls(bucket_contents):
    sfc_data = None
    pl_data = None

    for item in bucket_contents:
        file_path = item.get('name', '')
        download_url = item.get('presignedUrl')

        if "ClimateDT_sfc" in file_path and download_url:
            print(f"\n⬇️ Fetching {os.path.basename(file_path)} into memory...")
            sfc_data = requests.get(download_url).json()

        elif "ClimateDT_pl" in file_path and download_url:
            print(f"\n⬇️ Fetching {os.path.basename(file_path)} into memory...")
            pl_data = requests.get(download_url).json()

    return sfc_data, pl_data


# -------------------------
# Main Execution Function
# -------------------------
def fetch_current_eo4eu_data(lat, lon, timeout_sec=180):
    """
    Executes the EO4EU workflow. Aborts strictly if timeout_sec is reached.
    """
    client = connect_to_client(EO4EU_URL, EO4EU_USERNAME, EO4EU_PASSWORD)
    print("✅ Connected to EO4EU API.")

    fixed_points = [[38.5, 23], [37, 24.5]]

    sfc_script, current_date = generate_polytope_script(levtype="sfc", param="144/141/228/260048", points=fixed_points)
    pl_script, _ = generate_polytope_script(levtype="pl", param="130/131/132/129", points=fixed_points, levelist="500")

    encoded_scripts = [base64.b64encode(s.encode("ascii")).decode("ascii") for s in [pl_script, sfc_script]]

    client.workflow_update(WORKFLOW_ID, {"query": encoded_scripts, "meta": " "})
    client.workflow_start(WORKFLOW_ID)
    print(f"🚀 Workflow started for date: {current_date} evaluating POI ({lat}, {lon})")

    # 4. Wait for completion WITH STRICT TIMEOUT
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_sec:
            print(f"\n⏳ TIMEOUT: EO4EU workflow took longer than {timeout_sec} seconds. Interrupting process...")
            return None  # Actively aborts the loop

        status = get_workflow_status(client, WORKFLOW_ID)
        if status == 'COMPLETED':
            print("✅ Workflow COMPLETED.")
            break
        elif status in ['FAILED', 'ERROR']:
            print(f"❌ Workflow failed with status: {status}")
            return None

        print(f"⏳ Workflow status: {status} (Elapsed: {int(elapsed)}s). Please wait...")
        time.sleep(10)

    # 5. Fetch S3 links and load JSON to memory
    content = client.list_s3_bucket(WORKFLOW_ID)
    sfc_data, pl_data = fetch_json_from_urls(content)

    if not sfc_data or not pl_data:
        print("❌ Failed to retrieve one or both JSON data files.")
        return None

    # 6. Find the closest contained point
    coords = sfc_data['coverages'][0]['domain']['axes']['composite']['values']

    min_dist = float('inf')
    closest_idx = -1
    closest_coord = None

    for idx, coord in enumerate(coords):
        c_lat, c_lon, _ = coord
        dist = haversine_distance(lat, lon, c_lat, c_lon)
        if dist < min_dist:
            min_dist = dist
            closest_idx = idx
            closest_coord = (c_lat, c_lon)

    print(
        f"\n📍 Closest point found at ({closest_coord[0]:.4f}, {closest_coord[1]:.4f}) with a distance of {min_dist:.2f} km.")

    # 7. Extract weather variables
    temp_k = pl_data['coverages'][0]['ranges']['t']['values'][closest_idx]
    u_wind = pl_data['coverages'][0]['ranges']['u']['values'][closest_idx]
    v_wind = pl_data['coverages'][0]['ranges']['v']['values'][closest_idx]
    total_precip_m = sfc_data['coverages'][0]['ranges']['tp']['values'][closest_idx]
    snowfall_m = sfc_data['coverages'][0]['ranges']['sf']['values'][closest_idx]

    # 8. Calculate conditions
    temp_c = temp_k - 273.15
    wind_speed_kmh = math.sqrt(u_wind ** 2 + v_wind ** 2) * 3.6
    rain_mmh = (total_precip_m - snowfall_m) * 1000
    snow_cmh = snowfall_m * 100

    weather = {
        "rain": rain_mmh,
        "snow": snow_cmh,
        "wind": wind_speed_kmh,
        "temp": temp_c
    }

    print(f"\n  Current Climate-DT Conditions for requested location ({lat:.4f}, {lon:.4f}):\n")
    print(f"  🌧️ Rain:         {weather['rain']:.1f} mm/h")
    print(f"  ❄️ Snow:         {weather['snow']:.1f} cm/h")
    print(f"  💨 Wind Speed:   {weather['wind']:.1f} km/h")
    print(f"  🌡️ Temperature:  {weather['temp']:.1f} °C")
    print("-" * 45)

    result_payload = {
        "poi": {"lat": lat, "lon": lon},
        "closest_point": {"lat": closest_coord[0], "lon": closest_coord[1], "distance_km": round(min_dist, 2)},
        "weather": {
            "rain_mmh": round(rain_mmh, 2),
            "snow_cmh": round(snow_cmh, 2),
            "wind_kmh": round(wind_speed_kmh, 2),
            "temp_c": round(temp_c, 2)
        }
    }

    return result_payload