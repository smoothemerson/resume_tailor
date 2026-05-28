# Stack Research

**Project:** Resume Tailor CLI
**Researched:** 2026-05-28
**Overall confidence:** HIGH — narrow, stable problem space; all components are well-established

---

## Recommended Stack

| Component | Choice | Version | Rationale |
|-----------|--------|---------|-----------|
| Language runtime | Python | 3.11+ | Walrus operator, `tomllib` stdlib, `match` statements, and `ExceptionGroup` are all useful; 3.10 is EOL in Oct 2026 and 3.11 brings ~25% perf uplift. 3.12 or 3.13 is fine; 3.11 is the safe minimum. |
| HTTP client | `requests` | 2.32.x | Project constraint. Synchronous, stable, zero learning curve. For a single blocking POST to localhost, async (httpx) has zero benefit. `requests` 2.32 fixed a urllib3 CVE (GHSA-9wx4-h78v-vm56); pin `>= 2.32.0`. |
| CLI entry point | `argparse` (stdlib) | stdlib | Project already constrains to stdlib + requests. `argparse` handles the entire interface: `--model`, `--resume`, `--output-dir` flags are trivial. Avoids adding Click/Typer as deps for what amounts to 3 optional flags. |
| Multiline input | `sys.stdin` loop | stdlib | Read lines until sentinel `END`. `input()` in a `while True` loop is the correct Python idiom; no library needed. |
| File I/O | `pathlib.Path` | stdlib | `Path` over `os.path` everywhere: `.read_text()`, `.write_text()`, `.mkdir(parents=True, exist_ok=True)` — cleaner and less error-prone. |
| Timestamped filenames | `datetime` | stdlib | `datetime.now().strftime("%Y%m%d_%H%M%S")` produces the required `tailored_resume_YYYYMMDD_HHMMSS.tex` format directly. |
| Configuration | `config.py` (plain module) | stdlib | A plain Python module with constants (`MODEL`, `BASE_RESUME_PATH`, `OUTPUT_DIR`, `OLLAMA_URL`) is readable, importable, and requires no config-parsing library. `tomllib` (3.11+) is an alternative if TOML is preferred for user-facing config, but a `.py` file is simpler for a CLI personal tool. |
| JSON handling | `json` | stdlib | Ollama's REST API speaks JSON. `json.dumps()` for the request body, `response.json()` for parsing — both stdlib, both correct. |
| Error handling | `try/except` + `sys.exit(1)` | stdlib | Explicit `FileNotFoundError` for missing `.tex`, `requests.exceptions.ConnectionError` for Ollama being down. Print human-readable messages to `stderr` (`sys.stderr`), exit with code 1. No third-party error library needed. |
| Ollama endpoint | `/api/chat` | Ollama REST v1 | `/api/chat` with `stream: false` returns a single JSON object with `message.content`. Prefer `/api/chat` over `/api/generate`: it supports the system/user message structure natively, which maps directly to the prompt strategy (system prompt = LaTeX guardrail, user message = job description + resume). `/api/generate` conflates system and prompt into a single string, making prompt hygiene harder. |
| Dev tooling | `uv` | 0.4+ | `uv` is the 2025 standard for Python project setup: creates venvs, manages `pyproject.toml`, and installs deps faster than pip. `pyproject.toml` + `uv.lock` is the correct packaging baseline even for a single-dep project. |
| Project metadata | `pyproject.toml` | PEP 517/518 | Replaces `setup.py` and `requirements.txt`. Defines `[project.scripts]` entry point for `resume-tailor = "resume_tailor.cli:main"` so the tool is installable as a shell command. |
| Linting / formatting | `ruff` | 0.4+ | Single tool replacing flake8 + isort + black. Extremely fast, zero config needed for a project this size. Portfolio code should be clean. |
| Type checking | `mypy` (optional, dev only) | 1.10+ | Not required, but type hints on public functions (`def call_ollama(prompt: str, model: str) -> str`) improve portfolio legibility and catch bugs. Add as dev dependency. |

---

## What NOT to Use (and Why)

