# Phase 2: LLM Integration - Research

**Researched:** 2026-05-28
**Domain:** Ollama REST API, requests exception handling, Python string processing for LLM output safety
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Rewrite scope is **summary + skills + experience bullets only**. Education, contact info, company names, dates, and all structural LaTeX commands are preserved exactly.
- **D-02:** No-hallucination guardrail uses **both** a preservation rule AND an explicit prohibition: "You may only reword existing content. Every fact, date, company, and role must come verbatim from the original resume. Do not invent, add, or imply any experience, skill, company, project, date, or credential that is not present in the original resume."
- **D-03:** LaTeX-only output enforcement uses **explicit instruction with the structural anchor**: "Return only the complete LaTeX document. Do not include any explanations, markdown code fences, or prose. The response must start with `\documentclass` and end with `\end{document}`."
- **D-04:** System prompt is **generic** — no mention of AI engineering domain or resume owner. Works for any professional resume.
- **D-05:** Function signature: `generate_tailored_resume(resume_text: str, job_description: str) -> str`. Takes two string inputs; model and URL read from `config.py` constants inside the function.
- **D-06:** Returns the **validated LaTeX string only** — no file writing. Phase 3 / `main.py` calls `write_resume()` from `resume_writer.py` with the returned string.
- **D-07:** Health check (`GET /api/tags`) runs **inside `generate_tailored_resume()`** as the first step, before prompt building or API call. Phase 3 calls only one function — the caller cannot forget to check.
- **D-08:** `llm_client.py` uses `from log_manager import logger` for consistency with `resume_reader.py`.

### Claude's Discretion
- Internal module structure (one function vs. private helpers like `_build_messages()`, `_strip_fences()`, `_validate_latex()`) — researcher/planner may break these out for clarity
- Exact wording and ordering of system prompt sentences beyond the locked behavioral rules
- Exception types for each failure mode (e.g., `RuntimeError`, `ValueError`, `ConnectionError`) — must be raiseable (not sys.exit) per the accumulated context decision "exception catches at main.py boundary only"

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-04 | Call Ollama `/api/chat` (non-streaming) with `num_ctx: 8192`, `timeout=(10, 300)`, and role-separated system/user messages | Ollama API schema verified; timeout tuple behavior verified via requests docs |
| QUAL-01 | LLM response unconditionally stripped of markdown code fences before any further processing | String strip pattern documented; unconditional approach specified |
| QUAL-02 | Output validated in memory for `\documentclass` presence and `\end{document}` termination before writing to disk | String `in` operator pattern documented; ValidationError exception type recommended |
| QUAL-03 | `done_reason` field checked; if `"length"`, abort with clear error message (do not write truncated output) | Ollama response schema verified; `done_reason` field confirmed present in non-streaming response |
| QUAL-04 | Job description wrapped in `<job_description>...</job_description>` XML delimiters in the prompt | Pattern documented; prevents LaTeX special characters from corrupting prompt context |
| ERR-02 | If Ollama connection fails or times out, tool prints human-readable error to stderr and exits with code 1 | `requests.ConnectionError`, `requests.Timeout` exception hierarchy verified |
| ERR-03 | Ollama health check at startup (`GET /api/tags`); fail fast with clear message if Ollama not reachable | `/api/tags` endpoint verified; response structure confirmed |
</phase_requirements>

---

## Summary

Phase 2 produces a single module, `src/llm_client.py`, containing the `generate_tailored_resume(resume_text, job_description)` function. The function executes a fixed sequence: health check, prompt construction, Ollama API call, output sanitization, LaTeX validation, then returns the validated string. No file I/O happens in this module — that is Phase 3's responsibility.

All locked decisions from CONTEXT.md constrain the implementation precisely. The Ollama `/api/chat` endpoint with `stream: false` is verified as the correct call shape. The `requests` library's exception hierarchy (`ConnectionError`, `Timeout`) maps cleanly to the two error modes the function must handle. Python's `str` methods are sufficient for fence stripping and LaTeX boundary validation — no third-party parsing library is needed.

The module has no new package dependencies: `requests` (already declared) and Python stdlib (`re` or plain string methods) are sufficient for every operation in scope.

