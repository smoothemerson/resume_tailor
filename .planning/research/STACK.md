# Test Stack — Resume Tailor CLI v1.2

**Project:** resume-tailor
**Milestone:** v1.2 Test Coverage
**Researched:** 2026-06-02
**Confidence:** HIGH (all choices verified against pytest 9.0.3 docs, Context7, and PyPI)

---

## Recommended Additions

| Tool | Version | Rationale |
|------|---------|-----------|
| pytest | >=9.0.3 (already installed) | Already in `[dependency-groups] dev`. No upgrade needed. Runs unittest.TestCase natively. |
| pytest-subprocess | 1.6.0 (conditional) | Fakes `subprocess.Popen` for e2e tests needing isolated subprocess mocking. Latest release May 2026, Python 3.6-3.15 compatible. **Add only if a CI environment without Ollama needs full e2e mocking.** For this milestone (real Ollama required for e2e), stdlib `subprocess.run` is sufficient and this dep should be omitted. |

**Net new dependencies for the minimum viable test pyramid: zero.** pytest 9.0.3 is already installed and ships `tmp_path`, `monkeypatch`, `pytest.mark.skipif`, and `pytest.skip()` — everything needed for all three test layers.

---

## What NOT to Add (and Why)

| Tool | Why Not |
|------|---------|
| `pytest-subprocess` (default) | Only add if CI must run e2e tests without Ollama. The v1.2 plan calls for real Ollama in e2e. Mocking the subprocess defeats the purpose of an e2e test. Revisit at v1.3 if headless CI is needed. |
| `responses` / `httpretty` / `respx` | HTTP mocking libraries. The existing `unittest.mock.patch` on `requests.get` / `requests.post` already works for all 11 unit tests. stdlib `unittest.mock` is sufficient; no HTTP interceptor library needed. |
| `pytest-httpx` | Requires switching HTTP client from `requests` to `httpx`. Direct conflict with the stdlib+requests constraint. |
| `pytest-asyncio` | The codebase is synchronous end-to-end. Zero async code. |
| `pytest-cov` / `coverage` | Out of scope for v1.2 (structural test pyramid, not coverage reporting). Add in a future milestone if coverage gates are desired. |
| `click.testing.CliRunner` | Applicable only to Click-based CLIs. This CLI uses `argparse` + `sys.stdin`. Not applicable. |
| `pytester` | pytest's built-in plugin for testing pytest plugins. Not application testing. Overkill here. |
| `factory_boy` / `faker` | No complex domain objects. All fixtures are strings and `Path` objects — Python literals are sufficient. |
| `pytest-docker` | Overkill. Ollama already runs locally; no container orchestration needed. |
| Any third-party mock library | `unittest.mock` ships with Python 3.3+, is already used in all 18 existing tests, and covers every mocking need in this codebase. |

---

## unittest vs pytest Style Migration Decision

**Decision: Keep existing unittest.TestCase tests as-is. Write all new tests in pytest function style.**

Rationale:
- pytest 9.x runs `unittest.TestCase` subclasses natively with full discovery; no configuration change needed.
- The 18 existing tests use `@patch` decorators which are bound to `TestCase` methods. Migrating them to pytest-style would require rewriting `self.assertRaises` to `pytest.raises`, `self.assertEqual` to plain `assert`, and all `@patch` decorators to `monkeypatch` fixture calls — significant churn with zero behavioral benefit.
- New tests (unit for `_build_messages`, `read_resume`, `write_resume`, `_check_ollama_health`; integration; e2e) should be written in pytest function style to leverage `tmp_path`, `monkeypatch`, and fixture composition cleanly.
- This creates a mixed codebase (unittest-style in `src/`, pytest-style in `tests/`), which is explicitly supported and documented by pytest.
- **Rule:** existing tests stay; all new tests use pytest functions.

---

## E2E Subprocess Pattern

**Decision: Use `subprocess.run` directly. Do not add `pytest-subprocess`.**

The correct e2e pattern — invoking the real CLI entry point via subprocess with real Ollama:

