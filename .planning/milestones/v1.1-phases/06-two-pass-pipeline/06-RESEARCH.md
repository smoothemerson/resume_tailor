# Phase 06: Two-Pass Pipeline - Research

**Researched:** 2026-06-05
**Domain:** Python LLM pipeline restructuring — adding a JSON-returning analysis pass before an existing tailoring call
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Pass-1 returns a structured JSON dict with exactly three keys: `technologies` (list), `requirements` (list), `emphasis_areas` (list). No additional keys.
- **D-02:** When pass-1 JSON parsing fails (including LLM errors, malformed JSON, missing keys), the analysis function returns `None`. The caller (`cli.py`) checks `if analysis is not None:` before injecting. `None` is unambiguous — it cannot be confused with an empty-but-valid response.
- **D-03:** Two separate progress messages, one per LLM call:
  - Before pass 1: `"Analyzing job description..."` (printed with `flush=True`)
  - Before pass 2: existing `"Tailoring resume — this may take a minute..."` (unchanged)
- **D-04:** When the pass-1 fallback triggers (analysis returned `None`), the tool is fully silent — no warning, no stderr message. Tool proceeds directly to the existing tailoring call.
- **D-05:** Both LLM calls respect the existing `done_reason: length` truncation guard with no new error handling paths.

### Claude's Discretion

- Injection placement: how the `{technologies, requirements, emphasis_areas}` dict is formatted and embedded in the tailoring prompt (new XML tag in the user message, or new section in the system prompt) is left to the planner.
- Module location for the JD analysis function: new `jd_analyzer.py` module (consistent with single-concern pattern) or inside `llm_client.py` alongside `generate_tailored_resume()`.
- Analysis system prompt persona and exact extraction prompt wording are left to the planner/implementer.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-01 | Tool performs a JD analysis pass (pass 1) before the tailoring call — extracts key technologies, role requirements, and emphasis areas from the job description | New `analyze_job_description()` function making a `/api/chat` POST with `stream: False`, returning `dict \| None` |
| PIPE-02 | Analysis output is injected into the tailoring prompt (pass 2) to guide section-specific rewrites | `generate_tailored_resume()` signature extended with `analysis: dict \| None = None`; `_build_messages()` conditionally appends structured analysis content |
| PIPE-03 | If pass 1 fails (malformed output, parse error), tool falls back to single-pass behavior — no abort, no error surfaced to user | Analysis function wraps all failure paths in `try/except Exception` and returns `None`; caller uses `if analysis is not None:` guard |
| PIPE-04 | Both LLM calls respect existing `done_reason` truncation guard | Analysis call checks `data.get("done_reason") == "length"` before extracting content; raises `RuntimeError` on length truncation (caught by `cli.py` except block) |
</phase_requirements>

---

## Summary

Phase 6 restructures the single LLM call in `generate_tailored_resume()` into a two-call pipeline. The first call (`analyze_job_description()`) sends only the job description to Ollama and requests a structured JSON response with three keys. The second call is the existing tailoring call, optionally augmented with the structured analysis result. The entire phase is a pure Python refactor — no new dependencies, no new config values, no changes to the LaTeX output contract.

The primary implementation decision left open is **module placement** (new `jd_analyzer.py` vs. added to `llm_client.py`) and **injection placement** (XML tag in user message vs. section in system prompt). Both decisions have clear tradeoffs documented below. All failure paths are already handled by the existing `try/except (RuntimeError, ValueError, OSError)` block in `cli.py`; the analysis function's `None` return bypasses injection silently.

The key risk is test coverage: `cli_test.py` has 8 existing tests that all mock `generate_tailored_resume` directly. Adding a new `analyze_job_description()` call to `cli.py` means every existing test that calls `main()` will need an additional `@patch("cli.analyze_job_description")` decorator, otherwise the test will call into real analysis logic.

