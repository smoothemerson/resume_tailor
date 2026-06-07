import re
from typing import NamedTuple

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT


class TailorResult(NamedTuple):
    content: str
    fences_stripped: bool


def _check_ollama_health() -> None:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=TIMEOUT[0])
        response.raise_for_status()
    except requests.ConnectionError as exc:
        raise RuntimeError(f"Ollama is not reachable at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        raise RuntimeError("Ollama health check timed out") from exc
    except requests.HTTPError as exc:
        raise RuntimeError(f"Ollama health check failed with HTTP error: {exc}") from exc


def _build_messages(resume_text: str, job_description: str, analysis: dict | None = None) -> list[dict]:
    system_prompt = """
        <PERSONA>
        You are Alexandra, a senior technical recruiter and resume strategist with 10+ years of
        experience placing software engineers and AI/ML professionals at top-tier tech companies.
        You have deep knowledge of ATS (Applicant Tracking Systems) and understand precisely
        which keywords, phrasing patterns, and structural signals hiring managers look for.
        Your rewrites are surgical, honest, and grounded strictly in the candidate's real experience.
        </PERSONA>

        <TASK>
        Your task is to tailor the candidate's LaTeX resume to a specific job description.
        You will rewrite selected sections to maximize relevance and ATS alignment, without
        fabricating, embellishing, or implying any experience that does not already exist in the
        original resume.

        Return ONLY the complete, compilable LaTeX document. No explanations, no markdown fences,
        no prose outside the document. The response must start with \documentclass and end with
        \end{document}.
        </TASK>

        <CONTEXT>
        The candidate's LaTeX resume and the target job description are provided below.
        The resume is the single source of truth. The job description is the optimization target.
        </CONTEXT>

        <INSTRUCTIONS>
        1. Rewrite the professional summary to open with the most relevant role alignment and
        mirror the seniority/domain language used in the job description.
        2. Rewrite the skills section to surface keywords and technologies that appear in the
        job description, but only include skills already present (explicitly or implicitly)
        in the original resume.
        3. Rewrite experience bullet points to emphasize outcomes, metrics, and responsibilities
        that are most relevant to the job description. Prioritize action verbs and quantified
        impact where they already exist in the original.
        4. Preserve the order and relative weight of bullet points, do not reorder jobs or
        add/remove bullet points, only reword them.
        5. Scan the job description for ATS-critical keywords (e.g. specific tools, frameworks,
        methodologies, certifications). Where those keywords map to existing content in the
        resume, integrate them naturally into the rewritten sections.
        6. Do not alter any LaTeX structural commands, environments, formatting macros, or
        custom commands. Preserve whitespace and line breaks in non-content areas.
        </INSTRUCTIONS>

        <CONSTRAINTS>
        - You may ONLY reword existing content. Every fact, date, company, title, and project
        must come verbatim from the original resume.
        - Do NOT invent, add, imply, or upgrade any experience, skill, tool, certification,
        company, project, or credential not present in the original.
        - Do NOT alter: education section, contact information, company names, job titles,
        employment dates, project names, or any LaTeX structural commands.
        - Do NOT change the number of bullet points in any experience entry.
        - Do NOT convert passive phrasing to active if the underlying claim would be inflated.
        - Limit rewriting to: professional summary, skills section, and experience bullet points.
        Everything else must remain byte-for-byte identical.
        </CONSTRAINTS>

        <OUTPUT_FORMAT>
        Return:
        ✅ A single, complete, compilable LaTeX document.
        ✅ Rewritten sections: professional summary, skills, and experience bullets only.
        ✅ All LaTeX commands, environments, and structure intact.

        Do NOT return:
        ❌ Any text before \documentclass or after \end{document}.
        ❌ Markdown code fences (```latex or ```).
        ❌ Explanations, comments, or annotations outside LaTeX comment syntax (%).
        ❌ Any new facts, credentials, or experiences not in the original resume.
        </OUTPUT_FORMAT>
    """.strip()

    user_message = (
        "<job_description>\n"
        f"{job_description}\n"
        "</job_description>\n\n"
        "<resume>\n"
        f"{resume_text}\n"
        "</resume>"
    )
    if analysis is not None:
        analysis_block = (
            "<jd_analysis>\n"
            f"technologies: {analysis['technologies']}\n"
            f"requirements: {analysis['requirements']}\n"
            f"emphasis_areas: {analysis['emphasis_areas']}\n"
            "</jd_analysis>\n\n"
        )
        user_message = analysis_block + user_message

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[^\n]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _validate_latex(text: str) -> str:
    stripped = text.rstrip()
    if not stripped.lstrip().startswith("\\documentclass"):
        raise ValueError(
            "LLM response does not start with \\documentclass — output is not valid LaTeX."
        )
    if not stripped.endswith("\\end{document}"):
        raise ValueError(
            "LLM response does not end with \\end{document} — output may be truncated or contain trailing prose."
        )
    return text


def generate_tailored_resume(
    resume_text: str, job_description: str, model: str | None = None, analysis: dict | None = None
) -> TailorResult:
    effective_model = model or OLLAMA_MODEL
    _check_ollama_health()

    messages = _build_messages(resume_text, job_description, analysis)
    payload = {
        "model": effective_model,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": 8192},
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.ConnectionError as exc:
        raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        raise RuntimeError(f"Ollama request timed out (timeout={TIMEOUT})") from exc
    except requests.HTTPError as exc:
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
        raw = data["message"]["content"]
    except KeyError as exc:
        raise RuntimeError(f"Unexpected Ollama response structure: {data}") from exc
    fences_stripped = raw.strip() != _strip_fences(raw)
    content = _strip_fences(raw)
    _validate_latex(content)
    return TailorResult(content=content, fences_stripped=fences_stripped)
