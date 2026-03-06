from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from PIL import Image
import io
import json
import re


app = Flask(__name__)

# 🔑 Replace with your API Key
genai.configure(api_key="")

model = genai.GenerativeModel("gemini-2.5-flash")

PROMPT = """
Extract structured JSON from this receipt.

Return ONLY valid JSON in this format:
{
  "vendor": string,
  "date": "YYYY-MM-DD",
  "items": [{"name": string, "quantity": number, "price": number}],
  "subtotal": number,
  "tax": number,
  "total": number,
  "confidence": number (0 to 1)
}

Rules:
- If value missing → null
- Ensure numbers are numeric
- Confidence should reflect extraction reliability
- Do NOT return anything except JSON
"""

@app.route("/")
def index():
    return render_template("index.html")

import json
import re

@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    image = Image.open(file.stream)

    response = model.generate_content([PROMPT, image])
    raw_text = response.text.strip()

    try:
        # 🧼 Remove markdown ```json ``` if present
        cleaned = re.sub(r"```json|```", "", raw_text).strip()

        parsed_json = json.loads(cleaned)

        return jsonify({
            "success": True,
            "data": parsed_json,
            "confidence": parsed_json.get("confidence", None)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to parse JSON",
            "raw_output": raw_text
        }), 500

if __name__ == "__main__":
    app.run(debug=True)