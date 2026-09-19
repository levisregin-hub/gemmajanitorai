import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

AI_STUDIO_KEY = "AQ.Ab8RN6LnBF5fs5b2EkkPrmsj1uTrtcSHEY1MNXtLrtp_r1oxCg"
MODEL_NAME = "gemma-4-31b-it"

@app.route('/', methods=['GET', 'POST'])
@app.route('/v1/chat/completions', methods=['POST'])
@app.route('/chat/completions', methods=['POST'])
def chat_completions():
    if request.method == 'GET':
        return "Proxy server is running successfully 24/7!", 200
        
    data = request.json or {}
    
    # Cleanse and strip-reformat messy structural metadata blocks from JanitorAI
    raw_messages = data.get("messages", [])
    formatted_messages = []
    
    for m in raw_messages:
        content_text = m.get("content", "")
        if not content_text:
            continue
            
        # Convert custom layout strings into structural text blocks
        role = "user" if m.get("role") in ["user", "system"] else "model"
        
        # If consecutive roles match, merge their text contents cleanly
        if formatted_messages and formatted_messages[-1]["role"] == role:
            formatted_messages[-1]["parts"][0]["text"] += f"\n\n{content_text}"
        else:
            formatted_messages.append({"role": role, "parts": [{"text": content_text}]})
            
    # Self-healing fallback if array structure drops entirely
    if not formatted_messages:
        formatted_messages = [{"role": "user", "parts": [{"text": "Hello"}]}]

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"}
    ]

    gemini_payload = {
        "contents": formatted_messages, 
        "safetySettings": safety_settings,
        "generationConfig": {
            "temperature": float(data.get("temperature", 0.7)), 
            "maxOutputTokens": int(data.get("max_tokens", 1000))
        }
    }
    
    google_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={AI_STUDIO_KEY}"
    
    try:
        response = requests.post(google_url, json=gemini_payload, headers={"Content-Type": "application/json"})
        
        # Immediate fallback mapping if server drops an empty value block
        if not response.text or response.status_code != 200:
            return jsonify({"error": f"Google rejected block: {response.text}"}), response.status_code
            
        res_json = response.json()
        
        # Deep structured parsing extraction
        try:
            reply_text = res_json['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError):
            try:
                reply_text = res_json['candidates']['content']['parts']['text']
            except Exception:
                if 'promptFeedback' in res_json:
                    reply_text = "[Message dropped by Google's hard safety filtration lines]"
                else:
                    reply_text = "Connected successfully, but returned an unmappable content index block."
        
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": reply_text}, "finish_reason": "stop"}]
        })
    except Exception as e:
        return jsonify({"error": f"Internal proxy error parsing message: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
    
