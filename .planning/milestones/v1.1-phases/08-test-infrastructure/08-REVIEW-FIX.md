---
phase: 08-test-infrastructure
fixed_at: 2026-06-04T00:00:00Z
review_path: .planning/phases/08-test-infrastructure/08-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 08: Code Review Fix Report

**Fixed at:** 2026-06-04T00:00:00Z
**Source review:** .planning/phases/08-test-infrastructure/08-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (CR-01, WR-01, WR-02, WR-03, WR-04)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: `requests.Timeout` not caught in `ollama_available` fixture

**Files modified:** `tests/conftest.py`
**Commit:** b2037ee
**Applied fix:** Added `requests.Timeout` to the except tuple in `ollama_available`. The catch clause now reads `except (requests.ConnectionError, requests.Timeout)` so a slow Ollama response triggers a clean skip instead of crashing the entire test session.

---

### WR-01: `unittest.TestCase` blocks pytest fixture injection in both test files

**Files modified:** `src/cli_test.py`, `src/llm_client_test.py`
**Commit:** 3c05bf7 (with merge resolution in 17f5e2c)
**Applied fix:** Converted all `unittest.TestCase` classes in both files to plain pytest-style free functions. All `self.assert*` calls replaced with `assert` statements; `self.assertRaises` replaced with `pytest.raises`. The `@patch` decorators are fully compatible with plain pytest functions and parameter ordering was preserved. This makes the conftest fixtures (including `require_ollama`) injectable into future tests in these files.

---

### WR-02: `test_success_prints_absolute_path` asserts only the label, not the path value

**Files modified:** `src/cli_test.py`
**Commit:** e79a090
**Applied fix:** Updated the assertion to verify both the label string `"Tailored resume written to:"` AND the resolved path `"/tmp/tailored_resume_20260529.tex"` appear on the same printed line. The test name now matches what the assertion actually checks.

---

### WR-03: `test_empty_jd_exits_1` does not patch `cli.read_resume`

**Files modified:** `src/cli_test.py`
**Commit:** d42da4b
**Applied fix:** Added `@patch("cli.read_resume")` decorator and `mock_read` parameter to `test_empty_jd_exits_1`, with `mock_read.return_value = "resume text"`. The test is now isolated from the call-order of `read_resume` in `cli.main` and will not fail with a `FileNotFoundError` if the production code is refactored.

---

### WR-04: `TestErrorHandling` tests do not mock `cli.run_guards`

**Files modified:** `src/cli_test.py`
**Commit:** 0675626
**Applied fix:** Added `@patch("cli.run_guards")` and corresponding `mock_guards` parameter to both `test_runtime_error_from_llm_exits_1` and `test_value_error_from_llm_exits_1`. Both tests now fully isolate the error-handling exit path from production `run_guards` execution.

---

_Fixed: 2026-06-04T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