**Primary recommendation:** Implement `llm_client.py` as a single public function with three private helpers (`_build_messages`, `_strip_fences`, `_validate_latex`) for testability. Raise specific exception types at each failure point so `main.py` can catch and handle them cleanly.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ollama health check | llm_client.py | config.py (URL constant) | Health check is part of the LLM call contract; must run before prompt construction |
| Prompt construction | llm_client.py | — | Builds system + user message list from inputs; purely in-memory string construction |
| Ollama API call | llm_client.py | config.py (MODEL, URL, TIMEOUT) | Single POST request; all config injected from constants, not hardcoded |
| Output sanitization | llm_client.py | — | Fence stripping is an LLM output safety concern, not a file I/O concern |
| LaTeX validation | llm_client.py | — | Validation must happen before caller can write; belongs in the same module as the API call |
| File writing | resume_writer.py (Phase 3) | — | Explicitly out of scope for Phase 2 per D-06 |
| Exception boundary | main.py (Phase 3) | — | Per accumulated context: individual modules raise, main.py catches and exits |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `requests` | already installed (project dep) | POST to `/api/chat`, GET to `/api/tags` | Project constraint; already in pyproject.toml |
| `re` (stdlib) | stdlib | Fence stripping via regex; optional if plain string slicing used | Zero deps; unconditional strip pattern works cleanly with regex |
| `json` (stdlib) | stdlib | Serialize request body, parse response | Ollama speaks JSON; already used pattern |

### No New Packages Required

This phase adds **zero new dependencies**. All required functionality is covered by `requests` (already declared) and Python stdlib (`re`, `json`). The `slopcheck` audit is therefore N/A — no new packages to vet.

---

## Package Legitimacy Audit

**No new packages are installed in this phase.** Phase 2 uses only:
- `requests` — already declared in `pyproject.toml` [VERIFIED: existing project dependency]
- Python stdlib modules (`re`, `json`) — [VERIFIED: Python 3.11 stdlib]

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
generate_tailored_resume(resume_text, job_description)
          |
          v
  [1] _health_check()
      GET /api/tags -> OLLAMA_BASE_URL
      ConnectionError / Timeout
          |
          v (healthy)
  [2] _build_messages(resume_text, job_description)
      system message: LaTeX guardrail + rewrite scope + no-hallucination
      user message: <job_description>...</job_description> + resume_text
          |
          v
  [3] requests.post(
        OLLAMA_BASE_URL + "/api/chat",
        json={model, messages, stream: false, options: {num_ctx: 8192}},
        timeout=TIMEOUT
      )
      ConnectionError / Timeout / HTTPError
          |
          v (200 OK)
  [4] check done_reason == "length" -> raise RuntimeError (QUAL-03)
          |
          v
  [5] _strip_fences(response_text)   <- unconditional (QUAL-01)
          |
          v
  [6] _validate_latex(stripped_text) <- \documentclass + \end{document} (QUAL-02)
      missing markers -> raise ValueError
          |
          v
      return validated_latex_str
```

### Recommended Project Structure

No structural changes to `src/`. New file: `src/llm_client.py`. Flat layout per existing pattern.

```
src/
├── config.py          # OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT — imported by llm_client.py
├── log_manager.py     # logger — imported by llm_client.py (D-08)
├── llm_client.py      # NEW — generate_tailored_resume() + private helpers
├── resume_reader.py   # Phase 1 — unchanged
├── resume_writer.py   # Phase 1 — unchanged
└── cli.py             # Phase 1 stub — unchanged
```

### Pattern 1: Ollama Health Check via GET /api/tags

**What:** Before any prompt construction, issue a lightweight GET to `/api/tags`. If Ollama is down, this raises `requests.ConnectionError` immediately — before the user waits 300 seconds for a timeout. [CITED: https://github.com/ollama/ollama/blob/main/docs/api.md]

**When to use:** Always — runs as the first statement inside `generate_tailored_resume()` per D-07.

**Example:**
```python
# Source: Ollama API docs /api/tags + requests docs
def _check_ollama_health() -> None:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=TIMEOUT[0])
    except requests.ConnectionError as exc:
        raise RuntimeError("Ollama is not reachable at " + OLLAMA_BASE_URL) from exc
    except requests.Timeout as exc:
        raise RuntimeError("Ollama health check timed out") from exc
