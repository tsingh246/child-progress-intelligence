import json
import urllib.error
import urllib.request


def generate_summary_with_ollama(base_url, model_name, prompt, timeout_seconds=120):
    url = base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt,
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
        return {
            "ok": False,
            "summary_text": "",
            "error": f"Could not connect to Ollama: {error}",
        }
    except TimeoutError:
        return {
            "ok": False,
            "summary_text": "",
            "error": "Ollama summary generation timed out.",
        }

    message = response_data.get("message", {})
    summary_text = message.get("content", "").strip()

    if not summary_text:
        return {
            "ok": False,
            "summary_text": "",
            "error": "Ollama returned an empty summary.",
        }

    return {
        "ok": True,
        "summary_text": summary_text,
        "error": "",
    }
