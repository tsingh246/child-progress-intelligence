import base64
import json
import urllib.error
import urllib.request


def extract_text(uploaded_file, base_url, model_name, timeout_seconds=180):
    image_bytes = uploaded_file.getvalue()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """
Read this therapy report image.
Extract the visible text and organize it by sections when possible.
If AM and PM sections are both present, label them clearly.
If daily care, meals, toileting, or activity progress are present, label them clearly.
Do not invent missing text.
Return plain text only.
""".strip()

    url = base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [encoded_image],
            }
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        return f"Could not connect to Ollama vision model: {error}"
    except TimeoutError:
        return "Ollama vision OCR timed out."

    message = response_data.get("message", {})
    return message.get("content", "").strip()