```python
# tests/e2e/test_cli_e2e.py
import re
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.mark.e2e
def test_golden_path(ollama_health, tmp_path):
    if not ollama_health:
        pytest.skip("Ollama not reachable")
    result = subprocess.run(
        [sys.executable, "-m", "cli", "--output-dir", str(tmp_path)],
        input="Senior ML Engineer role\nEND\n",
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent / "src",
    )
    assert result.returncode == 0
    tex_files = list(tmp_path.glob("tailored_resume_*.tex"))
    assert len(tex_files) == 1
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", tex_files[0].name)

@pytest.mark.e2e
def test_ollama_unreachable_exits_1(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:19999")
    result = subprocess.run(
        [sys.executable, "-m", "cli", "--output-dir", str(tmp_path)],
        input="Some job\nEND\n",
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent / "src",
    )
    assert result.returncode == 1
    assert "stderr" or result.stderr  # error message emitted
```

`pytest-subprocess` is the right tool when faking subprocesses for isolation. For this project, e2e tests exist specifically to confirm real end-to-end behavior with Ollama. Faking the subprocess invocation defeats that purpose.

---

## Integration Test Skip Pattern

**Decision: Session-scoped fixture returning a boolean; `pytest.skip()` inside each test body.**

`@pytest.mark.skipif` evaluates at collection time — it cannot make a live HTTP call. `pytest.skip()` inside a test body (or inside a fixture) fires at execution time, which is required for service availability checks.

```python
# tests/conftest.py
import pytest
import requests as _requests

@pytest.fixture(scope="session")
def ollama_health() -> bool:
    try:
        r = _requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False
```

```python
# tests/integration/test_ollama_integration.py
import pytest
from llm_client import _check_ollama_health, generate_tailored_resume

@pytest.mark.integration
def test_health_check_succeeds(ollama_health):
    if not ollama_health:
        pytest.skip("Ollama not reachable — skipping integration test")
    _check_ollama_health()  # must not raise

@pytest.mark.integration
def test_generate_returns_valid_latex(ollama_health):
    if not ollama_health:
        pytest.skip("Ollama not reachable — skipping integration test")
    result = generate_tailored_resume(
        "\\documentclass{article}\\begin{document}\\end{document}",
        "Software engineer with Python skills"
    )
    assert result.strip().startswith("\\documentclass")
    assert "\\end{document}" in result
```

The `ollama_health` fixture is `scope="session"` so the HTTP probe runs once per test run, not per test. The boolean return is clean — no magic, no autouse complexity.

---

## pytest Configuration

Add to `/workspace/pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "src"]
pythonpath = ["src"]
addopts = ["--strict-markers", "-ra"]
markers = [
    "unit: fast isolated tests with all I/O mocked",
    "integration: tests hitting real Ollama HTTP API (requires Ollama running)",
    "e2e: full subprocess CLI invocation with real Ollama (requires Ollama running)",
]
```

Notes on each option:
- `testpaths = ["tests", "src"]` — discovers both the new `tests/` tree and the existing `src/*_test.py` files without moving them.
- `pythonpath = ["src"]` — adds `src/` to `sys.path` so `from llm_client import ...` in `tests/` resolves without `sys.path.insert` hacks. The existing `sys.path.insert` in `src/*_test.py` stays harmless but redundant.
- `--strict-markers` — any unregistered marker causes a collection error, catching typos immediately.
- `-ra` — shows a short summary of all non-passing tests (skipped, xfailed, errors) after each run. Essential when integration/e2e tests skip conditionally; without it, conditional skips are silent.
- Three markers match the three test pyramid layers exactly.

---

## Test Directory Layout

```
/workspace/
├── pyproject.toml                      # add [tool.pytest.ini_options] here
├── src/
│   ├── cli.py
│   ├── cli_test.py                     # existing — keep in place; discovered via testpaths
│   ├── config.py
│   ├── llm_client.py
│   ├── llm_client_test.py              # existing — keep in place; discovered via testpaths
│   ├── log_manager.py
│   ├── resume_reader.py
│   └── resume_writer.py
└── tests/
    ├── conftest.py                     # shared ollama_health session fixture
    ├── unit/
    │   ├── __init__.py
    │   ├── test_build_messages.py      # _build_messages() XML shape and role structure
    │   ├── test_check_health.py        # _check_ollama_health() in isolation (mocked requests)
    │   ├── test_resume_reader.py       # read_resume() with tmp_path, FileNotFoundError
    │   └── test_resume_writer.py       # write_resume() with tmp_path, timestamp filename regex
    ├── integration/
    │   ├── __init__.py
    │   └── test_ollama_integration.py  # real health check + real generate call
    └── e2e/
        ├── __init__.py
        └── test_cli_e2e.py             # subprocess.run CLI invocation, exit codes, file output
```

