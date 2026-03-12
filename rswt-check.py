import json
import requests
import json_utils
from json_utils import parse_json_input

# Import our newly created EO4EU module
from eo4eu_weather import fetch_current_eo4eu_data

api_key = "7bf849c2c869f9f8cbb3bc77be812fd2"

# RSWT thresholds
RSWT_MAP = {
    "rain": [50, 30, 15, 7, 2],  # mm/h
    "snow": [5, 3, 2, 1, 0],  # cm/h
    "wind": [80, 60, 40, 25, 10],  # km/h
    "temp": [(-40, 60), (-20, 50), (-10, 40), (0, 30), (5, 20)]  # °C
}


# -------------------------
# Weather fetching function (Fallback)
# -------------------------
def fetch_weather(api_key, lat, lon):
    """Fetch weather from OpenWeatherMap (Fallback)."""
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        response = requests.get(url).json()
        print("\n📦 OpenWeatherMap Raw Response:")
        print(json.dumps(response, indent=2))

        weather = {
            "rain": response.get("rain", {}).get("1h", 0),
            "snow": response.get("snow", {}).get("1h", 0),
            "wind": response.get("wind", {}).get("speed", 0),
            "temp": response.get("main", {}).get("temp", 18)
        }

        print(f"\n  Current Fallback Weather Conditions for location ({lat:.4f}, {lon:.4f}):\n")
        print(f"  🌧️ Rain (1h):    {weather['rain']:.1f} mm")
        print(f"  ❄️ Snow (1h):    {weather['snow']:.1f} cm")
        print(f"  💨 Wind Speed:   {weather['wind']:.1f} km/h")
        print(f"  🌡️ Temperature:  {weather['temp']:.1f} °C")
        print("-" * 45)

        return weather

    except Exception as e:
        print(f"❌ Fallback OpenWeatherMap API failed: {e}")
        return None


# -------------------------
# Vehicle filtering function
# -------------------------
def is_vehicle_suitable(vehicle, weather):
    RSWT = vehicle["RSWT"]

    # Rain
    rain_limit = RSWT_MAP["rain"][int(RSWT[0]) - 1]
    if weather["rain"] > rain_limit:
        return False

    # Snow
    snow_limit = RSWT_MAP["snow"][int(RSWT[1]) - 1]
    if weather["snow"] > snow_limit:
        return False

    # Wind
    wind_limit = RSWT_MAP["wind"][int(RSWT[2]) - 1]
    if weather["wind"] > wind_limit:
        return False

    # Temperature
    temp_min, temp_max = RSWT_MAP["temp"][int(RSWT[3]) - 1]
    if not (temp_min <= weather["temp"] <= temp_max):
        return False

    return True


# -------------------------
# Filter fleet
# -------------------------
def filter_fleet(json_input):
    lat, lon, vehicles = parse_json_input(json_input)

    if lat is None or lon is None:
        print("❌ Error: Invalid or missing POI in input JSON.")
        return {"error": "Invalid POI"}

    # 1. Attempt to fetch current weather from EO4EU
    print(f"\n🌍 Attempting to fetch primary weather data from EO4EU for ({lat}, {lon})...")

    eo4eu_payload = None
    use_fallback = False
    weather = None

    try:
        # This will internally print the EO4EU JSON payload as requested
        eo4eu_payload = fetch_current_eo4eu_data(lat, lon)
    except Exception as e:
        print(f"\n⚠️ EO4EU API execution error: {e}")

    # 2. Evaluate EO4EU response and distance threshold
    if eo4eu_payload:
        distance = eo4eu_payload.get("closest_point", {}).get("distance_km", float('inf'))

        if distance > 50:
            print(f"\n⚠️ WARNING: Closest EO4EU grid point is {distance} km away (> 50 km threshold).")
            use_fallback = True
        else:
            print("\n✅ Using primary EO4EU weather data.")
            # Map the EO4EU payload keys back to the standard keys our filter expects
            weather = {
                "rain": eo4eu_payload["weather"]["rain_mmh"],
                "snow": eo4eu_payload["weather"]["snow_cmh"],
                "wind": eo4eu_payload["weather"]["wind_kmh"],
                "temp": eo4eu_payload["weather"]["temp_c"]
            }
    else:
        print("\n⚠️ WARNING: EO4EU API returned no data or timed out.")
        use_fallback = True

    # 3. Fallback to OpenWeatherMap if required
    if use_fallback:
        print("🔄 Falling back to OpenWeatherMap API...")
        weather = fetch_weather(api_key, lat, lon)

    # 4. Filter vehicles based on retrieved weather
    if not weather:
        print("❌ Critical Error: Failed to fetch weather data from both EO4EU and OpenWeatherMap.")
        return {"error": "No weather data available"}

    suitable_list = [v for v in vehicles if is_vehicle_suitable(v, weather)]

    # 5. Create the required JSON structure
    result = {
        "suitable_vehicles": [v["id"] for v in suitable_list]
    }

    print("\nResult:", json.dumps(result, indent=4))
    return result


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    fleet = filter_fleet("resources/input.json")