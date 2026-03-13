import requests
import json

# The URL where your Flask app is running
API_URL = "http://127.0.0.1:5000/api/check-fleet"


def test_successful_request():
    """Test the API with a valid payload."""
    print("🚀 Sending valid request to API...")

    # Mock payload mirroring your input.json structure
    payload = {
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

    try:
        # Send POST request
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        # Print results
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=4))
        print("-" * 40)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API. Is your Flask server running?")


def test_missing_data_request():
    """Test the API with an invalid payload to ensure error handling works."""
    print("\n🚀 Sending invalid request (missing coordinates) to API...")

    payload = {
        "poi": {},  # Missing lat and lon!
        "vehicles": [
            {"id": "truck_01", "RSWT": "2131"}
        ]
    }

    try:
        response = requests.post(API_URL, json=payload)

        print(f"Status Code: {response.status_code} (Expected 400)")
        print("Response Body:")
        print(json.dumps(response.json(), indent=4))

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API.")


if __name__ == "__main__":
    # Run the tests
    test_successful_request()
    test_missing_data_request()