---
phase: 09-unit-test-gaps
fixed_at: 2026-06-05T00:00:00Z
review_path: .planning/phases/09-unit-test-gaps/09-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 09: Code Review Fix Report

**Fixed at:** 2026-06-05T00:00:00Z
**Source review:** .planning/phases/09-unit-test-gaps/09-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### WR-01: Replace vacuous None assertion with call-site verification

**Files modified:** `tests/unit/test_llm_client.py`
**Commit:** 5543773
**Applied fix:** Replaced `MagicMock(status_code=200)` with a `spec=requests.Response` mock, set `raise_for_status.return_value = None`, removed the `result is None` assertion, and added `mock_get.assert_called_once()` and `mock_response.raise_for_status.assert_called_once()` to verify the health check actually calls the endpoint and calls `raise_for_status`.

### WR-02: Add match= parameter to all three error-condition pytest.raises calls

**Files modified:** `tests/unit/test_llm_client.py`
**Commit:** 5a557c9
**Applied fix:** Added `match="not reachable"` to the `ConnectionError` test, `match="timed out"` to the `Timeout` test, and `match="HTTP error"` to the `HTTPError` test. Each pattern matches the distinct message string constructed by the corresponding `except` branch in `_check_ollama_health`.

### WR-03: Add closing XML tag assertions to four prompt structure tests

**Files modified:** `tests/unit/test_llm_client.py`
**Commit:** 5225c45
**Applied fix:** Added `assert "</PERSONA>" in result[0]["content"]` to `test_build_messages_system_contains_persona_tag`, `assert "</CONSTRAINTS>" in result[0]["content"]` to `test_build_messages_system_contains_constraints_tag`, `assert "</job_description>" in result[1]["content"]` to `test_build_messages_user_contains_job_description_xml_tag`, and `assert "</resume>" in result[1]["content"]` to `test_build_messages_user_contains_resume_xml_tag`.

### WR-04: Add unit tests for _strip_fences, _validate_latex, and generate_tailored_resume

**Files modified:** `tests/unit/test_llm_client.py`
**Commit:** 3ed23ef
**Applied fix:** Updated the top-level import to include `_strip_fences`, `_validate_latex`, and `generate_tailored_resume`. Added 12 new tests:
- `test_strip_fences_removes_latex_fence`: verifies fenced latex input is unwrapped
- `test_strip_fences_no_op_on_clean_content`: verifies clean LaTeX is returned unchanged
- `test_strip_fences_removes_fence_without_language_tag`: verifies plain triple-backtick fence is stripped
- `test_validate_latex_raises_on_missing_documentclass`: verifies `ValueError` with `match="documentclass"`
- `test_validate_latex_raises_on_missing_end_document`: verifies `ValueError` with `match=r"end\{document\}"`
- `test_validate_latex_returns_text_on_valid_input`: verifies valid LaTeX is returned unchanged
- `test_generate_tailored_resume_truncated_raises`: verifies `done_reason=length` raises `RuntimeError` with `match="truncated"`
- `test_generate_tailored_resume_returns_tailor_result`: verifies happy path returns correct `TailorResult` with `fences_stripped=False`
- `test_generate_tailored_resume_fences_stripped_flag`: verifies fenced response sets `fences_stripped=True`
- `test_generate_tailored_resume_connection_error_raises`: verifies `ConnectionError` on POST raises `RuntimeError` with `match="Cannot connect"`
- `test_generate_tailored_resume_timeout_raises`: verifies `Timeout` on POST raises `RuntimeError` with `match="timed out"`
- `test_generate_tailored_resume_missing_content_key_raises`: verifies missing `message.content` key raises `RuntimeError` with `match="Unexpected Ollama response"`

All 24 tests in `test_llm_client.py` pass.

---

_Fixed: 2026-06-05T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
