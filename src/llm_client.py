import re

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT
from log_manager import logger


def _check_ollama_health() -> None:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=TIMEOUT[0])
    except requests.ConnectionError as exc:
        logger.error(f"Ollama is not reachable at {OLLAMA_BASE_URL}")
        raise RuntimeError(f"Ollama is not reachable at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        logger.error("Ollama health check timed out")
        raise RuntimeError("Ollama health check timed out") from exc


def _build_messages(resume_text: str, job_description: str) -> list[dict]:
    system_prompt = (
        "You are a professional resume editor. Return only the complete LaTeX document. "
        "Do not include any explanations, markdown code fences, or prose. "
        "The response must start with \\documentclass and end with \\end{document}.\n\n"
        "You may rewrite the professional summary, skills section, and experience bullet points "
        "to better align with the provided job description. Preserve all other content exactly: "
        "education, contact information, company names, job titles, dates, and all LaTeX "
        "structural commands must remain unchanged.\n\n"
        "You may only reword existing content. Every fact, date, company, and role must come "
        "verbatim from the original resume. Do not invent, add, or imply any experience, skill, "
        "company, project, date, or credential that is not present in the original resume."
    )
    user_message = (
        f"<job_description>\n{job_description}\n</job_description>\n\n"
        f"Here is the resume to tailor:\n\n{resume_text}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```\s*\w*\s*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _validate_latex(text: str) -> str:
    if not text.lstrip().startswith("\\documentclass"):
        raise ValueError(
            "LLM response does not start with \\documentclass — output is not valid LaTeX."
        )
    if "\\end{document}" not in text:
        raise ValueError(
            "LLM response does not contain \\end{document} — output may be truncated."
        )
    return text


def generate_tailored_resume(resume_text: str, job_description: str) -> str:
    logger.info("Checking Ollama health...")
    _check_ollama_health()

    messages = _build_messages(resume_text, job_description)
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": 8192},
    }

    logger.info(f"Calling Ollama /api/chat with model {OLLAMA_MODEL}")
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.ConnectionError as exc:
        logger.error(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        logger.error(f"Ollama request timed out (timeout={TIMEOUT})")
        raise RuntimeError(f"Ollama request timed out (timeout={TIMEOUT})") from exc
    except requests.HTTPError as exc:
        logger.error(f"Ollama returned HTTP error: {exc}")
        raise RuntimeError(f"Ollama returned HTTP error: {exc}") from exc

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise RuntimeError(
            f"Ollama returned non-JSON response: {response.text[:200]}"
        ) from exc

    if data.get("done_reason") == "length":
        raise RuntimeError(
            "LLM response was truncated (done_reason=length). "
            "The resume may be too long for the model context window."
        )

    try:
        content = data["message"]["content"]
    except KeyError as exc:
        raise RuntimeError(
            f"Unexpected Ollama response structure: {data}"
        ) from exc
    content = _strip_fences(content)
    content = _validate_latex(content)

    logger.info("LLM response validated successfully.")
    return content
