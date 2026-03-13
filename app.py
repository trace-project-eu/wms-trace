from flask import Flask, request, jsonify
from rswt_check import filter_fleet

app = Flask(__name__)


@app.route('/api/check-fleet', methods=['POST'])
def check_fleet():
    """
    Expects a JSON payload with 'poi' and 'vehicles'.
    Returns the suitable vehicles based on the RSWT conditions.
    """
    try:
        # Get the JSON payload from the incoming HTTP request
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        print(f"\n📥 Received API request for {len(data.get('vehicles', []))} vehicles.")

        # Pass the dictionary directly to your filtering logic
        result = filter_fleet(data)

        # Handle errors returned by the filter
        if "error" in result:
            return jsonify(result), 400

        # Return the successful result as a JSON response
        return jsonify(result), 200

    except Exception as e:
        print(f"❌ Internal Server Error: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


if __name__ == '__main__':
    # Run the Flask app on port 5000
    print("🌐 Starting RSWT Fleet Checker API on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)