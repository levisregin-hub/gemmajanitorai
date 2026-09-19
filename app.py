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
        return "Proxy server is officially running 24/7!", 200
        
    data = request.json or {}
    headers = {"Content-Type": "application/json", "x-goog-api-key": AI_STUDIO_KEY}
    
    formatted_messages = []
    for m in data.get("messages", []):
        role = "user" if m["role"] == "user" else "model"
        formatted_messages.append({"role": role, "parts": [{"text": m["content"]}]})
        
    if not formatted_messages:
        return jsonify({"choices": [{"message": {"role": "assistant", "content": "Proxy connected successfully!"}, "finish_reason": "stop"}]})

    # Complete safety filter bypass configuration block
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
    
    google_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"
    
    try:
        response = requests.post(google_url, json=gemini_payload, headers=headers)
        res_json = response.json()
        
        if response.status_code != 200:
            return jsonify({"error": f"Google rejected request: {response.text}"}), response.status_code
            
        # Parse text output cleanly out of Google structure
        try:
            reply_text = res_json['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            if 'promptFeedback' in res_json:
                reply_text = "[Message blocked by Google's hard filters or parsing issue]"
            else:
                reply_text = "Connected, but returned an empty structural message format."
        
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": reply_text}, "finish_reason": "stop"}]
        })
    except Exception as e:
        return jsonify({"error": f"Internal proxy error parsing message: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
