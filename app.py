import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

SYSTEM_PROMPT = """
You are J.A.R.V.I.S., a refined personal AI assistant.
Speak naturally in Korean unless the user requests another language.
Be concise, calm, respectful and practical.
You are an AI assistant running inside a web application. Do not claim to control
devices or access private information unless the application explicitly provides that tool.
"""

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "메시지를 입력해 주세요."}), 400

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "서버에 GEMINI_API_KEY가 설정되지 않았습니다."}), 500

    try:
        client = genai.Client(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

        contents = []
        for item in history[-12:]:
            if item.get("role") in ("user", "assistant") and item.get("content"):
                role = "user" if item["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": item["content"]}]})
        contents.append({"role": "user", "parts": [{"text": message}]})

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": f"AI 연결 오류: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5050")))