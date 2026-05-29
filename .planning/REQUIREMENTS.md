# Requirements — Resume Tailor CLI

## v1 Requirements

### Core Flow

- [x] **CORE-01**: User can run the CLI tool that reads the base LaTeX resume from a configurable path in `config.py`
- [x] **CORE-02**: User can input a multiline job description via terminal prompt (type END on a new line to submit); EOFError treated as submission
- [x] **CORE-03**: User sees a progress message before the LLM call starts (so the tool does not appear frozen during cold model load)
- [x] **CORE-04**: Tool calls Ollama `/api/chat` (non-streaming) with `num_ctx: 8192`, `timeout=(10, 300)`, and role-separated system/user messages
- [x] **CORE-05**: Tool writes the tailored LaTeX output to `resumes/output/tailored_resume_YYYYMMDD_HHMMSS.tex` (directory created if missing)
- [x] **CORE-06**: Tool prints a success message with the full output file path on completion

### Output Quality & Safety

- [x] **QUAL-01**: LLM response is unconditionally stripped of markdown code fences before any further processing (do not rely on prompt alone)
- [x] **QUAL-02**: Output is validated in memory for `\documentclass` presence and `\end{document}` termination before writing to disk
- [x] **QUAL-03**: `done_reason` field in Ollama response is checked; if `"length"`, abort with a clear error message (do not write truncated output)
- [x] **QUAL-04**: Job description is wrapped in `<job_description>...</job_description>` XML delimiters in the prompt to prevent LaTeX special characters (`$`, `%`, `&`, `_`) from corrupting the LaTeX context

### Error Handling

- [x] **ERR-01**: If base resume file is not found, tool prints a human-readable error to stderr and exits with code 1
- [x] **ERR-02**: If Ollama connection fails or times out, tool prints a human-readable error to stderr and exits with code 1 (no raw traceback)
- [x] **ERR-03**: Tool performs an Ollama health check at startup (`GET /api/tags`) and fails fast with a clear message if Ollama is not reachable

### Configuration

- [x] **CONF-01**: `config.py` exposes `BASE_RESUME_PATH`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `OUTPUT_DIR`, and `TIMEOUT` as named constants — changing any of these requires no changes to other modules
- [x] **CONF-02**: All paths in `config.py` are anchored to `Path(__file__)` so the tool works regardless of which directory it is invoked from

### Packaging

- [x] **PKG-01**: Project is packaged with `pyproject.toml` + `uv`; installable as a `resume-tailor` shell command via `uv tool install .`

---

## v2 Requirements (Deferred)

- `--dry-run` flag — print the constructed prompt without calling Ollama; useful for iterating on prompt quality
- Diff output — show base vs tailored resume diff in terminal using `difflib` (stdlib); high portfolio signal
- Streaming output — print tokens as they arrive; conflicts with diff, defer until after diff is built

---

## Out of Scope

- **PDF auto-compilation** — user runs `pdflatex` themselves; out of scope per design
- **LangChain or LLM frameworks** — stdlib + `requests` only; adding frameworks contradicts portfolio intent
- **Web server or GUI** — CLI only; no HTTP server, no Electron wrapper
- **Multi-resume management** — single configurable base resume; no resume library or selection UI
- **Hallucination detection beyond prompt** — prompt-level guardrails are v1; diff review is v2

---

## Traceability

| REQ-ID | Phase | Notes |
|--------|-------|-------|
| CORE-01 | Phase 1 | File I/O foundation — reader uses config path |
| CORE-02 | Phase 3 | CLI wiring — multiline input loop in main.py |
| CORE-03 | Phase 3 | CLI wiring — progress message before LLM call |
| CORE-04 | Phase 2 | LLM integration — /api/chat call with num_ctx and timeout |
| CORE-05 | Phase 1 | File I/O foundation — writer creates timestamped output |
| CORE-06 | Phase 3 | CLI wiring — success message with output path |
| QUAL-01 | Phase 2 | LLM integration — unconditional fence stripping |
| QUAL-02 | Phase 2 | LLM integration — in-memory validation before write |
| QUAL-03 | Phase 2 | LLM integration — done_reason check |
| QUAL-04 | Phase 2 | LLM integration — XML delimiter wrapping in prompt |
| ERR-01  | Phase 1 | Foundation — FileNotFoundError for missing resume |
| ERR-02  | Phase 2 | LLM integration — connection/timeout error handling |
| ERR-03  | Phase 2 | LLM integration — startup health check via GET /api/tags |
| CONF-01 | Phase 1 | Foundation — config.py named constants |
| CONF-02 | Phase 1 | Foundation — __file__-anchored paths |
| PKG-01  | Phase 1 | Foundation — pyproject.toml + uv packaging |

---

*Generated: 2026-05-28*
