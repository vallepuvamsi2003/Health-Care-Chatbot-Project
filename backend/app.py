import os
import io
import base64
import time
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image
from google.api_core import exceptions

# Initialize Flask to look for the 'frontend' folder one level up
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# --- CONFIGURATION ---
API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual key
genai.configure(api_key=API_KEY.strip())

SYSTEM_INSTRUCTION = """
You are HealthBot AI, a helpful assistant specialized in general health and wellness.
- Analyze symptoms and provide general guidance.
- Analyze medical images if provided.
- DISCLAIMER: You are an AI, not a doctor. Always advise consulting a professional.
"""

MODEL_ROTATION = ['gemini-1.5-flash', 'gemini-1.5-pro']

# --- ROUTES TO SERVE FRONTEND ---

@app.route('/')
def serve_index():
    """Serves index.html when you visit the main URL."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serves CSS, JS, and Images."""
    return send_from_directory(app.static_folder, path)

# --- API LOGIC ---

def process_uploaded_image(file_info):
    try:
        if "preview" in file_info and "base64" in file_info["preview"]:
            base64_data = file_info["preview"].split(",")[1]
        else:
            return None
        image_bytes = base64.b64decode(base64_data)
        return Image.open(io.BytesIO(image_bytes))
    except Exception:
        return None

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        uploaded_files = data.get('files', [])
        
        content_parts = []
        if user_message: content_parts.append(user_message)
        if uploaded_files:
            for f in uploaded_files:
                img = process_uploaded_image(f)
                if img: content_parts.append(img)

        if not content_parts:
            return jsonify({"aiResponse": "Please provide input."})

        # Try models in rotation
        for model_name in MODEL_ROTATION:
            try:
                model = genai.GenerativeModel(model_name=model_name, system_instruction=SYSTEM_INSTRUCTION)
                response = model.generate_content(content_parts)
                return jsonify({"aiResponse": response.text})
            except Exception:
                continue

        return jsonify({"aiResponse": "Service temporarily busy. Please try again."})
    except Exception as e:
        return jsonify({"aiResponse": "Internal Server Error"}), 500

if __name__ == '__main__':
    # Bind to 0.0.0.0 and use the PORT provided by Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
