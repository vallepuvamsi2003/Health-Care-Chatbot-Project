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

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# --- CONFIGURATION ---
API_KEY = "YOUR_ACTUAL_API_KEY_HERE" # Ensure this is your real key
genai.configure(api_key=API_KEY.strip())

SYSTEM_INSTRUCTION = "You are HealthBot AI, a helpful medical assistant..."
MODEL_ROTATION = ['gemini-1.5-flash', 'gemini-1.5-pro'] 

# --- FILE SERVING ---
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# --- HELPER FUNCTIONS ---
def process_uploaded_image(file_info):
    try:
        if "preview" in file_info and "base64" in file_info["preview"]:
            base64_data = file_info["preview"].split(",")[1]
            image_bytes = base64.b64decode(base64_data)
            return Image.open(io.BytesIO(image_bytes))
        return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

# --- CHAT ROUTE (FIXED) ---
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

        # Loop through models in case one fails
        for model_name in MODEL_ROTATION:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_INSTRUCTION
                )
                response = model.generate_content(content_parts)
                return jsonify({"aiResponse": response.text})
            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                continue # Try the next model
        
        return jsonify({"aiResponse": "I'm sorry, I'm having trouble connecting to my brain right now."}), 503

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"aiResponse": "Internal Server Error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
