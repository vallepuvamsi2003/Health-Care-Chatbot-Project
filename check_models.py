import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API Key not found in .env")
else:
    genai.configure(api_key=api_key)
    print(f"Checking models for key: {api_key[:5]}...")
    try:
        print("\n--- AVAILABLE MODELS ---")
        count = 0
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
                count += 1
        if count == 0:
            print("⚠️ No models found! Your API Key might be invalid or has no permissions.")
    except Exception as e:
        print(f"❌ Error listing models: {e}")