**Primary recommendation:** Create `src/jd_analyzer.py` as a single-concern module following the `guards.py` / `diff_view.py` pattern. Inject analysis as an XML tag (`<jd_analysis>`) in the user message of `_build_messages()`, consistent with the existing `<job_description>` and `<resume>` tag structure.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pass-1 LLM call (JD analysis) | `jd_analyzer.py` or `llm_client.py` | — | Single-concern: one module per LLM interaction pattern |
| Pass-2 prompt assembly with analysis injection | `llm_client.py` (`_build_messages()`) | — | All prompt construction already lives here |
| Fallback logic (`None` check) | `cli.py` | — | Orchestration logic belongs in the CLI layer per existing pattern |
| Progress messaging | `cli.py` | — | All `print(flush=True)` calls are in `cli.py` today |
| Truncation guard | both LLM call sites | — | D-05 requires both passes check `done_reason: length` |
| Error surfacing / sys.exit | `cli.py` only | — | Established "raise-not-exit" rule: LLM modules raise, CLI exits |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json` (stdlib) | stdlib | Parse pass-1 LLM response as JSON dict | Project constraint: stdlib + requests only [ASSUMED] |
| `requests` | 2.32.x | HTTP POST to `/api/chat` for pass-1 | Explicit project constraint; already in use |
| `typing` (stdlib) | stdlib | `dict \| None` return type annotation | Used throughout existing codebase |

No new dependencies are introduced in this phase. [ASSUMED — confirmed by CONTEXT.md decision D-05 and CLAUDE.md constraint]

### Supporting

No additional supporting libraries — this phase reuses `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and `TIMEOUT` from `config.py` without modification.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `json.loads()` on raw `message.content` | Ollama `format: "json"` parameter | `format: "json"` forces Ollama to produce JSON but does not guarantee schema compliance; still requires key validation. Using it would simplify parse step but adds an Ollama version dependency. Not needed given the simple 3-key schema. [ASSUMED] |
| New `jd_analyzer.py` module | Adding `analyze_job_description()` to `llm_client.py` | `llm_client.py` is already the LLM layer; both calls are LLM calls. `jd_analyzer.py` keeps concerns separate and matches the single-concern module pattern (`guards.py`, `diff_view.py`). Either works — planner decides. |
| XML tag in user message for injection | Section in system prompt | User message injection keeps system prompt stable and reusable. System prompt already defines persona and constraints; injecting analysis there mixes execution-time data with configuration. User message injection mirrors existing `<job_description>` / `<resume>` pattern. [ASSUMED] |

**Installation:** No packages to install — no changes to `pyproject.toml` dependencies.

---

## Package Legitimacy Audit

No external packages are installed in this phase. Skip condition met.

---

## Architecture Patterns

### System Architecture Diagram

```
CLI main()
    │
    ├── print("Analyzing job description...", flush=True)
    │
    ├── analyze_job_description(job_description, model)    [NEW]
    │       │
    │       ├── POST /api/chat  (pass 1 — JD only)
    │       │       └── stream: False, response JSON extracted
    │       ├── json.loads(message.content)
    │       ├── key validation: {technologies, requirements, emphasis_areas}
    │       └── returns dict | None  (None on any failure)
    │
    ├── print("Tailoring resume — this may take a minute...", flush=True)
    │
    ├── generate_tailored_resume(resume_text, job_description, analysis=analysis, model)   [MODIFIED]
    │       │
    │       ├── _check_ollama_health()   [unchanged — called once]
    │       ├── _build_messages(resume_text, job_description, analysis)  [MODIFIED signature]
    │       │       └── conditionally appends <jd_analysis> XML block if analysis is not None
    │       ├── POST /api/chat  (pass 2 — full tailoring)
    │       └── done_reason guard, fence strip, LaTeX validate → TailorResult
    │
    ├── run_guards(...)      [unchanged]
    ├── write_resume(...)    [unchanged]
    ├── show_diff(...)       [unchanged]
    └── print success message
```

### Recommended Project Structure

```
src/
├── jd_analyzer.py       # NEW: analyze_job_description() — pass-1 LLM call, returns dict | None
├── cli.py               # MODIFIED: orchestrates two-pass flow, new progress message
├── llm_client.py        # MODIFIED: generate_tailored_resume() gains analysis param; _build_messages() gains analysis param
├── config.py            # unchanged
├── guards.py            # unchanged
├── diff_view.py         # unchanged
├── resume_reader.py     # unchanged
├── resume_writer.py     # unchanged
└── log_manager.py       # unchanged
```

