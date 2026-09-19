import os
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Official SDK Client Setup using your AI Studio Key
AI_STUDIO_KEY = "AQ.Ab8RN6LnBF5fs5b2EkkPrmsj1uTrtcSHEY1MNXtLrtp_r1oxCg"
client = genai.Client(api_key=AI_STUDIO_KEY)
MODEL_NAME = "gemma-4-31b-it"

@app.route('/', methods=['GET', 'POST', 'HEAD'])
@app.route('/v1/chat/completions', methods=['GET', 'POST', 'HEAD'])
@app.route('/chat/completions', methods=['GET', 'POST', 'HEAD'])
def chat_completions():
    if request.method in ['GET', 'HEAD']:
        return "Proxy server is running successfully 24/7!", 200
        
    data = request.json or {}
    raw_messages = data.get("messages", [])
    
    # Structure the conversation logs using official types.Content layout
    contents = []
    system_instruction = None
    
    for m in raw_messages:
        content_text = m.get("content", "")
        if not content_text:
            continue
            
        role_type = m.get("role", "user")
        
        # Pull out System settings cleanly to deliver as a root instruction parameter
        if role_type == "system":
            system_instruction = content_text
            continue
            
        sdk_role = "user" if role_type == "user" else "model"
        contents.append(
            types.Content(
                role=sdk_role,
                parts=[types.Part.from_text(text=content_text)]
            )
        )
        
    if not contents:
        contents = [types.Content(role="user", parts=[types.Part.from_text(text="Hello")])]

    # Complete backend safety configuration bypass parameters
    safety_settings = [
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    ]

    generation_config = types.GenerateContentConfig(
        temperature=float(data.get("temperature", 0.7)),
        max_output_tokens=int(data.get("max_tokens", 1000)),
        safety_settings=safety_settings,
        system_instruction=system_instruction
    )
    
    try:
        # Generate completion through the official Google client engine
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=generation_config
        )
        
        reply_text = response.text or "[Empty response block returned from Google server]"
        
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": reply_text}, "finish_reason": "stop"}]
        })
    except Exception as e:
        return jsonify({"error": f"Google client processing error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
    
