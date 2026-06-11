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
    system_prompt = r"""
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

        <ALLOWED>
        You may ONLY rewrite the following elements:
        - Title line: the \ {Title}\\ line in the \begin{center} contact header
        - Employer taglines: the \textit{\small ...}\\ line below each employer header
        - Employer bullet points: the \item entries inside \begin{itemize} under each employer
        (reword only — bullet count stays fixed)
        - Project subtitle: the descriptive text after \textbf{ProjectName} on each project line
        - Project bullet points: the \item entries inside \begin{itemize} under each project
        (reword only — bullet count stays fixed)
        - Skills content: the technology lists on \noindent\textbf{Category:} lines under
        \header{Skills} only — the \noindent\textbf{...:} lines under \header{Languages}
        use the same pattern and are protected
        (reorder/reweight within categories; use only skills already present in the original)

        Everything not listed above must remain byte-for-byte identical.
        </ALLOWED>

        <CONSTRAINTS>
        MUST NOT CHANGE:
        - Candidate name: the {\Huge \scshape {Name}}\\ line inside the \begin{center} block
        - Contact block: the \begin{center}...\end{center} block at the top of the document
        (name, email, phone, location, LinkedIn, GitHub) — EXCEPT the professional title line
        (the \ {AI Engineer}\\ line), which is the only rewritable line inside this block
        - Education section: everything under \header{Education}
        - Languages section: everything under \header{Languages}
        - Employer header lines: company name, role title, location, and date range
        (pattern: \textbf{EMPLOYER}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES\\)
        - Project anchors: the \href{url}{\textbf{ProjectName}} and \hfill date on each project line
        - Section headers: all \header{...} commands
        - All LaTeX commands and environments: \documentclass, \usepackage, \newcommand definitions,
        \begin, \end, \vspace, \hfill, \textbf, \textit, \href, and all other structural commands —
        the commands themselves never change; only text content inside the elements listed in
        <ALLOWED> may be reworded
        - Bullet point count: do not add or remove \item entries in any list

        TECHNOLOGY FIDELITY:
        Do not substitute one named technology for another. If a technology appears in the original
        resume, it must appear in the output. If a technology is absent from the original resume,
        it must not appear in the output — even if it appears in the job description.
        (Example: if the resume mentions Azure, Azure must remain; if the resume does not mention
        AWS, AWS must not be added.)
        </CONSTRAINTS>

        <OUTPUT_FORMAT>
        Return:
        ✅ A single, complete, compilable LaTeX document.
        ✅ Rewritten content limited to the six elements listed in <ALLOWED>.
        ✅ All LaTeX commands, environments, and structure intact.

        Do NOT return:
        ❌ Any text before \documentclass or after \end{document}.
        ❌ Markdown code fences (```latex or ```).
        ❌ Explanations, annotations, or comments of any kind — including LaTeX % comment lines.
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
        techs = analysis.get("technologies", [])
        reqs = analysis.get("requirements", [])
        areas = analysis.get("emphasis_areas", [])
        analysis_block = (
            "<jd_analysis>\n"
            f"technologies: {techs}\n"
            f"requirements: {reqs}\n"
            f"emphasis_areas: {areas}\n"
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