### Pattern 1: Single-Concern Module with One Public Entry Point

**What:** Each module in this codebase exports exactly one public function. Internal helpers are prefixed with `_` and not exported.

**When to use:** Any new capability that can be described in a single sentence.

**Example (from `guards.py`):**
```python
# Source: src/guards.py (existing codebase)
def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
```

`jd_analyzer.py` follows this exactly: one public `analyze_job_description()` function, internal `_build_analysis_messages()` and `_parse_analysis_response()` helpers.

### Pattern 2: Non-Fatal Fallback via Return Value (not exception)

**What:** Functions that must never crash the pipeline return `None` (or a sentinel) rather than raising. The caller checks before using the value.

**When to use:** Any operation that is enhancement-only — failure degrades quality but must not abort the pipeline.

**Example (from `guards.py`):**
```python
# Source: src/guards.py (existing codebase)
def _check_missing_sections(original: str, tailored: str) -> None:
    try:
        ...
    except Exception as exc:
        logger.warning(f"Section check failed: {exc}")
```

`analyze_job_description()` applies this more aggressively: the entire function body is wrapped in `try/except Exception`, returning `None` on any failure — not just logging.

### Pattern 3: Raise-Not-Exit in LLM Modules

**What:** `llm_client.py` raises `RuntimeError` or `ValueError` for all error conditions. Only `cli.py` calls `sys.exit(1)`.

**When to use:** Always, in any module that is not `cli.py`.

**Why it matters here:** The pass-1 analysis function has two distinct failure modes:
1. **Recoverable** (parse error, missing keys, empty response) → return `None` silently
2. **Non-recoverable** (truncation via `done_reason: length`) → raise `RuntimeError`

The `done_reason: length` case is non-recoverable because it means the model's context window was exhausted on just the job description, which indicates a configuration problem. That `RuntimeError` bubbles up through `cli.py`'s `except (RuntimeError, ValueError, OSError)` block and exits with code 1 — same path as today.

### Pattern 4: XML Tag Structure in User Message

**What:** The existing tailoring prompt wraps inputs in XML tags in the user message. The system prompt defines persona, task, and constraints only.

**When to use:** When injecting execution-time data (job description, resume content, analysis results).

**Existing structure (from `llm_client.py` `_build_messages()`):**
```python
# Source: src/llm_client.py (existing codebase)
user_message = (
    "<job_description>\n"
    f"{job_description}\n"
    "</job_description>\n\n"
    "<resume>\n"
    f"{resume_text}\n"
    "</resume>"
)
```

**Proposed extension for analysis injection:**
```python
# Consistent with existing pattern
if analysis is not None:
    analysis_block = (
        "<jd_analysis>\n"
        f"technologies: {analysis['technologies']}\n"
        f"requirements: {analysis['requirements']}\n"
        f"emphasis_areas: {analysis['emphasis_areas']}\n"
        "</jd_analysis>\n\n"
    )
    user_message = analysis_block + user_message
```

### Pattern 5: `_build_messages()` for Analysis Pass

**What:** The analysis call needs its own message builder. It uses a minimal system prompt (no LaTeX persona needed) and a user message containing only the job description.

**Proposed structure:**
```python
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
```

### Anti-Patterns to Avoid

