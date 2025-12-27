import os
import io
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image

# Initialize Flask to look for static files in your frontend folder
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# --- PRODUCTION CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY.strip())
else:
    print("❌ ERROR: GEMINI_API_KEY environment variable is missing!")

# Current valid model names for 2025
MODEL_ROTATION = ['gemini-2.0-flash', 'gemini-1.5-flash']

# --- SERVE FRONTEND ---
@app.route('/')
def serve_index():
    # Serves index.html when users visit the root URL
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Serves other static assets like images, CSS, or JS
    return send_from_directory(app.static_folder, path)

# --- CHAT API ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        for model_name in MODEL_ROTATION:
            try:
                model = genai.GenerativeModel(model_name=model_name)
                response = model.generate_content(user_message)
                return jsonify({"aiResponse": response.text})
            except Exception as e:
                print(f"⚠️ {model_name} failed: {e}")
                continue
        return jsonify({"aiResponse": "AI service is currently busy."}), 503
    except Exception as e:
        return jsonify({"aiResponse": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Render requires host 0.0.0.0 and dynamic PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


