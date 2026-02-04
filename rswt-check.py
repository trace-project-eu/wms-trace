import json

import requests
import json_utils
from json_utils import parse_json_input

api_key = "7bf849c2c869f9f8cbb3bc77be812fd2"

# RSWT thresholds
RSWT_MAP = {
    "rain":   [50, 30, 15, 7, 2],    # mm/h
    "snow":   [5, 3, 2, 1, 0],       # cm/h
    "wind":   [80, 60, 40, 25, 10],  # km/h
    "temp":   [(-40,60), (-20,50), (-10,40), (0,30), (5,20)]  # °C
}

# -------------------------
# Weather fetching function
# -------------------------
def fetch_weather(api_key, lat, lon):
    """Fetch weather from OpenWeatherMap (example)."""
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url).json()

    print(response)

    weather = {
        "rain": response.get("rain", {}).get("1h", 0),
        "snow": response.get("snow", {}).get("1h", 0),
        "wind": response.get("wind", {}).get("speed", 0),
        "temp": response.get("main", {}).get("temp", 18)
    }

    print(f"\n  Current Weather Conditions for location ({lat:.4f}, {lon:.4f}):\n")
    print(f"  🌧️ Rain (1h):    {weather['rain']:.1f} mm")
    print(f"  ❄️ Snow (1h):    {weather['snow']:.1f} cm")
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
    rain_limit = RSWT_MAP["rain"][int(RSWT[0])-1]
    if weather["rain"] > rain_limit:
        return False

    # Snow
    snow_limit = RSWT_MAP["snow"][int(RSWT[1])-1]
    if weather["snow"] > snow_limit:
        return False

    # Wind
    wind_limit = RSWT_MAP["wind"][int(RSWT[2])-1]
    if weather["wind"] > wind_limit:
        return False

    # Temperature
    temp_min, temp_max = RSWT_MAP["temp"][int(RSWT[3])-1]
    if not (temp_min <= weather["temp"] <= temp_max):
        return False

    return True

# -------------------------
# Filter fleet
# -------------------------
def filter_fleet(json_input):
    lat, lon, vehicles = parse_json_input(json_input)

    # 1. Fetch current weather
    weather = fetch_weather(api_key, lat, lon)

    # 2. Filter vehicles
    # (Assuming is_vehicle_suitable is defined as before)
    suitable_list = [v for v in vehicles if is_vehicle_suitable(v, weather)]

    # 3. Create the required JSON structure
    result = {
        "suitable_vehicles": [v["id"] for v in suitable_list]
    }

    # Optional: Print for debugging
    print("Result:", json.dumps(result, indent=4))

    return result

# -------------------------
# 5. Example usage
# -------------------------
if __name__ == "__main__":

    fleet = filter_fleet("input.json")