- **Double health check:** `_check_ollama_health()` is already called inside `generate_tailored_resume()`. If `analyze_job_description()` also calls it, health is checked twice per run — wasted latency. The CONTEXT.md code insights explicitly state: "pass-1 does NOT need a second health check". The analysis function should NOT call `_check_ollama_health()`.
- **Raising on JSON parse failure:** Pass-1 JSON failures must return `None`, not raise. Raising would surface a cryptic error to the user for a non-fatal degradation.
- **Injecting analysis into system prompt:** Mixes execution-time data with role/persona configuration. Harder to test (system prompt is a long static string) and breaks the existing XML-tag data injection pattern.
- **Validating analysis content beyond key presence:** PIPE-01 specifies three keys — checking that each list is non-empty or that values are strings would reject valid (if sparse) analysis results. Only validate key existence.
- **Adding `flush=True` only to the new message:** The existing `"Tailoring resume..."` message already uses `flush=True`. The new `"Analyzing job description..."` message must also use `flush=True` per D-03 and the existing pattern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON parsing from LLM response | Custom string parser for `{"key": [...]}` patterns | `json.loads()` (stdlib) | LLMs may produce valid JSON in various whitespace formats; `json.loads` handles all compliant JSON |
| Key validation | `hasattr` or index access without check | `all(k in parsed for k in ("technologies", "requirements", "emphasis_areas"))` | Clear, short, correct; raises no exception on missing keys |
| Mocking the analysis call in tests | Complex mock return value construction | `@patch("cli.analyze_job_description", return_value=None)` and `return_value={"technologies": [], "requirements": [], "emphasis_areas": []}` | Two states cover all test paths |

**Key insight:** The analysis function is structurally identical to `generate_tailored_resume()` with a simplified response contract. Copy the POST + JSON decode + `done_reason` guard pattern directly — no custom abstractions needed.

---

## Common Pitfalls

### Pitfall 1: Forgetting to Patch `analyze_job_description` in Existing cli_test.py Tests

**What goes wrong:** All 8 existing `cli_test.py` tests call `main()` with mocked `generate_tailored_resume`. After this phase, `main()` will call `analyze_job_description()` first. Without patching it, the test will attempt a real HTTP call to Ollama (which fails in CI) or call into the real function (which requires network).

**Why it happens:** The new call is inserted before `generate_tailored_resume` in the call sequence — all existing tests must add `@patch("cli.analyze_job_description")` decorators.

**How to avoid:** When modifying `cli.py`, immediately update all 8 tests in `cli_test.py` to add the new patch. Default mock return value should be `None` (simulates fallback path) unless the test specifically covers the injection path.

**Warning signs:** `ConnectionError` or `RuntimeError` in `cli_test.py` tests that previously passed cleanly.

### Pitfall 2: `_build_messages()` Signature Change Breaks Existing Unit Tests

**What goes wrong:** `test_llm_client.py` in `tests/unit/` has 8 tests that call `_build_messages("resume text", "job description")` with exactly 2 positional args. If `_build_messages` gains a required third param, all these tests fail.

**Why it happens:** The `analysis` parameter should be `analysis: dict | None = None` (optional with default `None`) so existing 2-arg calls remain valid.

**How to avoid:** Add `analysis: dict | None = None` as the third parameter to `_build_messages()`. Do not make it required.

**Warning signs:** `TypeError: _build_messages() missing 1 required positional argument` in unit tests.

### Pitfall 3: `json.loads()` on Markdown-Wrapped JSON

**What goes wrong:** Some LLMs return JSON wrapped in markdown fences (` ```json ... ``` `). `json.loads()` will raise `JSONDecodeError` on fenced content.

**Why it happens:** The model ignores the "no markdown" instruction in the system prompt.

**How to avoid:** Apply a strip pattern before parsing — try `json.loads(content)` first, and on `JSONDecodeError`, try stripping a ` ```json ` / ` ``` ` wrapper and retrying once. If still invalid, return `None`. Alternatively, use `re.search(r'\{.*\}', content, re.DOTALL)` to extract the first JSON object literal.

**Warning signs:** Analysis consistently returns `None` even when the model appears to be responding — check raw `message.content` in debug output.

### Pitfall 4: Analysis Raising RuntimeError Bypasses Fallback

**What goes wrong:** If `analyze_job_description()` raises `RuntimeError` instead of returning `None` on a JSON parse failure, `cli.py`'s except block catches it and exits code 1 — killing the pipeline entirely instead of falling back to single-pass.

**Why it happens:** The `done_reason: length` truncation check must raise (non-recoverable), but all other failures (parse errors, missing keys, HTTP errors, connection errors) must return `None` instead of raising.