Rationale for layout decisions:
- **Existing `src/*_test.py` files stay.** Moving them is out-of-scope churn. `testpaths = ["tests", "src"]` picks them up automatically.
- **Separate `tests/unit/`, `tests/integration/`, `tests/e2e/`** — enables `pytest tests/unit` for fast CI, `pytest tests/integration` for Ollama-dependent runs, and `pytest -m "not integration and not e2e"` to exclude slow/live tests from a dev loop.
- **`tests/conftest.py` at tests root** — the `ollama_health` fixture is shared by both integration and e2e layers, so it belongs at `tests/` root, not nested inside either subdirectory.
- **`__init__.py` in each test directory** — prevents import collisions when two test files in different directories share a name. With `importlib` import mode this matters less, but explicit `__init__.py` files are the safer baseline and explicit about directory boundaries.

---

## Running Tests by Layer

```bash
# Fast unit tests only (no Ollama required)
uv run pytest tests/unit src/ -m "not integration and not e2e"

# All unit tests including existing src/ tests
uv run pytest src/ tests/unit

# Integration tests (requires Ollama running)
uv run pytest tests/integration -m integration -v

# E2E tests (requires Ollama running)
uv run pytest tests/e2e -m e2e -v

# Full pyramid (skips integration/e2e if Ollama is down)
uv run pytest

# Legacy: existing src tests only
uv run pytest src/
```

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| pytest 9.x unittest compatibility | HIGH | Official pytest docs (Context7 verified), installed version confirmed |
| `tmp_path` / `monkeypatch` stdlib fixtures | HIGH | Core pytest fixtures, stable since pytest 4.x |
| `pytest.skip()` inside fixture/test vs decorator | HIGH | Official docs explicit on collection-time vs execution-time evaluation |
| `[tool.pytest.ini_options]` in pyproject.toml | HIGH | Supported since pytest 6.0; current docs confirm |
| `--strict-markers` + `markers =` in pyproject.toml | HIGH | Verified in pytest docs (Context7 fetched), stable feature |
| `testpaths` + `pythonpath` config | HIGH | Official goodpractices.html, confirmed pattern |
| `pytest-subprocess` 1.6.0 | MEDIUM | PyPI verified (May 2026 release); not added by default |
| `subprocess.run` for e2e invocation | HIGH | stdlib, no surprises; correct choice when real process needed |

---

## Sources

- pytest good practices (testpaths, pythonpath, src layout): https://docs.pytest.org/en/stable/explanation/goodpractices.html
- pytest skip/skipif patterns: https://docs.pytest.org/en/stable/how-to/skipping.html
- pytest markers (strict_markers, ini_options): fetched via Context7 `/pytest-dev/pytest`
- pytest unittest compatibility: fetched via Context7 `/pytest-dev/pytest`
- pytest-subprocess PyPI: https://pypi.org/project/pytest-subprocess/ (v1.6.0, May 2026)
- Subprocess server fixture pattern: https://til.simonwillison.net/pytest/subprocess-server
- pytest configuration reference: https://docs.pytest.org/en/stable/reference/customize.html

---

---

# Stack Research — v1.1 (archived reference)

**Project:** Resume Tailor CLI
**Researched:** 2026-06-02
**Overall confidence:** HIGH — all v1.1 features are solvable with existing stdlib; no new runtime dependencies needed

---

## v1.1 Additions Summary

Zero new runtime dependencies. All four new capabilities (diff view, keyword scoring, two-pass pipeline, hallucination/dropped-section detection) are covered by stdlib modules already available in Python 3.11+.

---

## Recommended Stack

### Core Technologies (unchanged from v1.0)

