import ollama
import json
import re


def extract_document(image_path):

    prompt = """
Analyze this document image carefully.

Extract only information that is actually visible.

Return ONLY valid JSON.
Do NOT use markdown.
Do NOT use ```json or ```.

Use exactly this structure:

{
    "document_type": "string",
    "title": "string",
    "summary": "string",
    "findings": [
        {
            "item": "string",
            "finding": "string",
            "severity": "LOW | MEDIUM | HIGH",
            "recommendation": "string"
        }
    ],
    "overall_severity": "LOW | MEDIUM | HIGH",
    "recommendations": [
        "string"
    ]
}

Rules:
- Do not invent information.
- If information is missing, use "Not specified".
- Carefully read the document.
- Keep findings factual.
- Return ONLY the JSON object.
"""

    response = ollama.chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_path]
            }
        ]
    )

    raw = response["message"]["content"].strip()

    # Remove markdown code fences if the model adds them
    raw = re.sub(r"^```json\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    raw = raw.strip()

    # Check that the result is actually JSON
    try:
        json.loads(raw)
    except json.JSONDecodeError:
        print("\n========== RAW MODEL RESPONSE ==========")
        print(raw)
        print("========================================\n")
        raise

    return raw