**How to avoid:** Structure the function with an outer `try/except Exception` that returns `None`, with the `done_reason` check positioned BEFORE the outer try, or re-raised from within it. See code example below.

**Warning signs:** Pass-1 failure causes exit code 1 instead of degrading to single-pass.

### Pitfall 5: Health Check Called Twice

**What goes wrong:** If `analyze_job_description()` calls `_check_ollama_health()`, and then `generate_tailored_resume()` also calls it (as it does today), every run makes two health check GETs to `/api/tags` before any actual work.

**Why it happens:** It feels natural to guard every LLM call with a health check. But the health check in `generate_tailored_resume()` already covers both calls — if Ollama goes down between the two calls, the second POST will fail with a `ConnectionError` which is already handled.

**How to avoid:** `analyze_job_description()` does not call `_check_ollama_health()`. The single check in `generate_tailored_resume()` is sufficient.

---

## Code Examples

### Analysis Function Structure (Non-Fatal Fallback)

```python
# Pattern: outer try/except returns None; done_reason check raises before fallback
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
            raise RuntimeError(
                "JD analysis response was truncated (done_reason=length)."
            )
        raw = data["message"]["content"]
        # strip markdown fences if present
        content = raw.strip()
        if content.startswith("```"):
            content = re.sub(r"^```\s*\w*\s*\n?", "", content)
            content = re.sub(r"\n?```$", "", content).strip()
        parsed = json.loads(content)
        required_keys = {"technologies", "requirements", "emphasis_areas"}
        if not required_keys.issubset(parsed.keys()):
            return None
        return {k: parsed[k] for k in required_keys}
    except RuntimeError:
        raise
    except Exception:
        return None
```

Key structural points:
- `RuntimeError` (from `done_reason: length`) is re-raised — it propagates to `cli.py`'s except block and exits code 1
- All other exceptions (connection, HTTP, JSON parse, key error) are caught and return `None`
- Fence stripping mirrors `_strip_fences()` in `llm_client.py`

### `generate_tailored_resume()` Signature Extension

```python
# Modified signature — analysis is optional, defaults to None
def generate_tailored_resume(
    resume_text: str, job_description: str, model: str | None = None, analysis: dict | None = None
) -> TailorResult:
    effective_model = model or OLLAMA_MODEL
    _check_ollama_health()
    messages = _build_messages(resume_text, job_description, analysis)
    ...
```

### `_build_messages()` Analysis Injection

```python
# Modified _build_messages — analysis is optional XML block prepended to user message
def _build_messages(resume_text: str, job_description: str, analysis: dict | None = None) -> list[dict]:
    ...
    user_message = (
        "<job_description>\n"
        f"{job_description}\n"
        "</job_description>\n\n"
        "<resume>\n"
        f"{resume_text}\n"
        "</resume>"
    )
    if analysis is not None:
        analysis_lines = (
            "<jd_analysis>\n"
            f"technologies: {analysis['technologies']}\n"
            f"requirements: {analysis['requirements']}\n"
            f"emphasis_areas: {analysis['emphasis_areas']}\n"
            "</jd_analysis>\n\n"
        )
        user_message = analysis_lines + user_message
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
```

### `cli.py` Two-Pass Flow

```python
# Modified main() — two progress messages, analysis result passed through
print("Analyzing job description...", flush=True)
analysis = analyze_job_description(job_description, model=args.model)
print("Tailoring resume — this may take a minute...", flush=True)
try:
    resume_text = read_resume(resume_path)
    result = generate_tailored_resume(resume_text, job_description, analysis=analysis, model=args.model)
    ...
```

Note: the existing progress message currently appears before `read_resume()`. The new flow preserves the spirit — analysis message before analysis call, tailoring message before tailoring call. `read_resume()` can stay before the analysis call (reading the file is fast and unambiguous) or move inside the try block. Either way works; keeping it where it is today (implicitly before analysis) is simplest.

### Patching `analyze_job_description` in Existing Tests

```python
# Pattern to apply to all 8 existing cli_test.py tests
@patch("cli.analyze_job_description", return_value=None)   # NEW
@patch("cli.show_diff")
@patch("cli.write_resume")
@patch("cli.generate_tailored_resume")
@patch("cli.read_resume")
@patch("builtins.input")
@patch("cli.run_guards")
def test_end_sentinel_breaks_loop(mock_guards, mock_input, mock_read, mock_generate, mock_write, mock_show_diff, mock_analyze):
    ...
