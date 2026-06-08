---
phase: 10-integration-tests
reviewed: 2026-06-07T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - tests/integration/test_llm_client.py
  - pyproject.toml
findings:
  critical: 2
  warning: 2
  info: 1
  total: 5
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-06-07
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Two files were reviewed: `tests/integration/test_llm_client.py` (2 integration tests against a live Ollama instance) and `pyproject.toml`. `tests/conftest.py` and `src/llm_client.py` were read as direct dependencies of the test under review.

Two critical defects were found. First, an assertion in the integration test is logically inverted: it asserts that the live model did NOT trigger the fence-stripping guard, making the test fail precisely when correct guard behavior fires. Second, cross-module analysis confirms that `_build_messages` in the production module is missing the `jd_analysis` third parameter that unit tests were written to expect — meaning both the unit test suite (one test currently fails with `TypeError`) and the integration test exercise an incomplete implementation.

Two warnings address gaps in the skip-guard reliability. One informational note confirms marker discipline is consistent.

---

## Critical Issues

### CR-01: `fences_stripped is False` assertion inverts the contract — fails on correct guard behavior

**File:** `tests/integration/test_llm_client.py:26`

**Issue:** The test hard-asserts `result.fences_stripped is False`. This assertion passes only when the live LLM returns clean LaTeX with no markdown fences. The entire purpose of `_strip_fences` and the `fences_stripped` flag is to handle the common real-world case where a model wraps output in triple-backtick fences despite instructions. When the model returns fenced LaTeX, `generate_tailored_resume` correctly strips them, sets `fences_stripped = True`, and returns valid content — but this test reports a failure even though behavior is correct and intentional.

The `assert "```" not in result.content` assertion on line 25 already verifies that fences are absent from output. Line 26 adds nothing useful and causes the test to break on the exact scenario the production code was designed to handle.

**Fix:** Remove line 26.

```python
@pytest.mark.integration
def test_generate_tailored_resume_returns_valid_latex(require_ollama):
    MINIMAL_JD = "Python backend engineer with REST API experience"
    result = generate_tailored_resume(MINIMAL_RESUME, MINIMAL_JD)
    assert result.content.lstrip().startswith("\\documentclass")
    assert result.content.rstrip().endswith("\\end{document}")
    assert "```" not in result.content
```

---

### CR-02: `_build_messages` missing `jd_analysis` parameter — unit test fails with `TypeError`, integration test exercises incomplete implementation

**File:** `tests/integration/test_llm_client.py:3` (cross-module finding)

**Issue:** `tests/unit/test_llm_client.py:222` calls `_build_messages("r", "jd", {"technologies": [], "requirements": [], "emphasis_areas": []})` and asserts that `<jd_analysis>` appears in the returned message. The production function `src/llm_client.py:26` defines `_build_messages(resume_text: str, job_description: str) -> list[dict]` — two parameters only, no `jd_analysis` argument, no `<jd_analysis>` tag in the output. This is a confirmed runtime failure:

```
TypeError: _build_messages() takes 2 positional arguments but 3 were given
```

The integration test in the reviewed file calls `generate_tailored_resume`, which internally calls `_build_messages`. It is exercising an implementation that is missing a documented capability. Any downstream consumer that expects `jd_analysis` enrichment in the prompt will not receive it.

**Fix:** Implement the `jd_analysis` optional parameter in `src/llm_client.py`:

```python
def _build_messages(
    resume_text: str,
    job_description: str,
    jd_analysis: dict | None = None,
) -> list[dict]:
    ...
    user_message = (
        "<job_description>\n"
        f"{job_description}\n"
        "</job_description>\n\n"
    )
    if jd_analysis is not None:
        import json as _json
        user_message += (
            "<jd_analysis>\n"
            f"{_json.dumps(jd_analysis, indent=2)}\n"
            "</jd_analysis>\n\n"
        )
    user_message += (
        "<resume>\n"
        f"{resume_text}\n"
        "</resume>"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
```

---

## Warnings

### WR-01: `ollama_available` fixture does not call `raise_for_status` — an HTTP 500 from Ollama is treated as "available"

**File:** `tests/conftest.py:9-12`

**Issue:** The session fixture catches `requests.ConnectionError` and `requests.Timeout` but does not call `response.raise_for_status()`. If Ollama is running but `/api/tags` returns a 5xx error, the fixture returns `True`, `require_ollama` does not skip, and `_check_ollama_health()` inside the test raises `RuntimeError`. This turns a situation that should produce a controlled SKIP into an unexpected ERROR, misleading CI output.

**Fix:**

```python
@pytest.fixture(scope="session")
def ollama_available() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        response.raise_for_status()
        return True
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
        return False
```

---

### WR-02: `require_ollama` fixture has default function scope while depending on a session-scoped fixture

**File:** `tests/conftest.py:15-18`

**Issue:** `ollama_available` is `scope="session"` (evaluated once for the entire test run) but `require_ollama` is implicitly `scope="function"` (default, re-invoked for each test). pytest permits a function-scoped fixture to consume a session-scoped one, but the asymmetry is a recognized source of bugs: if `require_ollama` is ever widened (e.g. to yield and perform cleanup), the scope mismatch will cause an error. Aligning both fixtures to `scope="session"` eliminates the inconsistency at zero cost.

**Fix:**

```python
@pytest.fixture(scope="session")
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")
```

---

## Info

### IN-01: `test_ollama_health_check_does_not_raise` has no explicit assertion — passes trivially if function becomes a no-op

**File:** `tests/integration/test_llm_client.py:14-16`

**Issue:** The test body is a bare call to `_check_ollama_health()` with no assertion. Pytest treats any non-raising call as a pass, so the implicit contract is "does not raise." This is valid as a smoke test, but if `_check_ollama_health` were refactored into a no-op by mistake, this test would still pass. The second test (`test_generate_tailored_resume_returns_valid_latex`) already exercises `_check_ollama_health` indirectly through `generate_tailored_resume`, making this test partially redundant. No action required, but consider whether the test earns its maintenance cost.

---

_Reviewed: 2026-06-07_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