| Category | Avoid | Reason |
|----------|-------|--------|
| LLM frameworks | LangChain, LlamaIndex, Haystack | Explicit project constraint. Also: all three are architecturally wrong here. LangChain alone pulls in 40+ transitive dependencies for what is a single `POST` request. The overhead is unjustifiable. |
| Async HTTP | `httpx`, `aiohttp` | The tool is sequential: read file → get input → POST to Ollama → write file. There is no concurrency benefit. `httpx` is excellent but adds a dep for zero gain. `requests` is correct here. |
| CLI frameworks | `click`, `typer`, `fire` | The interface is 3 optional flags and one multiline input loop. `click` and `typer` are valuable for complex CLIs with many subcommands; they are excess for this tool. Adding them signals dependency-blindness in a portfolio piece explicitly showcasing minimalism. |
| Ollama Python SDK | `ollama` (PyPI package) | The `ollama` PyPI package is a thin wrapper around the same REST calls. Using it would add a dependency that hides the HTTP call — the opposite of what the project is demonstrating (direct REST integration). Also conflicts with the stdlib + requests constraint. |
| `requests[security]` extras | — | Not needed for localhost calls. The `certifi`, `pyOpenSSL`, `cryptography` extras are for TLS verification against external services; Ollama on `http://localhost` uses plain HTTP. |
| `dotenv` / `python-dotenv` | — | Config is a Python module (`config.py`), not environment variables. `python-dotenv` is appropriate when deploying to cloud where env vars are injected; it is unnecessary overhead for a local CLI. |
| Structured output libraries | `pydantic`, `instructor` | Ollama's response is a simple string in `message.content`. No schema validation needed on the return path. Pydantic is excellent but would be premature optimization here; the LaTeX validity check is a compile step, not a runtime schema. |
| `subprocess` for pdflatex | — | Out of scope per PROJECT.md. Do not invoke pdflatex from the tool — user does this themselves. |
| `logging` module | — | The tool has two output paths: success message to stdout, error message to stderr. A full logging framework is unnecessary. Direct `print(..., file=sys.stderr)` is cleaner for a CLI. |

---

## Ollama API Decision Detail

**Use `/api/chat` with `stream: false`.**

Request shape:
```json
{
  "model": "mistral",
  "stream": false,
  "messages": [
    {"role": "system", "content": "<LaTeX guardrail prompt>"},
    {"role": "user",   "content": "<job description + resume content>"}
  ]
}
```

Response shape (relevant fields):
```json
{
  "message": {
    "role": "assistant",
    "content": "<tailored LaTeX string>"
  },
  "done": true
}
```

The output is at `response.json()["message"]["content"]`.

`/api/generate` uses a flat `prompt` string and a separate `system` field — workable but less semantically clear. `/api/chat` mirrors the OpenAI chat completions interface and is the Ollama-recommended path for instruction-following tasks. Both endpoints are stable as of Ollama 0.1.x through 0.5.x (HIGH confidence from training data; the endpoint has not changed since Ollama's public release).

---

## Dependency Surface

```
# pyproject.toml [project.dependencies]
requests >= 2.32.0

# [project.optional-dependencies]
# dev = ["ruff", "mypy"]
```

Total runtime dependencies: **1**. This is the entire point.

---

## Confidence Assessment

| Area | Level | Basis |
|------|-------|-------|
| `requests` as the correct HTTP choice | HIGH | Explicit project constraint; design rationale is sound and well-documented in Python community |
| `/api/chat` over `/api/generate` | HIGH | Ollama API design is stable; message-role separation is the standard LLM interface pattern |
| `argparse` over Click/Typer | HIGH | Scale of the CLI (3 flags) makes this clear-cut; no web search needed |
| `pathlib` for file I/O | HIGH | PEP 428 stdlib; universally recommended in modern Python |
| `uv` + `pyproject.toml` for packaging | HIGH | `uv` is the de facto 2025 Python packaging standard; `requirements.txt` is deprecated for new projects |
| `ruff` for linting | HIGH | Dominant linting tool since 2023; replaced flake8+black+isort across most major Python projects |
| Specific version numbers (`requests 2.32.x`, `ruff 0.4+`) | MEDIUM | Based on training data (cutoff Aug 2025); verify on PyPI before pinning — these are the correct major/minor lines but patch versions may have advanced |
| `mypy 1.10+` | MEDIUM | Training data version; confirm current stable on PyPI |

---

## Sources

- Ollama REST API: https://github.com/ollama/ollama/blob/main/docs/api.md (confirmed stable endpoint design through training data, Aug 2025)
- requests library: https://pypi.org/project/requests/ (2.32 security fix series; HIGH confidence)
- uv packaging tool: https://docs.astral.sh/uv/ (Astral, current standard as of 2025)
- ruff linter: https://docs.astral.sh/ruff/ (Astral, dominant Python linter 2024-2025)
- PEP 517/518 pyproject.toml: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- Python 3.11 release notes: https://docs.python.org/3/whatsnew/3.11.html