```

Note the decorator order: decorators are applied bottom-up, so `mock_analyze` becomes the last parameter. All existing tests default to `return_value=None` (fallback path). New tests covering injection explicitly set `return_value={"technologies": [...], ...}`.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-pass tailoring with raw JD text | Two-pass: structured JD analysis feeds tailoring | Phase 6 | Tailoring prompt gains explicit keyword/requirement structure |
| `generate_tailored_resume(resume, jd, model)` | `generate_tailored_resume(resume, jd, model, analysis)` | Phase 6 | Backward-compatible; existing call sites with `analysis=None` unchanged |
| `_build_messages(resume, jd)` | `_build_messages(resume, jd, analysis)` | Phase 6 | Optional third parameter; existing 2-arg test calls remain valid |

**No deprecations:** The single-pass path is preserved as fallback. There is no old code to remove.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `json` stdlib is sufficient to parse Ollama's JSON output — no third-party JSON library needed | Standard Stack | Low risk: stdlib `json` is complete and handles all valid JSON |
| A2 | The analysis call does not benefit from `"options": {"num_ctx": 8192}` (JD is shorter than a full resume) | Code Examples | Low risk: context window pressure is smaller for JD-only input; can add if needed |
| A3 | Injecting analysis as XML tag in user message (before `<job_description>`) is consistent with model attention behavior | Architecture Patterns | Low risk: placement within user message does not materially affect behavior; either ordering works |
| A4 | All 8 existing `cli_test.py` tests need a new `@patch("cli.analyze_job_description")` decorator after this phase | Common Pitfalls | HIGH risk if wrong: tests will fail in CI; must be verified during implementation |

**Verified claims:** All architectural patterns, function signatures, and test structures above are derived from direct code inspection of the existing codebase (`[VERIFIED: codebase grep]`). No external library documentation was required.

---

## Open Questions (RESOLVED)

1. **Where does `read_resume()` go relative to the analysis call?**
   - RESOLVED: `analyze_job_description()` is placed INSIDE the `try:` block (Plan 05, Task 1). Both LLM calls sit inside the existing try block so truncation `RuntimeError` is caught by the existing `except (RuntimeError, ValueError, OSError)` handler. `read_resume()` stays in its current position inside the try block.

2. **Should `analyze_job_description()` be in `jd_analyzer.py` or `llm_client.py`?**
   - RESOLVED: `jd_analyzer.py` (Plans 03 and 05). Separate module follows the single-concern pattern (`guards.py`, `diff_view.py`) and gives Phase 7 a clean import path for keyword matching.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All modules | ✓ | 3.11.2 | — |
| `requests` | HTTP calls to Ollama | ✓ | in pyproject.toml deps | — |
| `json` (stdlib) | Analysis response parsing | ✓ | stdlib | — |
| `uv` | Dev tooling | ✓ | 0.11.17 | — |
| pytest | Test suite | ✓ | 9.0.3 (via .venv) | — |
| Ollama | Integration/e2e tests only | unknown at research time | — | Tests skip when not available (existing fixture) |

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest -m unit tests/unit/ -x -q` |
| Full suite command | `pytest --tb=short -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | `analyze_job_description()` returns `dict` with three keys on valid JD | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x` | ❌ Wave 0 |
| PIPE-01 | Pass-1 progress message `"Analyzing job description..."` printed before analysis call | unit | `pytest -m unit src/cli_test.py::test_progress_message_printed -x` | ✅ (modify) |
| PIPE-02 | `_build_messages()` includes `<jd_analysis>` block when analysis is not None | unit | `pytest -m unit tests/unit/test_llm_client.py -x -k jd_analysis` | ❌ Wave 0 |
| PIPE-02 | `_build_messages()` omits `<jd_analysis>` block when analysis is None | unit | `pytest -m unit tests/unit/test_llm_client.py -x -k no_analysis` | ❌ Wave 0 |
| PIPE-03 | `analyze_job_description()` returns `None` on JSON parse failure | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x -k fallback` | ❌ Wave 0 |
| PIPE-03 | `analyze_job_description()` returns `None` on missing required keys | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x -k missing_keys` | ❌ Wave 0 |
| PIPE-03 | `analyze_job_description()` returns `None` on connection error | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x -k connection` | ❌ Wave 0 |
| PIPE-03 | `cli.py` calls `generate_tailored_resume` with `analysis=None` when analysis failed | unit | `pytest -m unit src/cli_test.py -x -k fallback` | ❌ Wave 0 |
| PIPE-04 | `analyze_job_description()` raises `RuntimeError` on `done_reason: length` | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x -k truncated` | ❌ Wave 0 |
| PIPE-04 | `generate_tailored_resume()` still raises on `done_reason: length` (unchanged) | unit | `pytest -m unit tests/unit/test_llm_client.py::test_generate_tailored_resume_truncated_raises` | ✅ existing |