| Component | Choice | Version | Rationale |
|-----------|--------|---------|-----------|
| Language runtime | Python | 3.11+ (project uses 3.13 in pyproject.toml) | Unchanged. `match` statements, walrus operator, `tomllib`, `ExceptionGroup` all useful. |
| HTTP client | `requests` | 2.34.x (verified in venv) | Unchanged. Two sequential blocking POSTs to localhost; async adds nothing. |
| CLI entry point | `argparse` | stdlib | Unchanged. v1.1 adds no new flags beyond what argparse already handles. |
| Ollama endpoint | `/api/chat` | Ollama REST v1 | Unchanged. `stream: false`, `message.content` response path. |
| File I/O | `pathlib.Path` | stdlib | Unchanged. |
| Configuration | `config.py` | stdlib | Unchanged. `num_ctx` constant may need review (see two-pass notes below). |

### New Stdlib Modules for v1.1

| Module | Purpose | v1.1 Feature |
|--------|---------|--------------|
| `difflib` | Line-by-line unified diff between original and tailored `.tex` | Diff view |
| `re` | Keyword tokenization from JD text; LaTeX section header extraction; entity extraction for hallucination detection | Keyword scoring, dropped-section check, hallucination detection |
| `collections.Counter` | Keyword frequency counting and set-difference scoring | Keyword scoring |
| `json` | Already used; also handles analysis-pass JSON parsing with fallback | Two-pass pipeline |

All four modules are already in the stdlib and are imported in the existing codebase (`re` and `json` are already in `llm_client.py`). No `pip install` step needed.

---

## Feature-by-Feature Stack Decisions

### 1. Diff View

**Use `difflib.unified_diff`.**

```python
import difflib

def compute_diff(original: str, tailored: str) -> str:
    a = original.splitlines(keepends=True)
    b = tailored.splitlines(keepends=True)
    lines = difflib.unified_diff(a, b, fromfile="original.tex", tofile="tailored.tex", lineterm="")
    return "\n".join(lines)
```

`difflib.unified_diff` takes two sequences of strings (lines) and yields the standard unified diff format (`---`, `+++`, `@@`, `-line`, `+line`, ` context`). Use `str.splitlines(keepends=True)` to produce the correct input from the `.tex` string without touching the filesystem a second time.

For colored terminal output: prefix `+` lines with `\033[32m` (green), `-` lines with `\033[31m` (red), `@@` lines with `\033[36m` (cyan), and always reset with `\033[0m`. These are raw ANSI escape codes — no library needed, and they work correctly in every modern terminal. Do not add `colorama` as a dependency; it exists for Windows cmd.exe compatibility, which is not a target platform for this tool.

`difflib.HtmlDiff` is available if an HTML side-by-side view is ever needed, but for a CLI tool targeting terminal output, `unified_diff` is correct. `difflib.SequenceMatcher` is the lower-level API — no need to use it directly when `unified_diff` wraps it correctly.

**What not to use:** `subprocess(['diff', ...])` — requires `diff` to be installed, produces identical output, and adds a subprocess call for zero benefit. `rich.Syntax` or `pygments` — correct tools in a richer TUI, but a dependency violation here.

### 2. JD Keyword Match Scoring

**Use `re.findall` + set arithmetic.**

```python
import re

STOP_WORDS = {"the", "a", "an", "and", "or", "in", "of", "to", "for",
              "with", "is", "are", "we", "you", "our", "your", "will",
              "be", "have", "has", "that", "this", "at", "by", "on",
              "as", "it", "its", "not", "but", "from", "their", "they"}

def extract_keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]{2,}", text.lower())
    return set(tokens) - STOP_WORDS

def score_coverage(jd: str, tailored: str) -> dict:
    jd_kw = extract_keywords(jd)
    out_kw = extract_keywords(tailored)
    matched = jd_kw & out_kw
    missing = jd_kw - out_kw
    score = len(matched) / len(jd_kw) if jd_kw else 0.0
    return {"score": score, "matched": len(matched), "total": len(jd_kw), "missing_sample": sorted(missing)[:10]}
```

The regex `[a-zA-Z][a-zA-Z0-9+#./-]{2,}` captures multi-character tokens including tech-specific formats like `C++`, `ASP.NET`, `CI/CD`, and version strings. Set intersection gives matched keywords; set difference gives missing ones. A stop word list of ~25 common English words is sufficient — no `nltk` or `spacy` needed for this scope.

`collections.Counter` is not needed for simple coverage scoring (set arithmetic is cleaner), but use it if the feature evolves to rank keywords by frequency in the JD. Keep it available as an import if that direction emerges.