```

Note: health check uses only the connect timeout (`TIMEOUT[0]` = 10 s), not the read timeout, since `/api/tags` responds instantly when Ollama is up. [ASSUMED — `TIMEOUT[0]` for health check is a reasonable convention; using full `TIMEOUT` also works and is simpler]

### Pattern 2: /api/chat Non-Streaming Request Body

**What:** POST to `/api/chat` with `stream: false`. The response is a single JSON object, not a stream. `message.content` holds the raw LLM output. [VERIFIED: https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md]

**When to use:** Whenever a complete response is needed before processing. This project requires validation before writing, so streaming is wrong for Phase 2.

**Request body shape (verified):**
```python
# Source: Ollama API docs https://github.com/ollama/ollama/blob/main/docs/api.md
payload = {
    "model": OLLAMA_MODEL,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
    "stream": False,
    "options": {"num_ctx": 8192},
}
response = requests.post(
    f"{OLLAMA_BASE_URL}/api/chat",
    json=payload,
    timeout=TIMEOUT,
)
```

**Response field access (verified):**
```python
data = response.json()
done_reason = data.get("done_reason")   # "stop", "length", "load", "unload"
content = data["message"]["content"]    # the raw LLM output string
```

### Pattern 3: done_reason Check (QUAL-03)

**What:** If `done_reason == "length"`, the model ran out of context window and the LaTeX document is truncated. A truncated `.tex` file will not compile. Abort before validation. [VERIFIED: Ollama API docs confirm `done_reason` values include `"length"`]

**Order matters:** Check `done_reason` BEFORE fence stripping and LaTeX validation. A truncated response may accidentally pass a partial `\documentclass` check.

```python
if data.get("done_reason") == "length":
    raise RuntimeError(
        "LLM response was truncated (done_reason=length). "
        "The resume is too long for the model context window. "
        "Try a model with a larger context or shorten the resume."
    )
```

### Pattern 4: Unconditional Fence Stripping (QUAL-01)

**What:** Strip markdown code fences regardless of whether they are present. Do not conditionally check. [ASSUMED — exact regex; unconditional requirement is locked in QUAL-01]

**Why unconditional:** A conditional strip introduces a code path where fences are detected but not stripped, which is wrong. Stripping an already-clean string is a no-op.

```python
import re

def _strip_fences(text: str) -> str:
    # Matches ```latex ... ``` or ``` ... ``` with optional language identifier
    return re.sub(r"^```[a-z]*\n?", "", re.sub(r"\n?```$", "", text.strip()))
```

Alternative (simpler, handles multi-line correctly):
```python
def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("\n", 1)[0] if "\n" in text else text[:-3]
    return text.strip()
```

The planner should choose the approach that handles multi-line fences most robustly. The `re.sub` approach with a pattern matching the opening fence line and closing fence line is more reliable for varying fence formats (`\`\`\`latex`, `\`\`\`tex`, `\`\`\``).

### Pattern 5: LaTeX Boundary Validation (QUAL-02)

**What:** Check that the stripped response contains both required LaTeX structural markers. If either is missing, the document is corrupt or incomplete. [ASSUMED — exact validation uses Python `in` operator; this is the simplest and most reliable approach for this use case]

```python
def _validate_latex(text: str) -> str:
    if "\\documentclass" not in text:
        raise ValueError(
            "LLM response does not contain \\documentclass — output is not valid LaTeX."
        )
    if "\\end{document}" not in text:
        raise ValueError(
            "LLM response does not contain \\end{document} — output may be truncated."
        )
    return text
```

### Pattern 6: requests Exception Hierarchy (ERR-02)

