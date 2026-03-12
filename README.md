# Fleet RSWT Weather Checker

This tool checks if a fleet of vehicles can safely operate at a specific location (POI) based on real-time weather conditions. It compares the current weather against each vehicle's **RSWT (Rain, Snow, Wind, Temperature)** limits.

It fetches high-quality weather data from the **EO4EU API** and automatically falls back to **OpenWeatherMap** if the data is unavailable, takes longer than 3 minutes to download, or is too far away.

---

## Setup & Installation

1. **Install requirements:**

    pip install -r requirements.txt

2. **Set up API Keys:** * Update the EO4EU and OpenWeatherMap credentials directly inside `eo4eu_weather.py` and `rswt-check.py`.
    * Make sure your DestinE environment variables (`DESTINY_USER_EMAIL`, `DESTINY_API_KEY`) are active on your system.

---

## Project Files

* **`rswt-check.py`**: The main script you will run.
* **`eo4eu_weather.py`**: Handles the EO4EU connection and the 5-minute timeout.
* **`json_utils.py`**: A small helper file to read your input data.
* **`requirements.txt`**: Lists all the Python dependencies required to run the project.

---

## Input Format

The script reads the POI and fleet data from a JSON file (by default, it looks for `resources/input.json`).

**Example `input.json` structure:**

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

*Note: The `RSWT` string maps to specific threshold levels (1-5) for Rain, Snow, Wind, and Temperature defined in `rswt-check.py`.*

---

## How to Run

Simply execute the main script in your terminal:

    python rswt-check.py

The script will display the weather conditions it found, let you know if it had to use the OpenWeatherMap fallback, and output the final list of suitable vehicles.