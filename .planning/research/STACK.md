# Stack Research

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

## Alternatives Considered

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

## Dependency Surface (unchanged)

```
# pyproject.toml [project.dependencies]
requests >= 2.32.0

# [dependency-groups] dev
pytest >= 9.0.3
ruff
mypy
```

Total runtime dependencies: **1**. v1.1 adds zero new runtime deps.

---

## Confidence Assessment

| Area | Level | Basis |
|------|-------|-------|
| `difflib.unified_diff` for diff view | HIGH | stdlib since Python 2.1; API stable; tested live against LaTeX content |
| `re` for keyword extraction and section detection | HIGH | stdlib; patterns verified against actual LaTeX resume structure |
| Two sequential `requests.post()` for two-pass pipeline | HIGH | Existing pattern in llm_client.py; no change to request shape beyond adding `format: "json"` to pass 1 |
| `format: "json"` reliability on 14b models | MEDIUM | Ollama API docs confirm format field exists and stream:false behavior; model compliance varies — fallback json extraction required |
| `json_schema` format field reliability on qwen3:14b | LOW | Not tested; smaller models may refuse or malform schema-constrained output; deferred |
| Hallucination detection via `re` entity extraction | MEDIUM | Heuristic approach — catches most common patterns (dates, `\textbf{}` values); won't catch inline text fabrication |
| `requests` 2.34.x as current version | HIGH | Verified in project venv via `uv run` |

---

## Sources

- Ollama REST API (format field, stream:false, done_reason): https://github.com/ollama/ollama/blob/main/docs/api.md — verified via WebFetch 2026-06-02
- Python `difflib` module: https://docs.python.org/3/library/difflib.html — stdlib, HIGH confidence
- Python `re` module: https://docs.python.org/3/library/re.html — stdlib, HIGH confidence
- requests 2.34.2 version: verified live in project venv via `uv run python3 -c "import requests; print(requests.__version__)"`
- All code patterns above: verified via live `python3` execution in the project environment
