import os
import io
import base64
import time
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
# We don't need load_dotenv for this specific debug step
import google.generativeai as genai
from PIL import Image
from google.api_core import exceptions

app = Flask(__name__)
CORS(app)

# --- DIRECT CONFIGURATION (Debugging) ---
# We are pasting the key here to bypass any .env file issues.
# ⚠️ WARNING: Only do this for testing. Do not share this file publicly.
API_KEY = "AIzaSyAp5YokgtmyL-hy0VpsvFCRbNjwznXlaKU"

# Clean the key just in case there are hidden spaces
API_KEY = API_KEY.strip()

print(f"✅ DEBUG: Using API Key starting with: {API_KEY[:5]}...")
genai.configure(api_key=API_KEY)

# System Instructions
SYSTEM_INSTRUCTION = """
You are HealthBot AI, a helpful assistant specialized in general health and wellness.
- Analyze symptoms and provide general guidance.
- Analyze medical images (rashes, pills, reports) if provided.
- DISCLAIMER: You are an AI, not a doctor. Always advise the user to consult a professional.
"""

# Model Rotation
MODEL_ROTATION = [
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-2.0-flash-exp',
    'gemini-flash-latest'
]

def process_uploaded_image(file_info):
    try:
        if "preview" in file_info and "base64" in file_info["preview"]:
            base64_data = file_info["preview"].split(",")[1]
        elif "preview" in file_info:
            parts = file_info["preview"].split(",")
            base64_data = parts[1] if len(parts) > 1 else parts[0]
        else:
            return None
        image_bytes = base64.b64decode(base64_data)
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        print(f"⚠️ Image error: {e}")
        return None

@app.route('/')
def health_check():
    return jsonify({"status": "Backend is running with Direct Key"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        uploaded_files = data.get('files', [])
        
        content_parts = []
        if user_message: content_parts.append(user_message)
        if uploaded_files:
            for file_info in uploaded_files:
                img = process_uploaded_image(file_info)
                if img: content_parts.append(img)

        if not content_parts:
            return jsonify({"aiResponse": "Please provide input."})

        last_error = ""
        for model_name in MODEL_ROTATION:
            try:
                time.sleep(random.uniform(0.5, 1.0))
                print(f"🔄 Trying {model_name}...")
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_INSTRUCTION
                )
                response = model.generate_content(content_parts)
                
                print(f"✅ Success using {model_name}")
                return jsonify({"aiResponse": response.text})

            except exceptions.ResourceExhausted:
                print(f"⚠️ Rate Limit on {model_name}. Switching...")
                continue
            except Exception as e:
                print(f"⚠️ Error on {model_name}: {e}")
                last_error = str(e)
                continue

        return jsonify({
            "aiResponse": f"Connection failed. Google says: {last_error}"
        })

    except Exception as e:
        print(f"❌ Server Error: {e}")
        return jsonify({"aiResponse": "Internal Server Error"}), 500

if __name__ == '__main__':
    print("🚀 Starting HealthBot (Debug Mode)...")
    app.run(debug=True, port=5000)