import os
import io
import base64
import time
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image
from google.api_core import exceptions

app = Flask(__name__)
CORS(app)

# --- PRODUCTION CONFIGURATION ---
# Securely load the key from Render's Environment Variables tab
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY.strip())
    print("✅ Gemini API configured via Render Environment.")
else:
    print("❌ ERROR: GEMINI_API_KEY environment variable not set!")

SYSTEM_INSTRUCTION = """
You are HealthBot AI, a helpful assistant specialized in general health and wellness.
- Analyze symptoms and provide general guidance.
- Analyze medical images (rashes, pills, reports) if provided.
- DISCLAIMER: You are an AI, not a doctor. Always advise the user to consult a professional.
"""

# Updated for Late 2025 Stability
MODEL_ROTATION = [
    'gemini-2.0-flash',      # Fastest, most reliable
    'gemini-2.5-flash',      # High capability
    'gemini-1.5-flash-8b',   # Lightweight fallback
    'gemini-flash-latest'    # Alias for latest stable
]

def process_uploaded_image(file_info):
    try:
        if "preview" in file_info and "base64" in file_info["preview"]:
            base64_data = file_info["preview"].split(",")[1]
            image_bytes = base64.b64decode(base64_data)
            return Image.open(io.BytesIO(image_bytes))
        return None
    except Exception as e:
        print(f"⚠️ Image error: {e}")
        return None

@app.route('/')
def health_check():
    return jsonify({"status": "Online", "service": "HealthBot AI"}), 200

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

        # Retry logic for 503 errors (overloaded models)
        for model_name in MODEL_ROTATION:
            try:
                model = genai.GenerativeModel(model_name=model_name, system_instruction=SYSTEM_INSTRUCTION)
                response = model.generate_content(content_parts)
                return jsonify({"aiResponse": response.text})
            except Exception as e:
                print(f"⚠️ {model_name} failed: {e}")
                continue
        
        return jsonify({"aiResponse": "Service temporarily overloaded. Please try again."}), 503

    except Exception as e:
        return jsonify({"aiResponse": "Internal Server Error"}), 500

if __name__ == '__main__':
    # RENDER BINDING: Use 0.0.0.0 and the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

