import ollama
import json
import re
import time

VISION_CLIENT = ollama.Client(timeout=180)


def extract_document(image_path):

    prompt = """
Extract only facts visible on this inspection page. Do not infer missing
information. Return one compact JSON object with exactly these fields:
{"equipment_inspected":"","inspection_status":"","overall_condition":"",
"summary":"","key_findings":[],"abnormalities":[],"recommended_actions":[]}
Use strings for each list item. Keep each item concise but preserve details.
Only include stated abnormalities and actions. Put negative observations
such as "no abnormal noise" in key_findings, not abnormalities.
Also list explicit issues such as leakage or above-normal readings under
abnormalities, even when they already appear in key_findings.
inspection_status must describe stated operational/completion status;
never use HIGH, MEDIUM, or LOW as inspection_status.
Set inspection_status only if the document explicitly states it; do not
infer "Completed" from the presence of findings, a signature, or a date.
Leave unknown fields empty.
"""

    started = time.perf_counter()
    try:
        response = VISION_CLIENT.chat(
            model="qwen2.5vl:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_path]
                }
            ],
            options={
                "num_predict": 256,
                "temperature": 0.2,
            },
        )
    finally:
        print(
            f"[vision] {image_path}: {time.perf_counter() - started:.1f}s",
            flush=True,
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