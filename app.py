import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Complete structural key parameters
AI_STUDIO_KEY = "AQ.Ab8RN6LnBF5fs5b2EkkPrmsj1uTrtcSHEY1MNXtLrtp_r1oxCg"
MODEL_NAME = "gemma-4-31b-it"

@app.route('/', methods=['GET', 'POST', 'HEAD'])
@app.route('/v1/chat/completions', methods=['GET', 'POST', 'HEAD'])
@app.route('/chat/completions', methods=['GET', 'POST', 'HEAD'])
def chat_completions():
    # FIXES 415: Instantly responds to Render/Janitor testing handshakes cleanly
    if request.method in ['GET', 'HEAD']:
        return "Proxy server is running successfully 24/7!", 200
        
    data = request.json or {}
    raw_messages = data.get("messages", [])
    formatted_messages = []
    
    for m in raw_messages:
        content_text = m.get("content", "")
        if not content_text:
            continue
            
        role = "user" if m.get("role") in ["user", "system"] else "model"
        
        if formatted_messages and formatted_messages[-1]["role"] == role:
            formatted_messages[-1]["parts"][0]["text"] += f"\n\n{content_text}"
        else:
            formatted_messages.append({"role": role, "parts": [{"text": content_text}]})
            
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
    
    # Explicit endpoint string target
    google_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={AI_STUDIO_KEY}"
    
    try:
        response = requests.post(google_url, json=gemini_payload, headers={"Content-Type": "application/json"})
        
        if response.status_code != 200:
            return jsonify({"error": f"Google rejected request layout: {response.text}"}), response.status_code
            
        res_json = response.json()
        
        try:
            reply_text = res_json['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError):
            try:
                reply_text = res_json['candidates']['content']['parts']['text']
            except Exception:
                if 'promptFeedback' in res_json:
                    reply_text = "[Message dropped by Google's filters]"
                else:
                    reply_text = f"Connected, but parsing failed. Raw context: {str(res_json)}"
        
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": reply_text}, "finish_reason": "stop"}]
        })
    except Exception as e:
        return jsonify({"error": f"Internal proxy error parsing content: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
    