### Sampling Rate

- **Per task commit:** `pytest -m unit -x -q`
- **Per wave merge:** `pytest --tb=short -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_jd_analyzer.py` — covers PIPE-01, PIPE-03, PIPE-04 for the analysis function
- [ ] New test cases in `tests/unit/test_llm_client.py` — covers PIPE-02 (`_build_messages` with/without analysis)
- [ ] New/updated test cases in `src/cli_test.py` — add `@patch("cli.analyze_job_description")` to all 8 existing tests + add new tests for injection and fallback paths

---

## Security Domain

Phase 6 introduces no new authentication, session management, access control, or cryptographic operations. The only new external interaction is an additional POST to `http://localhost:11434` — same trust boundary as the existing tailoring call.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (low severity) | `required_keys.issubset(parsed.keys())` — validate JSON structure before use |
| V6 Cryptography | no | — |

The job description is user-supplied text forwarded to a local LLM. No sanitization is required for localhost-only calls. The analysis result is a Python dict consumed internally — no SQL, no shell interpolation, no template rendering.

---

## Sources

### Primary (HIGH confidence)

- `src/llm_client.py` — direct code inspection: `generate_tailored_resume()`, `_build_messages()`, `TailorResult`, `_check_ollama_health()`, truncation guard pattern [VERIFIED: codebase]
- `src/cli.py` — direct code inspection: progress message placement, `try/except` block structure, integration points [VERIFIED: codebase]
- `src/guards.py` — direct code inspection: single-concern module pattern, non-fatal fallback pattern [VERIFIED: codebase]
- `src/diff_view.py` — direct code inspection: single-concern module with one public entry point, no raises [VERIFIED: codebase]
- `src/cli_test.py` — direct code inspection: 8 existing tests, mock patterns, decoration order [VERIFIED: codebase]
- `tests/unit/test_llm_client.py` — direct code inspection: existing `_build_messages` test coverage, 2-arg call signatures [VERIFIED: codebase]
- `.planning/phases/06-two-pass-pipeline/06-CONTEXT.md` — locked decisions D-01 through D-05 [VERIFIED: planning artifact]

### Secondary (MEDIUM confidence)

- Python stdlib `json` module behavior: `json.loads()` raises `json.JSONDecodeError` (subclass of `ValueError`) on invalid JSON [ASSUMED — standard Python behavior, not re-verified]

### Tertiary (LOW confidence)

- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; uses existing patterns from inspected codebase
- Architecture: HIGH — derived from direct code inspection; all integration points explicitly identified in CONTEXT.md
- Pitfalls: HIGH — Pitfalls 1 and 2 are mechanically certain from reading the existing test files; Pitfalls 3-5 are from standard LLM integration patterns

**Research date:** 2026-06-05
**Valid until:** 2026-07-05 (stable domain — pure Python, no external API changes expected)
