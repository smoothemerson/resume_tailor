# Phase 06: Two-Pass Pipeline - Pattern Map

**Mapped:** 2026-06-05
**Files analyzed:** 6 (1 new source, 1 new test, 2 modified source, 2 modified test)
**Analogs found:** 6 / 6

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/jd_analyzer.py` | service | request-response | `src/llm_client.py` | role-match (same LLM call shape) |
| `src/llm_client.py` | service | request-response | `src/llm_client.py` (self) | exact (modifying existing) |
| `src/cli.py` | controller | request-response | `src/cli.py` (self) | exact (modifying existing) |
| `tests/unit/test_jd_analyzer.py` | test | — | `tests/unit/test_llm_client.py` | exact (same mock/patch shape) |
| `tests/unit/test_llm_client.py` | test | — | `tests/unit/test_llm_client.py` (self) | exact (modifying existing) |
| `src/cli_test.py` | test | — | `src/cli_test.py` (self) | exact (modifying existing) |

---

## Pattern Assignments

### `src/jd_analyzer.py` (service, request-response)

**Analog:** `src/llm_client.py` (POST to `/api/chat`, `done_reason` guard, return typed result)
**Structure reference:** `src/guards.py` (single public entry point, internal `_` helpers, non-fatal fallback)
**Never-raises reference:** `src/diff_view.py` (public function never raises; all paths return cleanly)

**Imports pattern** — copy from `src/llm_client.py` lines 1–6, simplify:
```python
import json
import re

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT
```

**Module structure** — one public entry point, two private helpers (copy single-concern shape from `src/guards.py` lines 47–50):
```python
# src/guards.py lines 47-50 — public function calls private helpers, never raises
def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
```

`jd_analyzer.py` follows the same shape: `analyze_job_description()` calls `_build_analysis_messages()` and `_parse_analysis_response()` — both private, none exported.

**Core POST pattern** — copy from `src/llm_client.py` lines 139–165 (the `requests.post` + `raise_for_status` + `response.json()` sequence):
```python
# src/llm_client.py lines 139-165
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
```

NOTE for `jd_analyzer.py`: Do NOT copy the outer `try/except requests.*` blocks as-is. The analysis function wraps everything in `try/except Exception: return None` — connection errors and HTTP errors must return `None`, not raise (except `RuntimeError` from `done_reason: length` which must re-raise). See fallback pattern below.

**`done_reason` truncation guard** — copy from `src/llm_client.py` lines 167–171:
```python
# src/llm_client.py lines 167-171
if data.get("done_reason") == "length":
    raise RuntimeError(
        "LLM response was truncated (done_reason=length). "
        "The resume may be too long for the model context window."
    )
```

Adapt message: `"JD analysis response was truncated (done_reason=length)."`

**Fence-stripping** — copy from `src/llm_client.py` lines 112–116:
```python
# src/llm_client.py lines 112-116
def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```\s*\w*\s*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()
```

Apply the same regex to `message.content` before calling `json.loads()`.

**Non-fatal fallback pattern** — copy from `src/guards.py` lines 9–16 (try/except on internal helpers):
```python
# src/guards.py lines 9-16
def _check_missing_sections(original: str, tailored: str) -> None:
    try:
        original_sections = re.findall(r'\\header\{([^}]+)\}', original)
        for section in original_sections:
            if f'\\header{{{section}}}' not in tailored:
                logger.warning(f'Section "{section}" missing from tailored output.')
    except Exception as exc:
        logger.warning(f"Section check failed: {exc}")
```

`analyze_job_description()` applies this more aggressively: the entire function body (POST through `json.loads` through key validation) is wrapped in `try/except Exception: return None`, with `RuntimeError` explicitly re-raised before the outer except catches it:
```python
try:
    ...  # POST, response.json(), done_reason check, json.loads, key validation
    return {k: parsed[k] for k in required_keys}
except RuntimeError:
    raise          # done_reason=length is non-recoverable — propagate to cli.py
except Exception:
    return None    # all other failures degrade silently
```

**Message builder for analysis** — analogous to `_build_messages()` in `src/llm_client.py` lines 26–109 (system/user structure, XML tags in user message):
```python
# src/llm_client.py lines 97-108 — XML tag structure for user message
user_message = (
    "<job_description>\n"
    f"{job_description}\n"
    "</job_description>\n\n"
    "<resume>\n"
    f"{resume_text}\n"
    "</resume>"
)

return [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_message},
]
```

`_build_analysis_messages()` uses the same `[system, user]` list shape. System prompt is a compact extraction instruction (no LaTeX persona). User message wraps only the job description in `<job_description>` tags.