**What not to use:** `nltk`, `spacy`, `sklearn` — each adds a multi-MB dependency with no proportionate benefit for a bag-of-words coverage check. Stemming/lemmatization (reducing "deploying" → "deploy") is a nice-to-have but can be achieved with simple suffix stripping in stdlib (`word.rstrip("ing")`) if needed later.

### 3. Two-Pass Ollama Pipeline

**Two independent `requests.post()` calls. No `requests.Session`. No async.**

Pass 1 — JD analysis:
```json
{
  "model": "<model>",
  "messages": [
    {"role": "system", "content": "Extract JD requirements as JSON. Return ONLY a JSON object."},
    {"role": "user",   "content": "<job_description>...</job_description>"}
  ],
  "format": "json",
  "stream": false,
  "options": {"num_ctx": 4096}
}
```

Pass 2 — tailoring with analysis context:
```json
{
  "model": "<model>",
  "messages": [
    {"role": "system", "content": "<existing tailoring prompt>\n\nJD analysis: <analysis_json>"},
    {"role": "user",   "content": "<job_description>...<resume>..."}
  ],
  "stream": false,
  "options": {"num_ctx": 8192}
}
```

**Gotchas:**

- `done_reason: "length"` truncation check must run on **both** passes, not just pass 2. A truncated analysis pass produces a garbage JSON blob that poisons pass 2.
- `format: "json"` does **not** guarantee valid JSON (verified against Ollama API docs). The model must also be instructed in the system prompt to return only a JSON object. Always wrap pass 1's `json.loads()` in a try/except with a regex fallback: `re.search(r'\{.*\}', raw, re.DOTALL)`. If the fallback also fails, proceed with an empty analysis dict rather than raising — pass 2 can still run without analysis context.
- Context window: pass 1 needs only ~4096 tokens. Pass 2 needs `8192` or more because it now carries JD + resume + injected analysis. The existing `num_ctx: 8192` in config is sufficient if the analysis output is constrained to key fields (keywords list, seniority, role type). If the model returns verbose analysis, pass 2 may hit the window. Mitigation: constrain the pass 1 prompt to return a minimal schema: `{"keywords": [...], "seniority": "...", "role": "..."}`.
- `json_schema` in the `format` field (Ollama's structured output mode) is more reliable than `format: "json"` but requires the model to support it. For the current default (`qwen3:14b`) and small/medium models generally, `format: "json"` with explicit prompt instruction is the safer choice. Reserve json_schema for future work if analysis pass reliability becomes a pain point.
- Total latency doubles. The CLI progress message should be updated to reflect two passes ("Analyzing job description... / Tailoring resume...") so users do not assume the tool is hung.
- No `requests.Session` needed. TCP connection to localhost has near-zero handshake time; the read timeout (300s) dominates. Two independent `requests.post()` calls with the existing `TIMEOUT` constant is correct.

### 4. Hallucination and Dropped-Section Detection

**Use `re` only. No external NLP library needed.**

**Dropped-section detection:**
```python
import re

def extract_sections(latex_text: str) -> set[str]:
    return set(re.findall(r"\\(?:sub)*section\*?\{([^}]+)\}", latex_text))

def check_dropped_sections(original: str, tailored: str) -> list[str]:
    return sorted(extract_sections(original) - extract_sections(tailored))
```

The pattern `\\(?:sub)*section\*?\{([^}]+)\}` captures `\section{...}`, `\subsection{...}`, `\subsubsection{...}`, and starred variants. Verified against the actual LaTeX structure of `english.tex` style resumes. Set difference returns sections present in original but absent from tailored output.

**Hallucination detection:**
```python
def extract_entities(latex_text: str) -> dict:
    years = set(re.findall(r"\b(19|20)\d{2}\b", latex_text))
    bold_items = set(re.findall(r"\\textbf\{([^}]+)\}", latex_text))
    return {"years": years, "bold_items": bold_items}

def check_hallucinations(original: str, tailored: str) -> dict:
    orig = extract_entities(original)
    tail = extract_entities(tailored)
    return {
        "new_years": sorted(tail["years"] - orig["years"]),
        "new_bold_items": sorted(tail["bold_items"] - orig["bold_items"]),
    }
```

Years (`\b(19|20)\d{2}\b`) catch fabricated employment dates. `\textbf{...}` items catch new employer names, project names, or credentials the model may have invented. These are heuristics, not guarantees — they detect the most common hallucination patterns (new dates, new company names) without requiring semantic understanding. The system prompt already forbids hallucination; this detection layer is a post-generation sanity check that surfaces warnings to the user.

**Format violation detection** (for the "markdown prose" guard):
```python
def check_format_violations(text: str) -> list[str]:
    violations = []
    if re.search(r"^```", text, re.MULTILINE):
        violations.append("markdown_fence_detected")
    if not text.lstrip().startswith("\\documentclass"):
        violations.append("missing_documentclass")
    if "\\end{document}" not in text:
        violations.append("missing_end_document")
    return violations
```

This overlaps with the existing `_validate_latex` function in `llm_client.py` and should reuse or extend it rather than duplicate.

**What not to use:** `difflib.SequenceMatcher` for hallucination detection — it finds text similarity, not entity presence. `spacy` named entity recognition — excessive for detecting whether a year or `\textbf{}` value appears in a set. `fuzzywuzzy`/`rapidfuzz` — string matching libraries, not needed for exact set membership checks.

---

## Unchanged Stack (v1.0 decisions still valid)

All decisions from v1.0 STACK.md hold. The additions above layer onto the existing architecture without requiring changes to:

- `resume_reader.py` — no change
- `resume_writer.py` — no change
- `config.py` — `num_ctx` is already 8192; no change required unless model changes
- `cli.py` — updated to display two progress messages and new output sections
- `llm_client.py` — refactored to support two-pass flow; existing `_validate_latex` and `_strip_fences` reused

---

## Alternatives Considered (v1.1)

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `difflib.unified_diff` | `subprocess(['diff', ...])` | Requires `diff` binary; same output; adds process spawn overhead |
| `difflib.unified_diff` | `rich.Syntax` diff display | Adds a non-trivial dependency; violates stdlib+requests constraint |
| `re` keyword extraction | `nltk`, `spacy` | Multi-MB downloads for bag-of-words coverage check; no proportionate benefit |
| `re` entity extraction | semantic NER | Over-engineered for detecting date/employer hallucinations in known LaTeX structure |
| `format: "json"` + prompt | `format: json_schema` | json_schema structured output is less reliable on 14b-class models; format:json with explicit prompt instruction is more robust at this model size |
| Two sequential `requests.post()` | `requests.Session` | Session saves connection pooling overhead; for 2 calls to localhost over HTTP, savings are microseconds — not worth the complexity |
| Two sequential `requests.post()` | Async pipeline (`asyncio` + `httpx`) | Tool is inherently sequential: analysis must complete before tailoring; no concurrency available |

---

## What NOT to Add (v1.1 Scope)

| Avoid | Reason |
|-------|--------|
| `rich` | Correct tool for TUI output; wrong here — ANSI escape codes cover the diff coloring need, and adding `rich` would be the first violation of the stdlib+requests constraint |
| `nltk` / `spacy` | NLP pipeline for a token-set coverage check is architectural overkill; `re.findall` + set arithmetic is 10 lines and zero dependencies |
| `pydantic` / `instructor` | The analysis pass JSON is a small, optional dict; schema validation via `json.JSONDecodeError` + fallback is sufficient |
| `fuzzywuzzy` / `rapidfuzz` | Fuzzy matching is not needed for dropped-section or hallucination checks; exact set membership is the right operation |
| `colorama` | Windows cmd.exe ANSI compatibility shim; not a target platform; raw ANSI codes work in all target terminals (macOS/Linux) |
| `pytest-mock` or `responses` | Already have `pytest`; existing test patterns (monkeypatch + mock) cover the new modules |

---

## Dependency Surface (unchanged through v1.1 and v1.2)

```
# pyproject.toml [project.dependencies]
requests >= 2.32.0

# [dependency-groups] dev
pytest >= 9.0.3
ruff
mypy
```

Total runtime dependencies: **1**. v1.1 and v1.2 both add zero new runtime deps.

---

## Sources (v1.1)

- Ollama REST API (format field, stream:false, done_reason): https://github.com/ollama/ollama/blob/main/docs/api.md
- Python `difflib` module: https://docs.python.org/3/library/difflib.html
- Python `re` module: https://docs.python.org/3/library/re.html
- requests 2.34.2 version: verified live in project venv via `uv run`
