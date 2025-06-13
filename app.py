from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import json
import os
from urllib.parse import quote

# Initialize the Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# --- API and File Constants ---
API_TRANSACTIONS_BASE = "https://api.donutsmp.net/v1/auction/transactions/"
API_LISTINGS_BASE = "https://api.donutsmp.net/v1/auction/list/"
API_STATS_BASE = "https://api.donutsmp.net/v1/stats/"
HISTORY_FILE = "market_history.json"

# --- Helper function to get headers ---
def _get_auth_header():
    """Extracts the Authorization header from the incoming request."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    return {"Authorization": auth_header}

# --- Proxy Endpoints for DonutSMP API ---

@app.route('/transactions/<int:page>', methods=['GET'])
def get_transactions(page):
    """Proxies requests to the DonutSMP transactions endpoint."""
    headers = _get_auth_header()
    if not headers:
        return jsonify({"error": "Authorization token is missing"}), 401
    try:
        response = requests.get(f"{API_TRANSACTIONS_BASE}{page}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/listings/<int:page>', methods=['GET'])
def get_listings(page):
    """Proxies requests to the DonutSMP listings endpoint."""
    headers = _get_auth_header()
    if not headers:
        return jsonify({"error": "Authorization token is missing"}), 401
    try:
        response = requests.get(f"{API_LISTINGS_BASE}{page}", headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/<username>', methods=['GET'])
def get_player_stats(username):
    """Proxies requests to the DonutSMP player stats endpoint."""
    headers = _get_auth_header()
    if not headers:
        return jsonify({"error": "Authorization token is missing"}), 401
    
    # URL encode the username to handle special characters (like '.' for Bedrock players)
    encoded_username = quote(username, safe='')
    
    try:
        response = requests.get(f"{API_STATS_BASE}{encoded_username}", headers=headers)
        if response.status_code == 404:
            return jsonify({"result": {"money": "Unknown"}})
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# --- Local Data Persistence Endpoints ---

@app.route('/history', methods=['GET'])
def get_history():
    """Reads and returns all historical data from the local JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return jsonify([]) # Return empty list if no history exists
    try:
        with open(HISTORY_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Could not read history file: {e}"}), 500

@app.route('/history', methods=['POST'])
def save_history():
    """Receives new transaction records and appends them to the local JSON file."""
    new_records = request.get_json()
    if not isinstance(new_records, list):
        return jsonify({"error": "Invalid data format; expected a list of records"}), 400
    
    try:
        all_records = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                # Handle case where file is empty or malformed
                try:
                    all_records = json.load(f)
                except json.JSONDecodeError:
                    all_records = []
        
        all_records.extend(new_records)
        
        # Sort by timestamp before saving
        all_records.sort(key=lambda x: x.get('unixMillisDateSold', 0))

        with open(HISTORY_FILE, 'w') as f:
            json.dump(all_records, f, indent=2)
            
        return jsonify({"status": "success", "added": len(new_records)})
    except (IOError, TypeError) as e:
        return jsonify({"error": f"Could not write to history file: {e}"}), 500

@app.route('/history/overwrite', methods=['POST'])
def overwrite_history():
    """Receives a complete list of transaction records and overwrites the local JSON file."""
    new_records = request.get_json()
    if not isinstance(new_records, list):
        return jsonify({"error": "Invalid data format; expected a list of records"}), 400
    try:
        # Sort by timestamp before saving
        new_records.sort(key=lambda x: x.get('unixMillisDateSold', 0))
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(new_records, f, indent=2)
            
        return jsonify({"status": "success", "total_records": len(new_records)})
    except (IOError, TypeError) as e:
        return jsonify({"error": f"Could not write to history file: {e}"}), 500

# --- Serve the frontend ---
@app.route('/')
def serve_frontend():
    """Serves the main HTML file."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serves static files like CSS, JS, images, etc."""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)