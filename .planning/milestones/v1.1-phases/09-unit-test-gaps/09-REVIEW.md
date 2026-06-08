---
phase: 09-unit-test-gaps
reviewed: 2026-06-04T12:00:00Z
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

**Reviewed:** 2026-06-04T12:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Three unit test files were reviewed covering `llm_client.py`, `resume_reader.py`, and `resume_writer.py`. All 18 tests currently pass. However, three of those passing tests are either vacuous (the assertion cannot fail regardless of what production code does), missing call-site verification (the happy path is not actually exercised), or structurally incomplete (only opening XML tags are checked, closing tags are invisible to the test). Additionally, the primary public function `generate_tailored_resume` — which contains six distinct reachable error branches plus `_validate_latex` and `_strip_fences` logic — has zero unit test coverage, leaving the most critical production code path entirely untested.

## Warnings

### WR-01: `test_check_ollama_health_200_does_not_raise` is vacuously passing — `result is None` is always true regardless of what the production code does

**File:** `tests/unit/test_llm_client.py:83-88`
**Issue:** `_check_ollama_health` has no `return` statement; it always implicitly returns `None`. The test asserts `result is None`, which passes unconditionally. Furthermore, the mock returned by `MagicMock(status_code=200)` auto-creates a `raise_for_status` attribute that is a `MagicMock` callable — it never raises. This means the test passes even if the entire body of `_check_ollama_health` is replaced with `pass`. The test provides zero regression protection: removing the `raise_for_status()` call from the production code, or removing the health check entirely, leaves this test green.
**Fix:**
```python
@patch("llm_client.requests.get")
def test_check_ollama_health_200_does_not_raise(mock_get):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    _check_ollama_health()
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
```

### WR-02: Error-condition tests do not use `match=` — any `RuntimeError` from any code path satisfies `pytest.raises(RuntimeError)`, masking misdirected error handling

**File:** `tests/unit/test_llm_client.py:59-80`
**Issue:** All three error tests (`ConnectionError`, `Timeout`, `HTTPError`) use bare `pytest.raises(RuntimeError)` without a `match=` parameter. The production code constructs distinct messages for each error type (lines 19, 21, 23 of `llm_client.py`). Without `match=`, a test passes if any `RuntimeError` is raised from anywhere inside `_check_ollama_health` — including an accidental `raise RuntimeError("wrong reason")`. This makes the tests structurally correct but semantically weak: they verify exception type but not which error branch was triggered.
**Fix:**
```python
with pytest.raises(RuntimeError, match="not reachable"):
    _check_ollama_health()

with pytest.raises(RuntimeError, match="timed out"):
    _check_ollama_health()

with pytest.raises(RuntimeError, match="HTTP error"):
    _check_ollama_health()
```

### WR-03: XML tag tests check only opening tags — a dropped closing tag in the prompt template is undetectable

**File:** `tests/unit/test_llm_client.py:22-54`
**Issue:** Four tests assert the presence of opening XML tags (`<PERSONA>`, `<CONSTRAINTS>`, `<job_description>`, `<resume>`) but none checks the corresponding closing tags. The production prompt contains all four closing tags (`</PERSONA>`, `</CONSTRAINTS>`, `</job_description>`, `</resume>`) at lines 34, 81, 100, and 103 of `llm_client.py`. If a closing tag were accidentally deleted during a prompt refactor, every tag-presence test would still pass. Malformed XML in the system prompt is likely to degrade LLM compliance with the output constraints.
**Fix:** Add closing-tag assertions in the existing tests or alongside them:
```python
def test_build_messages_system_contains_persona_tag():
    result = _build_messages("resume text", "job description")
    assert "<PERSONA>" in result[0]["content"]
    assert "</PERSONA>" in result[0]["content"]

def test_build_messages_user_contains_job_description_xml_tag():
    result = _build_messages("resume text", "job description")
    assert "<job_description>" in result[1]["content"]
    assert "</job_description>" in result[1]["content"]

def test_build_messages_user_contains_resume_xml_tag():
    result = _build_messages("resume text", "job description")
    assert "<resume>" in result[1]["content"]
    assert "</resume>" in result[1]["content"]
```

### WR-04: `generate_tailored_resume`, `_strip_fences`, and `_validate_latex` have zero unit test coverage