**What:** `requests.ConnectionError` is raised when Ollama is not running (connection refused). `requests.Timeout` is raised when the connect or read timeout is exceeded. Both must be caught. [VERIFIED: https://docs.python-requests.org/en/latest/api/]

```python
# Source: requests docs Developer Interface
except requests.ConnectionError as exc:
    raise RuntimeError("Cannot connect to Ollama at " + OLLAMA_BASE_URL) from exc
except requests.Timeout as exc:
    raise RuntimeError("Ollama request timed out (timeout=" + str(TIMEOUT) + ")") from exc
```

`requests.Timeout` catches both `ConnectTimeout` and `ReadTimeout` — catching the parent class is correct here since the user message for both is the same ("took too long").

### Pattern 7: System Prompt Structure (D-01 through D-04)

The system prompt must encode all four locked decisions. Recommended ordering for maximum LLM compliance: (1) role + output format enforcement, (2) rewrite scope, (3) no-hallucination rule, (4) structural anchor.

```
You are a professional resume editor. Return only the complete LaTeX document.
Do not include any explanations, markdown code fences, or prose.
The response must start with \documentclass and end with \end{document}.

You may rewrite the professional summary, skills section, and experience bullet points
to better align with the provided job description. Preserve all other content exactly:
education, contact information, company names, job titles, dates, and all LaTeX
structural commands must remain unchanged.

You may only reword existing content. Every fact, date, company, and role must come
verbatim from the original resume. Do not invent, add, or imply any experience, skill,
company, project, date, or credential that is not present in the original resume.
```

[ASSUMED — exact wording; planner/implementer may adjust within the D-01/D-02/D-03/D-04 constraints]

### Pattern 8: User Message Structure (QUAL-04)

The user message wraps the job description in XML delimiters to prevent LaTeX special characters (`$`, `%`, `&`, `_`, `#`, `^`) from being parsed as LaTeX by the model, and then appends the full resume text.

```python
user_message = (
    f"<job_description>\n{job_description}\n</job_description>\n\n"
    f"Here is the resume to tailor:\n\n{resume_text}"
)
```

[ASSUMED — exact delimiter format; `<job_description>` XML tags are locked by QUAL-04, the resume concatenation format is at implementer discretion]

### Pattern 9: Import and Logging Pattern (D-08)

Follows the established pattern from `resume_reader.py`:

```python
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT
from log_manager import logger

# Usage:
logger.info("Checking Ollama health...")
logger.info("Calling Ollama /api/chat with model " + OLLAMA_MODEL)
logger.error("Ollama not reachable: " + str(exc))
```

### Anti-Patterns to Avoid

- **`sys.exit()` inside `llm_client.py`:** `resume_reader.py` uses `sys.exit` but the accumulated context decision overrides this for `llm_client.py`. Raise exceptions; let `main.py` call `sys.exit`.
- **Checking for fences before stripping:** Conditional fence detection defeats the unconditional guarantee required by QUAL-01. Always strip unconditionally.
- **Validating before done_reason check:** A truncated response can still contain `\documentclass` if truncation happened mid-document. The `done_reason` check must come first.
- **Hardcoding model, URL, or timeout:** All three come from `config.py` imports. No string literals for these values in `llm_client.py`.
- **Parsing the response with anything other than `.json()`:** `response.json()` from `requests` is stdlib JSON under the hood and is the correct access pattern.
- **Accessing `response.json()` before checking HTTP status:** Call `response.raise_for_status()` before `.json()` to catch non-200 responses (e.g., 404 if model not found) as `requests.HTTPError`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP client for Ollama | Custom socket/urllib code | `requests.post` | Already a dep; handles encoding, JSON serialization, timeout, redirects |
| JSON serialization of request body | Manual string building | `json=payload` kwarg in `requests.post` | Automatic; handles escaping, encoding |
| Timeout enforcement | Thread-based wrappers | `timeout=TIMEOUT` in `requests.post` | Native requests feature; tuple syntax is (connect, read) |
| Markdown fence stripping | HTML parser, markdown lib | stdlib `re` or plain string slice | Fences are simple delimiters; no parser needed |
| LaTeX structural validation | Full LaTeX parser | Python `in` operator | Only two fixed sentinel strings needed; a parser is overkill |

**Key insight:** Every operation in this module — HTTP call, JSON parsing, string cleaning, boundary validation — is handled by `requests` or Python stdlib. Adding any library would be pure overhead for no functional gain.

---

## Common Pitfalls

### Pitfall 1: Streaming Response Mistakenly Parsed as JSON
**What goes wrong:** If `stream` is omitted from the request body (default is `true` in Ollama), the response is a sequence of newline-delimited JSON objects, not a single object. `response.json()` will succeed on the first line only, or raise an error.
**Why it happens:** `stream: false` must be explicitly set — it is not the default.
**How to avoid:** Always include `"stream": False` in the payload dict.
**Warning signs:** `response.text` contains multiple lines each starting with `{"model":`.

### Pitfall 2: done_reason Check After Fence Strip / Validation
**What goes wrong:** A truncated response that ends mid-document may contain `\documentclass` but lack `\end{document}`. The validation at QUAL-02 would then raise the wrong error ("missing `\end{document}`") instead of the correct truncation error.
**Why it happens:** Wrong operation ordering.
**How to avoid:** `done_reason` check → fence strip → `\documentclass` check → `\end{document}` check. This exact order is specified in the Additional Context section.

### Pitfall 3: ConnectionError vs. Timeout Confusion
**What goes wrong:** Catching only `requests.ConnectionError` misses timeout failures. Catching only `requests.Timeout` misses refused-connection failures.
**Why it happens:** They look similar but are in different branches of the exception hierarchy.
**How to avoid:** Catch both. `requests.ConnectionError` for service-down; `requests.Timeout` for service-up-but-slow. Both re-raise as `RuntimeError` with user-readable messages.

### Pitfall 4: Fence Stripping with Only ``` Not Matched
**What goes wrong:** Some models return `\`\`\`latex\n...\`\`\`` or `\`\`\`tex\n...\`\`\`` — the language identifier after the backticks varies. A strip pattern that only matches bare `\`\`\`` misses these.
**Why it happens:** LLMs add language hints to fences inconsistently.
**How to avoid:** Use a pattern that matches `` ``` `` optionally followed by any word characters (e.g., `re.sub(r"^```\w*\n?", "", text)`).

### Pitfall 5: Health Check Using Full TIMEOUT Tuple
**What goes wrong:** Using `timeout=TIMEOUT` (= `(10, 300)`) for the health check means the read phase can wait 300 seconds. `/api/tags` responds instantly when Ollama is healthy. If there is a network oddity that accepts the connection but stalls the response, the health check would hang.
**Why it happens:** Reusing the API call timeout for the health check without considering the different response profile.
**How to avoid:** Use `timeout=TIMEOUT[0]` (= 10 s) for the health check, or use `timeout=10` explicitly. The health check only needs the connect timeout; the read should be fast.
**Warning signs:** Health check takes unexpectedly long before raising a timeout error.

### Pitfall 6: raise_for_status() Not Called
**What goes wrong:** If Ollama returns 404 (model not found) or 500, `requests.post` does not raise by default. `response.json()["message"]["content"]` may not exist, leading to a confusing `KeyError`.
**Why it happens:** `requests` does not raise on non-2xx by default.
**How to avoid:** Call `response.raise_for_status()` immediately after the POST before accessing response fields. This raises `requests.HTTPError` with the status code, which can be caught alongside `ConnectionError` and `Timeout`.

---

## Code Examples

### Full llm_client.py Skeleton

```python
# Source: Pattern synthesized from Ollama API docs + requests docs + CONTEXT.md decisions
import re

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT
from log_manager import logger


def _check_ollama_health() -> None:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=TIMEOUT[0])
    except requests.ConnectionError as exc:
        raise RuntimeError(f"Ollama is not reachable at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
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
    text = re.sub(r"^```\w*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _validate_latex(text: str) -> str:
    if "\\documentclass" not in text:
        raise ValueError("LLM response does not contain \\documentclass — output is not valid LaTeX.")
    if "\\end{document}" not in text:
        raise ValueError("LLM response does not contain \\end{document} — output may be truncated.")
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
        raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        raise RuntimeError(f"Ollama request timed out (timeout={TIMEOUT})") from exc
    except requests.HTTPError as exc:
        raise RuntimeError(f"Ollama returned HTTP error: {exc}") from exc

    data = response.json()

    if data.get("done_reason") == "length":
        raise RuntimeError(
            "LLM response was truncated (done_reason=length). "
            "The resume may be too long for the model context window."
        )

    content = data["message"]["content"]
    content = _strip_fences(content)
    content = _validate_latex(content)

    logger.info("LLM response validated successfully.")
    return content
```

[ASSUMED — exact system prompt wording and exact exception messages; functional structure is correct per all locked decisions]

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `/api/generate` with single prompt string | `/api/chat` with system/user roles | Ollama v0.1.x → v0.1.14+ | Cleaner prompt hygiene; system message separate from user content |
| `stream: true` (Ollama default) | `stream: false` for single-shot response | Always available | Simpler response handling; single JSON object instead of NDJSON stream |

**Deprecated/outdated:**
- `/api/generate`: Still functional in Ollama but conflates system and prompt into one string. D-03 in CONTEXT.md explicitly chooses `/api/chat` for the role separation. [CITED: https://github.com/ollama/ollama/blob/main/docs/api.md]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `TIMEOUT[0]` (= 10 s) used for health check only; full `TIMEOUT` for API call | Pattern 1, Pitfall 5 | If health check uses full tuple and Ollama stalls on tags response, startup delay of up to 300 s before failing — acceptable fallback, just slower |
| A2 | System prompt wording beyond locked D-01/D-02/D-03/D-04 sentences | Pattern 7, Code Example | LLM may not comply if wording is unclear; planner can iterate on wording in implementation |
| A3 | `_strip_fences` regex pattern `^```\w*\n?` covers all common fence formats | Pattern 4 | If model returns unusual fence (e.g., `` ` `` with spaces), strip may miss; acceptable failure mode — document passes to validation which will catch missing `\documentclass` |
| A4 | `raise_for_status()` is the correct guard for non-2xx responses | Pattern 6 | If not called, a 404 (model not found) produces a confusing `KeyError` — this is a correctness issue, not just style |
| A5 | Exact error messages to end user | Code examples throughout | User-facing messages are discretionary; planner may refine wording |

---

## Open Questions

1. **Health check timeout granularity**
   - What we know: `TIMEOUT = (10, 300)` is defined in config.py; `TIMEOUT[0]` = 10 s
   - What's unclear: Whether to use `TIMEOUT[0]` or the full `TIMEOUT` tuple for the health check GET
   - Recommendation: Use `TIMEOUT[0]` (connect-only timeout, 10 s) for `/api/tags`. Ollama responds to tags instantly when running; a 300 s read timeout on a health check provides no benefit and could mask a stalled connection.

2. **Exception type for validation failures**
   - What we know: CONTEXT.md leaves exception types to Claude's discretion
   - What's unclear: Whether `ValueError` (semantic mismatch) or `RuntimeError` (operational failure) better represents a bad LLM response
   - Recommendation: Use `ValueError` for validation failures (QUAL-02 — malformed output from LLM) and `RuntimeError` for operational failures (connection down, truncation, HTTP error). This distinction helps `main.py` catch them separately if needed in Phase 3.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Runtime | Yes | 3.11.2 | — |
| `requests` library | HTTP calls to Ollama | Declared in pyproject.toml; not installed in dev env shell | — | Install via `uv sync` |
| Ollama service at localhost:11434 | All LLM calls | Not running in this environment (curl exit 7 = connection refused) | — | Ollama must be running before tool execution; tool fails fast via health check |

**Missing dependencies with no fallback:**
- Ollama must be running before `generate_tailored_resume()` is called. The health check (ERR-03) handles this gracefully — the tool will fail fast with a clear message. This is expected runtime behavior, not a blocker for implementation.

**Missing dependencies with fallback:**
- `requests` not installed in shell — install via `uv sync` in the project virtualenv before running.

---

## Validation Architecture

> Skipped — `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json`.

---

## Security Domain

This phase makes no network calls to external services — all HTTP calls go to `http://localhost:11434` (Ollama, local only). No authentication, no TLS, no user data leaves the machine. ASVS categories V2/V3/V4/V6 do not apply.

**V5 Input Validation:** The job description input is passed to the LLM via the prompt, not executed or stored. The XML delimiter wrapping (QUAL-04) is the only sanitization needed — it prevents LaTeX special characters from corrupting the LaTeX generation context in the model's attention.

No additional security controls are required for a localhost-only CLI tool.

---

## Sources

### Primary (HIGH confidence)
- Ollama REST API docs: https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md — `/api/chat` request schema, response schema, `done_reason` values, `/api/tags` endpoint, `stream: false` behavior, `num_ctx` option field. [CITED]
- requests Developer Interface: https://docs.python-requests.org/en/latest/api/ — exception hierarchy (`ConnectionError`, `Timeout`, `ConnectTimeout`, `ReadTimeout`, `HTTPError`), timeout tuple behavior, `raise_for_status()`. [CITED]
- `src/config.py` (verified directly) — `TIMEOUT = (10, 300)`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` constants. [VERIFIED: codebase]
- `src/log_manager.py` (verified directly) — `CustomLogger` class, `logger` module-level instance, import pattern. [VERIFIED: codebase]
- `src/resume_reader.py` (verified directly) — import pattern, module structure. [VERIFIED: codebase]

### Secondary (MEDIUM confidence)
- requests timeout behavior: https://oxylabs.io/blog/python-requests-timeout — confirmed tuple timeout pattern and exception type distinction. [CITED, corroborates requests docs]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; requests and stdlib already confirmed
- Architecture: HIGH — Ollama API schema verified from official docs; all decisions locked in CONTEXT.md
- Pitfalls: HIGH — derived from verified API behavior (stream default, done_reason values, exception hierarchy) and locked implementation decisions
- System prompt content: MEDIUM — behavioral rules are locked (D-01 through D-04); exact wording is assumed/discretionary

**Research date:** 2026-05-28
**Valid until:** 2026-08-28 (Ollama REST API is stable; requests exception hierarchy does not change between minor versions)
