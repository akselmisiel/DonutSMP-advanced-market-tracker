from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import json
import os
import gzip
import time
from datetime import datetime, timedelta
from urllib.parse import quote

# Initialize the Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# --- API and File Constants ---
API_TRANSACTIONS_BASE = "https://api.donutsmp.net/v1/auction/transactions/"
API_LISTINGS_BASE = "https://api.donutsmp.net/v1/auction/list/"
API_STATS_BASE = "https://api.donutsmp.net/v1/stats/"
HISTORY_FILE = "market_history.json"
COMPRESSED_HISTORY_FILE = "market_history.json.gz"
MAX_RECORDS = 150000  # Maximum number of records to keep
DAYS_TO_KEEP = 14     # Keep only last 14 days of data

# --- Data Compression & Optimization Functions ---
def compress_transaction(tx):
    """Compress transaction data by removing redundant fields and shortening keys."""
    compressed = {
        'ts': tx.get('unixMillisDateSold'),  # timestamp
        'p': tx.get('price'),                # price
        'i': {                               # item
            'id': tx.get('item', {}).get('id'),
            'c': tx.get('item', {}).get('count', 1),
        },
        's': tx.get('seller', {}).get('name') # seller name only
    }
    
    # Add enchantments if present
    item = tx.get('item', {})
    enchants = item.get('enchants', {})
    if enchants and enchants.get('enchantments', {}).get('levels'):
        compressed['i']['e'] = enchants['enchantments']['levels']
    
    # Add trim if present
    if enchants and enchants.get('trim'):
        compressed['i']['t'] = enchants['trim']
    
    # Add contents if present (for shulker boxes)
    if item.get('contents'):
        compressed['i']['cont'] = item['contents']
    
    return compressed

def decompress_transaction(compressed_tx):
    """Convert compressed transaction back to original format."""
    return {
        'unixMillisDateSold': compressed_tx.get('ts'),
        'price': compressed_tx.get('p'),
        'item': {
            'id': compressed_tx.get('i', {}).get('id'),
            'count': compressed_tx.get('i', {}).get('c', 1),
            'enchants': {
                'enchantments': {'levels': compressed_tx.get('i', {}).get('e', {})},
                'trim': compressed_tx.get('i', {}).get('t')
            } if compressed_tx.get('i', {}).get('e') or compressed_tx.get('i', {}).get('t') else {},
            'contents': compressed_tx.get('i', {}).get('cont', [])
        },
        'seller': {'name': compressed_tx.get('s')}
    }

def cleanup_old_data(records, days_to_keep=DAYS_TO_KEEP):
    """Remove records older than specified days."""
    if not records:
        return records
    
    cutoff_time = int((datetime.now() - timedelta(days=days_to_keep)).timestamp() * 1000)
    return [r for r in records if r.get('ts', 0) >= cutoff_time]

def optimize_data_storage(records):
    """Optimize storage by removing duplicates and old data."""
    if not records:
        return []
    
    # Remove duplicates based on timestamp, price, item, and seller
    seen = set()
    unique_records = []
    
    for record in records:
        # Create a unique key for deduplication
        key = (
            record.get('ts'),
            record.get('p'),
            record.get('i', {}).get('id'),
            record.get('s')
        )
        
        if key not in seen:
            seen.add(key)
            unique_records.append(record)
    
    # Sort by timestamp
    unique_records.sort(key=lambda x: x.get('ts', 0))
    
    # Keep only the most recent records if we exceed the limit
    if len(unique_records) > MAX_RECORDS:
        unique_records = unique_records[-MAX_RECORDS:]
    
    # Remove old data
    unique_records = cleanup_old_data(unique_records)
    
    return unique_records

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
        return jsonify([])
    try:
        with open(HISTORY_FILE, 'r') as f:
            compressed_data = json.load(f)
        
        # Convert compressed data back to original format
        decompressed_data = [decompress_transaction(tx) for tx in compressed_data]
        return jsonify(decompressed_data)
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Could not read history file: {e}"}), 500

@app.route('/history', methods=['POST'])
def save_history():
    """Receives new transaction records and saves them optimized to the local JSON file."""
    new_records = request.get_json()
    if not isinstance(new_records, list):
        return jsonify({"error": "Invalid data format; expected a list of records"}), 400
    
    try:
        all_records = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try:
                    all_records = json.load(f)
                except json.JSONDecodeError:
                    all_records = []
        
        # Compress new records and add to existing
        compressed_new = [compress_transaction(tx) for tx in new_records]
        all_records.extend(compressed_new)
        
        # Optimize storage (remove duplicates, old data, etc.)
        optimized_records = optimize_data_storage(all_records)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(optimized_records, f, separators=(',', ':'))  # Compact JSON
            
        return jsonify({
            "status": "success", 
            "total_records": len(optimized_records),
            "compression_ratio": f"{len(optimized_records)/max(len(all_records), 1):.2f}"
        })
    except (IOError, TypeError) as e:
        return jsonify({"error": f"Could not write to history file: {e}"}), 500

        with open(HISTORY_FILE, 'w') as f:
            json.dump(all_records, f, indent=2)
            
        return jsonify({"status": "success", "added": len(new_records)})
    except (IOError, TypeError) as e:
        return jsonify({"error": f"Could not write to history file: {e}"}), 500

@app.route('/history/overwrite', methods=['POST'])
def overwrite_history():
    """Receives a complete list of transaction records and overwrites the local JSON file with optimization."""
    new_records = request.get_json()
    if not isinstance(new_records, list):
        return jsonify({"error": "Invalid data format; expected a list of records"}), 400
    try:
        # Compress the records
        compressed_records = [compress_transaction(tx) for tx in new_records]
          # Optimize storage
        optimized_records = optimize_data_storage(compressed_records)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(optimized_records, f, separators=(',', ':'))  # Compact JSON
            
        return jsonify({
            "status": "success", 
            "total_records": len(optimized_records),
            "compression_ratio": f"{len(optimized_records)/max(len(new_records), 1):.2f}"
        })
    except (IOError, TypeError) as e:
        return jsonify({"error": f"Could not write to history file: {e}"}), 500

@app.route('/history/cleanup', methods=['POST'])
def cleanup_history():
    """Manually trigger cleanup of old data and optimization."""
    try:
        if not os.path.exists(HISTORY_FILE):
            return jsonify({"status": "success", "message": "No history file to clean"})
        
        with open(HISTORY_FILE, 'r') as f:
            records = json.load(f)
        
        original_count = len(records)
        optimized_records = optimize_data_storage(records)
        new_count = len(optimized_records)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(optimized_records, f, separators=(',', ':'))
        
        return jsonify({
            "status": "success",
            "original_records": original_count,
            "cleaned_records": new_count,
            "removed": original_count - new_count,
            "compression_ratio": f"{new_count/max(original_count, 1):.2f}"
        })
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Could not cleanup history: {e}"}), 500

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