**File:** `tests/unit/test_llm_client.py` (missing; covers `src/llm_client.py:112-180`)
**Issue:** The three untested functions contain the most complex and failure-prone logic in the codebase:
- `_strip_fences` uses two regex substitutions to strip markdown fences; edge cases include fences with no language tag, fences with trailing spaces, and input with no fences.
- `_validate_latex` raises `ValueError` on two distinct conditions (missing `\documentclass` and missing `\end{document}`); neither condition is exercised.
- `generate_tailored_resume` has six independently reachable error branches: `ConnectionError` on POST (line 153), `Timeout` on POST (line 155), `HTTPError` on POST (line 157), `JSONDecodeError` (line 162), `done_reason == "length"` truncation (line 167), and missing `message.content` key (line 174). It also computes the `fences_stripped` flag whose logic (`raw.strip() != _strip_fences(raw)`) is not tested for correctness.

None of these code paths are exercised by any test in the suite. This is the primary entry point called by the CLI; all of its error paths map directly to user-visible failure modes.

**Fix:** Add tests for the pure functions first (no mocking needed):
```python
def test_strip_fences_removes_latex_fence():
    from llm_client import _strip_fences
    fenced = "```latex\n\\documentclass{article}\n\\end{document}\n```"
    assert _strip_fences(fenced) == "\\documentclass{article}\n\\end{document}"

def test_strip_fences_no_op_on_clean_content():
    from llm_client import _strip_fences
    content = "\\documentclass{article}\n\\end{document}"
    assert _strip_fences(content) == content

def test_validate_latex_raises_on_missing_documentclass():
    from llm_client import _validate_latex
    with pytest.raises(ValueError, match="documentclass"):
        _validate_latex("not latex at all\n\\end{document}")

def test_validate_latex_raises_on_missing_end_document():
    from llm_client import _validate_latex
    with pytest.raises(ValueError, match="end{document}"):
        _validate_latex("\\documentclass{article}\ntruncated")
```
Then add mocked tests for `generate_tailored_resume`:
```python
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

## Info

### IN-01: `test_read_resume_returns_file_content` uses ASCII-only content — removing the `encoding="utf-8"` parameter from `read_resume` would not be caught

**File:** `tests/unit/test_resume_reader.py:7-10`
**Issue:** The test fixture writes and reads back `"\\documentclass{article}"`, which is pure ASCII and will round-trip correctly under any encoding. The production function explicitly specifies `encoding="utf-8"` (line 6 of `resume_reader.py`). A developer removing that parameter would not be caught by this test. Resumes can legitimately contain accented characters.
**Fix:** Add a supplementary test with non-ASCII content:
```python
def test_read_resume_preserves_unicode_content(tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text("Résumé — naïve café", encoding="utf-8")
    assert read_resume(resume_file) == "Résumé — naïve café"
```

### IN-02: `test_write_resume_filename_matches_timestamp_pattern` does not freeze time — the test is currently safe but fragile under future extension

**File:** `tests/unit/test_resume_writer.py:24-26`
**Issue:** `write_resume` calls `datetime.now()` without any injection point. The test uses a regex (`\d{8}_\d{6}`) which is robust against second-boundary crossings. No defect in the current assertion. However, if a future developer adds a stricter assertion (e.g., asserting the exact timestamp matches a pre-computed value), the test will become flaky. The underlying production function provides no clock-injection seam.
**Fix:** Low priority. If stricter timestamp assertions are ever needed, `write_resume` should accept an optional `clock` callable parameter defaulting to `datetime.now`.

### IN-03: `test_build_messages_*` tests import only `_build_messages` and `_check_ollama_health` from `llm_client` — the `generate_tailored_resume` symbol is not imported and could be renamed or removed without any test failing

**File:** `tests/unit/test_llm_client.py:5`
**Issue:** The import on line 5 covers only the two helper functions. The public API of the module (`generate_tailored_resume`, `TailorResult`) is not imported in the test file, meaning import-time errors or signature changes in those symbols are not caught by this test module.
**Fix:** Once tests for `generate_tailored_resume` are added (per WR-04), ensure the import line includes it:
```python
from llm_client import _build_messages, _check_ollama_health, generate_tailored_resume
```

---

_Reviewed: 2026-06-04T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
