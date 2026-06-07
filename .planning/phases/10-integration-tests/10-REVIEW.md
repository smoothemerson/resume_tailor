---
phase: 10-integration-tests
reviewed: 2026-06-07T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - tests/integration/test_llm_client.py
  - pyproject.toml
findings:
  critical: 1
  warning: 2
  info: 0
  total: 3
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-06-07
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Phase 10 added two integration tests that exercise `llm_client` against a live Ollama instance and skip gracefully when Ollama is unavailable. The `pyproject.toml` received `--import-mode=importlib` to resolve the basename collision between `tests/unit/test_llm_client.py` and `tests/integration/test_llm_client.py`. Unit tests were confirmed to still pass under importlib mode. The skip mechanism (`require_ollama` / `ollama_available` fixtures) works correctly. One critical defect exists: a test assertion that will falsely fail on correct production behavior from the live LLM. Two warnings cover an error class gap in the skip guard fixture and a documentation-accuracy issue in a test assertion message.

## Critical Issues

### CR-01: Integration test asserts `fences_stripped is False` — fails on correct model behavior

**File:** `tests/integration/test_llm_client.py:26`

**Issue:** The test hard-codes `assert result.fences_stripped is False`. This assertion means the test passes only when the live LLM returns clean LaTeX with no markdown fences. However, the entire point of `_strip_fences` and the `fences_stripped` flag is to handle the common case where an LLM wraps output in triple-backtick fences despite being instructed not to. When (not if) the model returns fenced LaTeX, `generate_tailored_resume` correctly strips the fences, sets `fences_stripped = True`, and returns valid content — but the test reports a failure even though the behavior is correct and intentional. This is a BLOCKER because it inverts the contract: a correctly-handling call is reported as broken, while the only way to satisfy the assertion is for the model to behave perfectly, which defeats the purpose of having fence-stripping at all.

The `assert "```" not in result.content` assertion on line 25 already verifies that no fences remain in the output. Line 26 adds nothing useful and makes the test unreliable.

**Fix:**

Remove line 26 entirely. The absence of fences in the output content (line 25) is the meaningful contract. Whether the model emitted fences that were stripped is an implementation detail, not a correctness requirement at the integration boundary.

```python
@pytest.mark.integration
def test_generate_tailored_resume_returns_valid_latex(require_ollama):
    MINIMAL_JD = "Python backend engineer with REST API experience"
    result = generate_tailored_resume(MINIMAL_RESUME, MINIMAL_JD)
    assert result.content.lstrip().startswith("\\documentclass")
    assert result.content.rstrip().endswith("\\end{document}")
    assert "```" not in result.content
    # fences_stripped is intentionally not asserted — the model may or may not
    # emit fences; stripping them is correct behavior, not a test failure
```

---

## Warnings

### WR-01: `ollama_available` fixture does not catch `HTTPError` — skip guard can fail with an ERROR instead of SKIP

**File:** `tests/conftest.py:9-12` (relied upon by the new integration tests)

**Issue:** The `ollama_available` session fixture catches only `requests.ConnectionError` and `requests.Timeout`. If Ollama is running but `/api/tags` returns an HTTP error (e.g. 500, 503), `requests.get()` succeeds without raising, so `ollama_available` returns `True`. The subsequent call to `_check_ollama_health()` inside the test then raises `RuntimeError` — turning what should be a controlled SKIP into an unexpected ERROR. The test appears to "fail" rather than skip, which misleads CI.

Note: `conftest.py` was not changed in phase 10, but the two new integration tests directly depend on this fixture behaving as a reliable skip guard.

**Fix:**

Catch `requests.HTTPError` in the availability probe, or use `response.raise_for_status()` before returning `True`:

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

### WR-02: `test_ollama_health_check_does_not_raise` does not assert anything — a silent pass masks a broken function

**File:** `tests/integration/test_llm_client.py:14-16`

**Issue:** The test body is a single call to `_check_ollama_health()` with no assertion. The implicit contract is "does not raise," which pytest does enforce (any exception is a failure). However, the test name claims it "does not raise," which is the only thing being tested. If `_check_ollama_health` were changed to a no-op that returns immediately (e.g. due to a refactor), this test would still pass, providing false confidence that Ollama is reachable and the health-check path was exercised.

A more reliable formulation verifies that Ollama actually responded: either by checking the return value (the function currently returns `None`, so that is not directly useful) or by verifying that the subsequent `generate_tailored_resume` call succeeds — but the latter is already covered by the second test. At minimum, the test should be documented as a smoke test, or `_check_ollama_health` should be changed to return a value (e.g. model list) that can be positively asserted.

**Fix:**

Either add a meaningful assertion or acknowledge the smoke-test nature explicitly. The simplest improvement: change `_check_ollama_health` to return the parsed tags response so callers can verify it. Alternatively, confirm that the function calls `requests.get` exactly once by having the test check a side-effect — but since this is against the live service, the most practical fix is to at minimum assert that Ollama reports at least one available model:

```python
@pytest.mark.integration
def test_ollama_health_check_does_not_raise(require_ollama):
    # Smoke test: verifies _check_ollama_health completes without raising
    # against a live Ollama instance. Correctness of the function body is
    # covered by unit tests in tests/unit/test_llm_client.py.
    _check_ollama_health()
```

The convention `no comments or docstrings` in CLAUDE.md applies to production source code; test files are not excluded from this rule per the text of CONVENTIONS.md. Since the project convention is no comments, the alternative fix is to rename the test to make the scope explicit, or accept the current form as-is and address WR-01 and WR-02 together by reconsidering whether this test adds value beyond the second test.

---

_Reviewed: 2026-06-07_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