**Key validation** — no analog exists; use set subset check:
```python
required_keys = {"technologies", "requirements", "emphasis_areas"}
if not required_keys.issubset(parsed.keys()):
    return None
return {k: parsed[k] for k in required_keys}
```

---

### `src/llm_client.py` — modifications (service, request-response)

**Analog:** `src/llm_client.py` (self — extending existing file)

**`_build_messages()` signature change** — current signature at line 26:
```python
# src/llm_client.py line 26 — CURRENT
def _build_messages(resume_text: str, job_description: str) -> list[dict]:
```
Change to (analysis is optional, default `None` preserves all 8 existing test calls):
```python
def _build_messages(resume_text: str, job_description: str, analysis: dict | None = None) -> list[dict]:
```

**Analysis injection** — insert conditional block after the `user_message` assignment (lines 97–104) and before the `return` at line 106:
```python
# src/llm_client.py lines 97-108 — CURRENT user_message construction
user_message = (
    "<job_description>\n"
    f"{job_description}\n"
    "</job_description>\n\n"
    "<resume>\n"
    f"{resume_text}\n"
    "</resume>"
)

return [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_message},
]
```
After the `user_message =` assignment, add:
```python
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

**`generate_tailored_resume()` signature change** — current signature at lines 132–134:
```python
# src/llm_client.py lines 132-134 — CURRENT
def generate_tailored_resume(
    resume_text: str, job_description: str, model: str | None = None
) -> TailorResult:
```
Change to (analysis is optional keyword-only convention matches `model`):
```python
def generate_tailored_resume(
    resume_text: str, job_description: str, model: str | None = None, analysis: dict | None = None
) -> TailorResult:
```

Then update the `_build_messages()` call at line 138 to pass `analysis`:
```python
# src/llm_client.py line 138 — CURRENT
messages = _build_messages(resume_text, job_description)
# CHANGE TO:
messages = _build_messages(resume_text, job_description, analysis)
```

---

### `src/cli.py` — modifications (controller, request-response)

**Analog:** `src/cli.py` (self — extending existing file)

**Progress message pattern** — copy from `src/cli.py` line 47:
```python
# src/cli.py line 47 — existing pattern
print("Tailoring resume — this may take a minute...", flush=True)
```
New pass-1 message uses identical convention: `print("Analyzing job description...", flush=True)`

**Import addition** — current imports at lines 1–10:
```python
# src/cli.py lines 1-10 — CURRENT
import argparse
import sys
from pathlib import Path

from config import BASE_RESUME_PATH, OUTPUT_DIR
from diff_view import show_diff
from guards import run_guards
from llm_client import TailorResult, generate_tailored_resume
from resume_reader import read_resume
from resume_writer import write_resume
```
Add one import:
```python
from jd_analyzer import analyze_job_description
```

**Two-pass orchestration** — current single-pass flow at lines 47–58:
```python
# src/cli.py lines 47-58 — CURRENT single-pass flow
print("Tailoring resume — this may take a minute...", flush=True)

try:
    resume_text = read_resume(resume_path)
    result = generate_tailored_resume(resume_text, job_description, model=args.model)
    run_guards(resume_text, result.content, result.fences_stripped)
    output_path = write_resume(result.content, output_dir)
    show_diff(resume_text, result.content)
    print(f"Tailored resume written to: {output_path.resolve()}")
