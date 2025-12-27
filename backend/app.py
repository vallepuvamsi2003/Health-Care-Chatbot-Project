import os
import io
import base64
import time
import random
from flask import Flask, request, jsonify, send_from_directory # Added send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image
from google.api_core import exceptions

# 1. Initialize Flask with the correct path to your frontend folder
# Since app.py is inside 'backend/', we go up one level to find 'frontend/'
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# --- DIRECT CONFIGURATION ---
API_KEY = "YOUR API KEY" 
API_KEY = API_KEY.strip()
genai.configure(api_key=API_KEY)

SYSTEM_INSTRUCTION = "You are HealthBot AI..."
MODEL_ROTATION = ['gemini-2.0-flash', 'gemini-1.5-flash'] # Note: 2.5 doesn't exist yet

# 2. Update the root route to serve your index.html
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# 3. Add a route to serve other files (CSS, JS, Images)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# --- Keep your /chat and process_uploaded_image functions exactly as they are ---

@app.route('/chat', methods=['POST'])
def chat():
    # ... your existing chat code ...
    pass

if __name__ == '__main__':
    # 4. Use environment variables for Port (required for Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
