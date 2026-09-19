import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Secure key locked directly into your host machine
AI_STUDIO_KEY = "AQ.Ab8RN6LnBF5fs5b2EkkPrmsj1uTrtcSHEY1MNXtLrtp_r1oxCg" 
MODEL_NAME = "gemma-4-31b-it"

@app.route('/', methods=['GET', 'POST'])
@app.route('/v1/chat/completions', methods=['POST'])
@app.route('/chat/completions', methods=['POST'])
def chat_completions():
    if request.method == 'GET':
        return "Proxy server is officially running 24/7!", 200
        
    data = request.json
    headers = {"Content-Type": "application/json", "x-goog-api-key": AI_STUDIO_KEY}
    
    formatted_messages = []
    for m in data.get("messages", []):
        role = "user" if m["role"] == "user" else "model"
        formatted_messages.append({"role": role, "parts": [{"text": m["content"]}]})
        
    gemini_payload = {
        "contents": formatted_messages, 
        "generationConfig": {
            "temperature": data.get("temperature", 0.7), 
            "maxOutputTokens": data.get("max_tokens", 1000)
        }
    }
    
    # PERFECTLY SEPARATED GOOGLE API ENDPOINT
    google_url = f"https://googleapis.com{MODEL_NAME}:generateContent"
    
    try:
        response = requests.post(google_url, json=gemini_payload, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": f"Google rejected request: {response.text}"}), response.status_code
        
        res_json = response.json()
        reply_text = res_json['candidates']['content']['parts']['text']
        
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": reply_text}, "finish_reason": "stop"}]
        })
    except Exception as e:
        return jsonify({"error": f"Internal proxy error parsing message: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