except (RuntimeError, ValueError, OSError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```
New two-pass flow inserts analysis call before the `print("Tailoring resume...")` line:
```python
print("Analyzing job description...", flush=True)
analysis = analyze_job_description(job_description, model=args.model)
print("Tailoring resume — this may take a minute...", flush=True)

try:
    resume_text = read_resume(resume_path)
    result = generate_tailored_resume(resume_text, job_description, analysis=analysis, model=args.model)
    run_guards(resume_text, result.content, result.fences_stripped)
    output_path = write_resume(result.content, output_dir)
    show_diff(resume_text, result.content)
    print(f"Tailored resume written to: {output_path.resolve()}")
except (RuntimeError, ValueError, OSError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

Note: `analyze_job_description()` sits OUTSIDE the `try` block. Its `None` return for parse failures is not an exception — no catch needed. The `RuntimeError` it raises for `done_reason: length` propagates naturally into the surrounding test catch or main process exit (cli.py has no outer try). If that RuntimeError needs to be caught, it can be placed inside the try block — see Open Question in RESEARCH.md. Default recommendation is outside for simplicity.

---

### `tests/unit/test_jd_analyzer.py` (test)

**Analog:** `tests/unit/test_llm_client.py` — exact match on mock/patch shape, `@pytest.mark.unit`, `MagicMock`, `requests.post` patching

**Imports pattern** — copy from `tests/unit/test_llm_client.py` lines 1–11:
```python
import pytest
import requests
from unittest.mock import MagicMock, patch

from jd_analyzer import analyze_job_description
```

**`@pytest.mark.unit` decorator** — every test in `tests/unit/test_llm_client.py` uses `@pytest.mark.unit` (e.g., lines 14, 20, 26). All new tests in `test_jd_analyzer.py` must use the same marker.

**Mock POST pattern** — copy from `tests/unit/test_llm_client.py` lines 141–152:
```python
# tests/unit/test_llm_client.py lines 141-152
@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_truncated_raises(mock_post, mock_health):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "length",
        "message": {"content": ""},
    }
    mock_post.return_value = mock_response
    with pytest.raises(RuntimeError, match="truncated"):
        generate_tailored_resume("resume", "job desc")
```
Adapt module path to `jd_analyzer.requests.post` (no health check to patch).

**Success case mock** — copy from `tests/unit/test_llm_client.py` lines 155–169, adapting for JSON content:
```python
# Pattern: mock_response.json.return_value sets the Ollama API response body
mock_response.json.return_value = {
    "done_reason": "stop",
    "message": {"content": '{"technologies": ["Python"], "requirements": ["5 years"], "emphasis_areas": ["ML"]}'},
}
```

**Fallback case (returns None)** — mock `requests.post` to raise `requests.ConnectionError`; assert `analyze_job_description(...)` returns `None`. No `pytest.raises` needed — the function must not raise.

**Missing keys case** — mock response content to `'{"technologies": [], "requirements": []}` (missing `emphasis_areas`); assert returns `None`.

**Truncation case** — mock `done_reason: "length"`; assert `pytest.raises(RuntimeError)`.

---

### `tests/unit/test_llm_client.py` — modifications (test)

**Analog:** `tests/unit/test_llm_client.py` (self — extending existing file)

**New test: `_build_messages` with analysis** — append after existing `_build_messages` tests (lines 14–61). Follow the exact same pattern:
```python
# tests/unit/test_llm_client.py lines 14-17 — pattern to copy for new tests
@pytest.mark.unit
def test_build_messages_returns_two_element_list():
    result = _build_messages("resume text", "job description")
    assert len(result) == 2
```

Two new test functions needed:
1. `test_build_messages_with_analysis_includes_jd_analysis_tag` — call `_build_messages("r", "jd", {"technologies": [], "requirements": [], "emphasis_areas": []})`, assert `"<jd_analysis>"` and `"</jd_analysis>"` in `result[1]["content"]`
2. `test_build_messages_without_analysis_omits_jd_analysis_tag` — call `_build_messages("r", "jd")` (2-arg, existing call shape), assert `"<jd_analysis>"` NOT in `result[1]["content"]`

Existing 8 `_build_messages` tests call with 2 positional args — they remain valid because `analysis` defaults to `None`. No existing test modifications required for `test_llm_client.py`.

---

### `src/cli_test.py` — modifications (test)

**Analog:** `src/cli_test.py` (self — modifying all 8 existing tests)

**Current test decorator stack** — copy from `src/cli_test.py` lines 9–16:
```python
# src/cli_test.py lines 9-16 — CURRENT decorator stack (representative test)
@patch("sys.argv", ["resume-tailor"])
@patch("cli.show_diff")
@patch("cli.write_resume")
@patch("cli.generate_tailored_resume")
@patch("cli.read_resume")
@patch("builtins.input")
@patch("cli.run_guards")
def test_end_sentinel_breaks_loop(mock_guards, mock_input, mock_read, mock_generate, mock_write, mock_show_diff):
```

**New decorator to add to all 8 tests:**
```python
@patch("cli.analyze_job_description", return_value=None)
```
Placement: add as the OUTERMOST `@patch` decorator (topmost line, just above `@patch("sys.argv", ...)`). Python applies decorators bottom-up, so the outermost decorator maps to the LAST parameter.

**Updated test signature** — add `mock_analyze` as the LAST parameter in the function signature:
```python
# AFTER modification — representative test
@patch("cli.analyze_job_description", return_value=None)   # NEW — outermost
@patch("sys.argv", ["resume-tailor"])
@patch("cli.show_diff")
@patch("cli.write_resume")
@patch("cli.generate_tailored_resume")
@patch("cli.read_resume")
@patch("builtins.input")
@patch("cli.run_guards")
def test_end_sentinel_breaks_loop(mock_guards, mock_input, mock_read, mock_generate, mock_write, mock_show_diff, mock_analyze):
```

**Default `return_value=None`** — used on all 8 existing tests (simulates fallback path, mirrors existing behavior). No assertion on `mock_analyze` needed in existing tests unless the test specifically targets injection.

**New tests to add** (in `src/cli_test.py`):
1. Test that `"Analyzing job description..."` is printed before analysis call — same `printed_lines` capture pattern as `test_progress_message_printed` (lines 109–123).
2. Test that `generate_tailored_resume` receives `analysis=None` when analysis returns `None` — check `mock_generate.call_args.kwargs["analysis"]`.
3. Test that `generate_tailored_resume` receives the dict when analysis returns a valid dict — set `@patch("cli.analyze_job_description", return_value={"technologies": [], "requirements": [], "emphasis_areas": []})`.

**`printed_lines` capture pattern** — copy from `src/cli_test.py` lines 117–122:
```python
# src/cli_test.py lines 117-122
printed_lines = []
with patch("builtins.print", side_effect=lambda *a, **kw: printed_lines.append(a[0] if a else "")):
    main()

assert any("Tailoring resume" in line for line in printed_lines), (
    f"Expected progress message containing 'Tailoring resume' in print calls, got: {printed_lines}"
)
```

---

## Shared Patterns

### Non-fatal fallback (return None instead of raise)
**Source:** `src/guards.py` lines 9–16, 19–30, 33–44
**Apply to:** `src/jd_analyzer.py` — entire `analyze_job_description()` body
```python
# src/guards.py lines 9-16
def _check_missing_sections(original: str, tailored: str) -> None:
    try:
        ...
    except Exception as exc:
        logger.warning(f"Section check failed: {exc}")
```
`jd_analyzer.py` uses the same `except Exception` catch-all, but returns `None` instead of logging (D-04: silent fallback).

### Raise-not-exit (LLM modules raise, only cli.py exits)
**Source:** `src/llm_client.py` lines 153–165; `src/cli.py` lines 56–58
**Apply to:** `src/jd_analyzer.py` — `done_reason: length` re-raises `RuntimeError`
```python
# src/llm_client.py lines 153-165 — raise pattern
except requests.ConnectionError as exc:
    raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}") from exc
...
# src/cli.py lines 56-58 — only cli.py calls sys.exit
except (RuntimeError, ValueError, OSError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

### `flush=True` on progress prints
**Source:** `src/cli.py` line 47
**Apply to:** new `print("Analyzing job description...", flush=True)` in `src/cli.py`
```python
# src/cli.py line 47
print("Tailoring resume — this may take a minute...", flush=True)
```

### XML tag data injection in user message
**Source:** `src/llm_client.py` lines 97–104
**Apply to:** `_build_analysis_messages()` in `src/jd_analyzer.py`; `_build_messages()` analysis injection block in `src/llm_client.py`
```python
# src/llm_client.py lines 97-104
user_message = (
    "<job_description>\n"
    f"{job_description}\n"
    "</job_description>\n\n"
    "<resume>\n"
    f"{resume_text}\n"
    "</resume>"
)
```

### `@pytest.mark.unit` on every unit test
**Source:** `tests/unit/test_llm_client.py` line 14 (and every test in the file)
**Apply to:** all new tests in `tests/unit/test_jd_analyzer.py`; all new tests added to `tests/unit/test_llm_client.py`
```python
@pytest.mark.unit
def test_...(self):
```

### `@patch` decorator ordering (outermost = last parameter)
**Source:** `src/cli_test.py` lines 9–16
**Apply to:** all 8 modified tests in `src/cli_test.py` when adding `@patch("cli.analyze_job_description")`
```python
# Decorators are applied bottom-up: bottom decorator → first param, top decorator → last param
@patch("cli.analyze_job_description", return_value=None)   # outermost → last param
@patch("sys.argv", ["resume-tailor"])                      # sys.argv needs no param slot
@patch("cli.show_diff")
...
@patch("cli.run_guards")
def test_name(mock_guards, ..., mock_show_diff, mock_analyze):
#                                               ^^^ last param = outermost patch
```

---

## No Analog Found

All files have analogs. No gaps.

---

## Metadata

**Analog search scope:** `src/`, `tests/unit/`
**Files read:** `src/llm_client.py`, `src/guards.py`, `src/cli.py`, `src/diff_view.py`, `src/cli_test.py`, `tests/unit/test_llm_client.py`
**Pattern extraction date:** 2026-06-05
