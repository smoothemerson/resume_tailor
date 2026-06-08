import json
import re

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT


def _build_analysis_messages(job_description: str) -> list[dict]:
    system_prompt = (
        "Extract structured information from a job description. "
        "Return ONLY a valid JSON object with exactly these three keys: "
        "technologies (list of strings), requirements (list of strings), "
        "emphasis_areas (list of strings). No explanation, no markdown, no prose."
    )
    user_message = (
        "<job_description>\n"
        f"{job_description}\n"
        "</job_description>"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def _parse_analysis_response(content: str) -> dict | None:
    text = content.strip()
    text = re.sub(r"^```[^\n]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    required_keys = {"technologies", "requirements", "emphasis_areas"}
    if not required_keys.issubset(parsed.keys()):
        return None
    if not all(isinstance(parsed[k], list) for k in required_keys):
        return None
    return {k: parsed[k] for k in required_keys}


def analyze_job_description(job_description: str, model: str | None = None) -> dict | None:
    effective_model = model or OLLAMA_MODEL
    messages = _build_analysis_messages(job_description)
    payload = {
        "model": effective_model,
        "messages": messages,
        "stream": False,
    }
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("done_reason") == "length":
            return None
        raw = data["message"]["content"]
        return _parse_analysis_response(raw)
    except Exception:
        return None
