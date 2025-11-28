import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io
import base64

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# NOTE: The API key is securely managed by the environment.
# When running locally, it uses the .env file.
# When deployed, it will use the environment variables set on the server.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. API calls might fail.")
    # This warning is helpful for local development.


# Initialize the generative model with a system instruction
genai.configure(api_key=GEMINI_API_KEY)

# --- UPDATED SYSTEM INSTRUCTION ---
# This instruction now explicitly tells the model it can analyze images
# and provides strict safety guidelines for doing so.
system_instruction = """
You are a helpful AI assistant specialized in providing general information about health and wellness.
Your purpose is to answer user questions related to healthcare topics, including analyzing images provided by the user.

- You can interpret and analyze healthcare-related images such as skin rashes, pills, medical equipment, or general health photos.
- Provide general, helpful information based on the image. For example: "This image appears to show a red, bumpy rash. Common causes for such rashes can include..." or "This pill has markings that are often associated with...".
- **Crucial Safety Rule:** You MUST NOT provide a medical diagnosis or medical advice. Always state clearly that your analysis is informational only and NOT a diagnosis. You MUST always recommend that the user consults a qualified healthcare professional for any medical concerns, diagnosis, or treatment.
- You must not answer any questions or analyze images outside of the healthcare domain.
- If a user asks a non-healthcare question or uploads a non-healthcare image (e.g., a car, a landscape, a document), you must politely decline and state that you can only assist with healthcare-related topics and images.
"""

# --- UPDATED MODEL ---
# Using a newer model version that is also multimodal
model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025', system_instruction=system_instruction)


# --- Utility Functions ---
def exponential_backoff_generate_content(model_instance, contents, max_retries=5, initial_delay=1.0):
    """
    Calls generate_content with exponential backoff for robustness.
    """
    delay = initial_delay
    for i in range(max_retries):
        try:
            # Generate content using the new gemini-2.5-flash-preview-09-2025 model
            response = model_instance.generate_content(contents)
            return response
        except Exception as e:
            # This handles transient errors like rate limiting
            print(f"Attempt {i+1} failed: {e}")
            if i < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                print("All retries failed.")
                return None # <-- Return None instead of raising an error
    return None

def create_model_content(user_message, uploaded_files):
    """
    Formats the user message and uploaded files into a content list for the model.
    """
    contents = []
    
    # Add the user's text message if it exists
    if user_message:
        contents.append({'text': user_message})

    # Add images to the content list if they exist
    if uploaded_files:
        for file in uploaded_files:
            try:
                # Extract base64 data and MIME type from the data URL
                file_type = file['type']
                # Ensure we only process images
                if not file_type.startswith("image/"):
                    print(f"Skipping non-image file: {file['name']}")
                    continue
                    
                base64_data = file['preview'].split(",")[1]
                
                # Decode the base64 string
                image_data = base64.b64decode(base64_data)
                
                # Open the image using PIL (Pillow)
                image = Image.open(io.BytesIO(image_data))
                
                # Append the image part to the content list
                contents.append(image)
            except Exception as e:
                print(f"Error processing image file: {e}")
                continue # Skip to the next file if an error occurs
    
    # If no text and no valid images, return empty
    if not contents:
        return [{'text': ''}] # Send empty text if no valid content
        
    return contents


# --- API Endpoints ---

@app.route('/')
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "Backend is running! Access frontend separately."})

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handles incoming chat messages, interacts with Gemini API, and returns responses.
    """
    data = request.json
    user_id = data.get('userId')
    conversation_id = data.get('conversationId')
    user_message = data.get('message', '').strip() # Get message, default to empty string
    uploaded_files = data.get('files', [])
    frontend_chat_history = data.get('chatHistory', [])

    if not all([user_id, conversation_id]):
         return jsonify({"error": "Missing userId or conversationId"}), 400

    if not user_message and not uploaded_files:
        return jsonify({"error": "Missing message or file"}), 400

    print(f"Received message from User: {user_id}, Conv: {conversation_id}, Message: {user_message}")
    
    # Prepare contents for the Gemini model
    gemini_conversation = frontend_chat_history
    
    # Add the user's new message and files to the history for the model to process
    new_user_content = create_model_content(user_message, uploaded_files)
    
    # Only append if there is valid content
    if new_user_content and (new_user_content[0].get('text') or len(new_user_content) > 1):
        gemini_conversation.append({'role': 'user', 'parts': new_user_content})
    else:
        # Handle case where user sent a non-image file or something went wrong
        print("No valid content to send to model.")
        return jsonify({"aiResponse": "I'm sorry, I was unable to process the file you uploaded. I can only analyze images."})


    print("Gemini conversation history being sent (last 2 turns):", gemini_conversation[-2:])

    try:
        # Use the robust function
        gemini_response = exponential_backoff_generate_content(model, gemini_conversation)

        if gemini_response and gemini_response.candidates and gemini_response.candidates[0].content:
            ai_response_text = gemini_response.candidates[0].content.parts[0].text
            print(f"AI Response: {ai_response_text}")
            
            # The new system prompt handles non-healthcare images,
            # so we can remove any manual checks here.
            
            return jsonify({"aiResponse": ai_response_text})
        else:
            print(f"Gemini API returned no content or unexpected structure: {gemini_response}")
            return jsonify({"error": "Failed to get AI response: No content from model."}), 500

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": f"Failed to get AI response: {str(e)}"}), 500

if __name__ == '__main__':
    # Running on port 5000
    app.run(debug=True, port=5000)

