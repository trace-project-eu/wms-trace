# Fleet RSWT Weather Checker

This tool checks if a fleet of vehicles can safely operate at a specific location (POI) based on real-time weather conditions. It compares the current weather against each vehicle's **RSWT (Rain, Snow, Wind, Temperature)** limits.

It fetches high-quality weather data from the **EO4EU API** and automatically falls back to **OpenWeatherMap** if the data is unavailable, takes longer than 3 minutes to download, or is too far away.

---

## Setup & Installation

1. **Install requirements (if running locally):**

    pip install -r requirements.txt

2. **Set up API Keys:** * Update the EO4EU and OpenWeatherMap credentials directly inside `eo4eu_weather.py` and `rswt_check.py`.

---

## Project Files

* **`app.py`**: The Flask web server that turns the checker into a REST API.
* **`rswt_check.py`**: The core script handling the weather fallback and filtering logic (renamed with an underscore for API compatibility).
* **`eo4eu_weather.py`**: Handles the EO4EU connection and the 3-minute timeout.
* **`json_utils.py`**: A helper file to safely read your input data from local files or API payloads.
* **`test_api.py`**: A quick script to test your running API.
* **`Dockerfile`**: Containerizes the application so it always runs perfectly, regardless of your local environment.

---

## Input Format

The tool accepts data either from a JSON file (like `resources/input.json`) or directly via an API `POST` request payload.

**Example JSON structure:**

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

*Note: The `RSWT` string maps to specific threshold levels (1-5) for Rain, Snow, Wind, and Temperature defined in `rswt_check.py`.*

---

## How to Run

You can now run this tool in two different ways:

### Option 1: Run as a REST API (Docker)
This runs the tool as a background web server that can constantly accept incoming requests.

1. Build the Docker image:
    docker build -t fleet-rswt-api .

2. Run the container (inserting your real keys)

3. Test the API by running the tester script in your terminal:
    python test_api.py

### Option 2: Run Locally (Terminal)
If you just want to run a one-off test against a local file without using the API:

    python rswt_check.py