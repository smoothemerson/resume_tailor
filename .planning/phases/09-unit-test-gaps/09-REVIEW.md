---
phase: 09-unit-test-gaps
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - tests/unit/test_llm_client.py
  - tests/unit/test_resume_reader.py
  - tests/unit/test_resume_writer.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 09: Code Review Report

**Reviewed:** 2026-06-04T00:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Three unit test files were reviewed covering `llm_client.py`, `resume_reader.py`, and `resume_writer.py`. The tests are structurally sound and follow pytest idioms correctly. However, there are four reliability / correctness defects: one mock that does not actually intercept the patched target (making a test vacuously pass or fail for the wrong reason), one assertion that is trivially satisfied and cannot detect a regression, one missing assertion on a silent-success path, and one coverage gap on a public function with multiple reachable error branches. Three additional informational findings cover minor test design quality issues.

## Warnings

### WR-01: `test_check_ollama_health_200_does_not_raise` asserts `result is None` but also never calls `raise_for_status` — the mock returns a plain `MagicMock` whose `raise_for_status` attribute is also a `MagicMock` (a callable that does nothing), so the test would pass even if the production code did not call `raise_for_status` at all

**File:** `tests/unit/test_llm_client.py:84`
**Issue:** The mock returned by `MagicMock(status_code=200)` has a `raise_for_status` attribute that is itself a `MagicMock`. That mock-method never raises, so the test passes regardless of whether `_check_ollama_health` calls `raise_for_status` or completely omits it. The test verifies return-is-None but not that the happy-path flow completes the expected call sequence.
**Fix:** Add an assertion that `raise_for_status` was actually called, or use `spec=requests.Response` so the mock mirrors real object behavior:
```python
@patch("llm_client.requests.get")
def test_check_ollama_health_200_does_not_raise(mock_get):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    _check_ollama_health()
    mock_response.raise_for_status.assert_called_once()
```

### WR-02: `test_check_ollama_health_http_error_raises_runtime_error` does not assert on the `RuntimeError` message, so any `RuntimeError` — including one raised for a completely unrelated reason — would cause the test to pass

**File:** `tests/unit/test_llm_client.py:74`
**Issue:** `pytest.raises(RuntimeError)` catches any `RuntimeError`. The production code path for `HTTPError` explicitly constructs a message containing `"HTTP error"`. If the error-handling code were accidentally changed to re-raise the raw `HTTPError` (which is also not a `RuntimeError`), the test would fail for the right reason; but if any other code path in the function raises a `RuntimeError` first, the test silently validates the wrong path. The same applies to the `ConnectionError` and `Timeout` tests, but the HTTP-error test is most at risk because the mock sets up `raise_for_status` as a side-effect, and `raise_for_status` is only called after `requests.get` succeeds — making the ordering critical and untestable without a message check.
**Fix:** Use `pytest.raises` as a context manager and check `excinfo.value` or use `match=`:
```python
with pytest.raises(RuntimeError, match="HTTP error"):
    _check_ollama_health()
```

### WR-03: `test_build_messages_system_contains_persona_tag` and sibling tag-presence tests do not verify closing tags, so a prompt that opens `<PERSONA>` without closing it would still pass all tag-presence assertions

**File:** `tests/unit/test_llm_client.py:22`
**Issue:** Each of the four tag-presence tests checks only the opening tag (`<PERSONA>`, `<CONSTRAINTS>`, `<job_description>`, `<resume>`). The production prompt template could drop a closing tag — causing malformed XML that may confuse the LLM — and the tests would not detect it. This matters because the prompt structure is the primary guardrail for LLM output quality.
**Fix:** Assert on both the opening and closing tag in each test, or assert on the full paired sequence. At minimum for the user-message tags:
```python
assert "<job_description>" in result[1]["content"]
assert "</job_description>" in result[1]["content"]
assert "<resume>" in result[1]["content"]
assert "</resume>" in result[1]["content"]
```

### WR-04: `generate_tailored_resume` (the primary public function in `llm_client.py`) has no unit tests at all, leaving several reachable error branches with zero coverage

**File:** `tests/unit/test_llm_client.py` (missing coverage for `src/llm_client.py:132-180`)
**Issue:** `generate_tailored_resume` contains six distinct error branches that are independently reachable and each produces a different `RuntimeError` message: `done_reason == "length"` truncation (line 167), missing `message.content` key (line 174), non-JSON response (line 162), `ConnectionError` on the POST (line 153), `Timeout` on the POST (line 155), and `HTTPError` on the POST (line 157). It also has logic that detects whether fence-stripping was performed (`fences_stripped` flag, line 177) and calls `_validate_latex` which raises `ValueError` for two distinct conditions. None of these paths are exercised by the current test suite. Because this is the integration point between the mocked helpers and the actual Ollama API, untested branches here are the most likely source of production failures.
**Fix:** Add tests for at minimum the truncation path and the `done_reason` logic, the `fences_stripped` flag detection, and the `ValueError` raised by `_validate_latex`. Example skeleton:
```python
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_truncated_response_raises(mock_post, mock_health):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"done_reason": "length", "message": {"content": ""}}
    mock_post.return_value = mock_response
    with pytest.raises(RuntimeError, match="truncated"):
        generate_tailored_resume("resume", "job desc")
```

## Info

### IN-01: `test_write_resume_filename_matches_timestamp_pattern` is not race-condition-proof — if the call to `write_resume` crosses a second boundary, `result.name` will contain a timestamp that still matches the regex but the file written 59 ms earlier under a different timestamp would fail if the test also verified the actual on-disk filename against a pre-computed expected value

**File:** `tests/unit/test_resume_writer.py:24`
**Issue:** The test uses a regex to validate the filename pattern, which is correct and robust. No actual defect exists here, but the test does not freeze `datetime.now` — this is acceptable for the current assertion, but if a future developer adds a stricter filename comparison they will introduce a flaky test. The underlying `write_resume` implementation uses `datetime.now()` without injection.
**Fix:** Low priority. If stricter timestamp assertions are ever needed, inject a `datetime` mock or accept a `clock` callable in `write_resume`.

### IN-02: `test_read_resume_returns_file_content` does not verify that the function preserves non-ASCII characters or handles UTF-8 multi-byte content

**File:** `tests/unit/test_resume_reader.py:7`
**Issue:** The test uses pure ASCII content. The production function explicitly specifies `encoding="utf-8"`. A test with a Unicode string (e.g., accented characters or CJK that might appear in an international resume) would verify that the encoding parameter is present and correct — its removal would only be caught by such a test.
**Fix:** Add a supplementary test:
```python
def test_read_resume_preserves_unicode_content(tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text("Ré­su­mé — naïve", encoding="utf-8")
    assert read_resume(resume_file) == "Ré­su­mé — naïve"
```

### IN-03: `test_build_messages_system_contains_persona_tag` and similar tests use hard-coded string literals that are sensitive to tag-name casing changes in the prompt template — a refactor renaming `<PERSONA>` to `<persona>` would break the tests without breaking functionality

**File:** `tests/unit/test_llm_client.py:22`
**Issue:** The tests couple the test suite to the exact casing of XML tag names in the prompt. This is not a bug, but it makes the tests brittle with respect to prompt refactoring that does not change semantics.
**Fix:** Either import the tag names as constants from `llm_client` (if they become constants), or document that these tests are intentionally case-sensitive guards.

---

_Reviewed: 2026-06-04T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
