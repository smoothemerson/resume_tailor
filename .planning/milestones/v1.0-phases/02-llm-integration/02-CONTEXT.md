# Phase 2: LLM Integration - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

`llm_client.py` — a single module that: (1) runs an Ollama health check before any API call, (2) builds a structured `/api/chat` prompt from the resume text and job description, (3) calls Ollama with the locked parameters, (4) applies all output safety guards (fence stripping, LaTeX validation, done_reason check), and (5) returns the validated LaTeX string. File writing is NOT this module's responsibility.

</domain>

<decisions>
## Implementation Decisions

### System Prompt Content
- **D-01:** Rewrite scope is **summary + skills + experience bullets only**. Education, contact info, company names, dates, and all structural LaTeX commands are preserved exactly.
- **D-02:** No-hallucination guardrail uses **both** a preservation rule AND an explicit prohibition: "You may only reword existing content. Every fact, date, company, and role must come verbatim from the original resume. Do not invent, add, or imply any experience, skill, company, project, date, or credential that is not present in the original resume."
- **D-03:** LaTeX-only output enforcement uses **explicit instruction with the structural anchor**: "Return only the complete LaTeX document. Do not include any explanations, markdown code fences, or prose. The response must start with `\documentclass` and end with `\end{document}`."
- **D-04:** System prompt is **generic** — no mention of AI engineering domain or resume owner. Works for any professional resume.

### generate_tailored_resume() Contract
- **D-05:** Function signature: `generate_tailored_resume(resume_text: str, job_description: str) -> str`. Takes two string inputs; model and URL read from `config.py` constants inside the function.
- **D-06:** Returns the **validated LaTeX string only** — no file writing. Phase 3 / `main.py` calls `write_resume()` from `resume_writer.py` with the returned string.

### Health Check Wiring
- **D-07:** Health check (`GET /api/tags`) runs **inside `generate_tailored_resume()`** as the first step, before prompt building or API call. Phase 3 calls only one function — the caller cannot forget to check.

### Logging
- **D-08:** `llm_client.py` uses `from log_manager import logger` for consistency with `resume_reader.py`. `log_manager.py` is a real part of the codebase and will be committed. Note: this supersedes the CLAUDE.md "no logging module" guideline — actual code pattern wins.

### Claude's Discretion
- Internal module structure (one function vs. private helpers like `_build_messages()`, `_strip_fences()`, `_validate_latex()`) — researcher/planner may break these out for clarity
- Exact wording and ordering of system prompt sentences beyond the locked behavioral rules
- Exception types for each failure mode (e.g., `RuntimeError`, `ValueError`, `ConnectionError`) — must be raiseable (not sys.exit) per the accumulated context decision "exception catches at main.py boundary only"

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Scope
- `.planning/REQUIREMENTS.md` — Phase 2 requirements: CORE-04, QUAL-01, QUAL-02, QUAL-03, QUAL-04, ERR-02, ERR-03; traceability table maps each requirement to this phase
- `.planning/PROJECT.md` — constraints (stdlib + requests only), key decisions table, out-of-scope list

### Roadmap & Success Criteria
- `.planning/ROADMAP.md` §"Phase 2: LLM Integration" — goal statement and 5 success criteria that must all be TRUE before phase is complete

### Existing Source Files
- `src/config.py` — OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT constants; llm_client.py reads these directly
- `src/resume_writer.py` — write_resume(content, output_dir) API; Phase 3 will call this with the string returned by generate_tailored_resume()
- `src/resume_reader.py` — pattern reference for log_manager usage and module structure
- `src/log_manager.py` — CustomLogger wrapper; import as `from log_manager import logger`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/config.py`: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `TIMEOUT` — read directly by `llm_client.py`; no function call needed, just import
- `src/resume_writer.py`: `write_resume(content: str, output_dir: Path) -> Path` — called by Phase 3, not Phase 2
- `src/log_manager.py`: `logger` (CustomLogger) — import and use for info/error/warning logging

### Established Patterns
- `resume_reader.py` raises no exceptions itself (uses `sys.exit(1)` directly) — but the accumulated context decision overrides this: `llm_client.py` must raise exceptions, not exit, to keep it testable in isolation
- All config constants at module level in `config.py` — no class wrapping; import with `from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT`
- `src/` flat layout — `llm_client.py` goes in `src/`, imported as `from llm_client import generate_tailored_resume`

### Integration Points
- Phase 3 `main.py` calls: `generate_tailored_resume(resume_text, job_description)` → returns LaTeX string → passes to `write_resume(latex_str, OUTPUT_DIR)`
- Phase 3 catches all exceptions from `llm_client.py` and handles print-to-stderr + `sys.exit(1)` at the boundary

</code_context>

<specifics>
## Specific Ideas

- The `/api/chat` request body must include: `model`, `messages` (system + user roles), `stream: false`, `options: {num_ctx: 8192}`
- `TIMEOUT = (10, 300)` is already defined in `config.py` — pass directly to `requests.post(..., timeout=TIMEOUT)`
- Job description wrapped in `<job_description>...</job_description>` XML delimiters in the user message (QUAL-04)
- Fence stripping must be unconditional (QUAL-01): strip regardless of whether fences are present — do not conditionally check
- `done_reason` check (QUAL-03): if response JSON contains `done_reason == "length"`, raise an error before any validation step

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 2-LLM Integration*
*Context gathered: 2026-05-28*
