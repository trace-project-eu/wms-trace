# Fleet Weather & RSWT Suitability Checker

A Python-based tool to evaluate and filter a fleet of vehicles based on real-time weather conditions at a specific Point of Interest (POI). 

This script determines if a vehicle can safely operate in a given area by comparing current weather data against the vehicle's **RSWT (Rain, Snow, Wind, Temperature)** capability thresholds. It primarily fetches high-fidelity DestinE Climate-DT data via the **EO4EU API** and seamlessly falls back to the **OpenWeatherMap API** if the EO4EU grid data is too far away or unavailable.

---

## Features

* **Dual-Source Weather Routing:** Attempts to fetch weather via an asynchronous EO4EU workflow first. If the workflow fails, times out, or the closest EO4EU grid point is more than 50 km from the POI, it falls back to OpenWeatherMap.
* **In-Memory Data Processing:** Downloads massive Polytope/Climate-DT S3 JSON payloads directly into memory using pre-signed URLs—avoiding local disk clutter.
* **Haversine Distance Matching:** Automatically calculates the great-circle distance to find the exact Climate-DT grid point closest to your POI.
* **Dynamic RSWT Filtering:** Evaluates each vehicle against strict operational thresholds for Rain (mm/h), Snow (cm/h), Wind (km/h), and Temperature (°C).

---

## Project Structure

* **`rswt-check.py`**: The main execution script. Orchestrates the fetching of weather, handles the fallback logic, and filters the vehicle fleet.
* **`eo4eu_weather.py`**: Interacts with the EO4EU API. Generates dynamic Polytope payloads, polls the workflow status, fetches S3 links, parses the meteorological parameters (U/V wind vectors, temp, precip), and calculates distances.
* **`json_utils.py`**: Helper functions to safely parse the input JSON file containing the POI and fleet data.
* **`requirements.txt`**: Lists all the Python dependencies required to run the project.
* **`.gitignore`**: Prevents caching files, virtual environments, local logs, and temporary JSON payloads from being committed to the repository.

---

## Prerequisites & Installation

* **Python 3.8+**

Install all the required standard Python packages at once using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## Configuration

Before running the application, you need to configure your API credentials. 

**Important:** Currently, credentials for EO4EU and OpenWeatherMap are hardcoded in the `.py` files. It is highly recommended to move these to environment variables (e.g., `.env`) before deploying to production.

* **EO4EU Credentials:** Located at the top of `eo4eu_weather.py` (`EO4EU_USERNAME`, `EO4EU_PASSWORD`, `WORKFLOW_ID`).
* **DestinE Credentials:** Required for the Polytope payload. Ensure `DESTINY_USER_EMAIL` and `DESTINY_API_KEY` are set as system environment variables.
* **OpenWeatherMap API Key:** Located in `rswt-check.py` (`api_key`).

---

## Input Format

The script reads the POI and fleet data from a JSON file (by default, it looks for `resources/input.json`).

**Example `input.json` structure:**
```json
{
  "poi": {
    "lat": 37.9838,
    "lon": 23.7275
  },
  "vehicles": [
    {
      "id": "truck_01",
      "RSWT": "2131"
    },
    {
      "id": "van_02",
      "RSWT": "3124"
    },
    {
      "id": "scooter_01",
      "RSWT": "5545"
    }
  ]
}
```
*Note: The `RSWT` string maps to specific threshold levels (1-5) for Rain, Snow, Wind, and Temperature defined in `rswt-check.py`.*

---

## Usage

To run the fleet suitability check, execute the main script from your terminal:

```bash
python rswt-check.py
```

### Expected Output Process:
1. The script will attempt to connect to the EO4EU API.
2. It will submit the dynamically generated Polytope scripts and wait for the workflow to complete.
3. It downloads the `pl` and `sfc` JSON coverages into memory and prints the closest found grid point.
4. If the point is within 50 km, it prints the extracted weather and filters the fleet.
5. If the point is >50 km away, it prints a warning and fetches OpenWeatherMap data instead.
6. Outputs a final JSON dictionary containing the `"suitable_vehicles"`.