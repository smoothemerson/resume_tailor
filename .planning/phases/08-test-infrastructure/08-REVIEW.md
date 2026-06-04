---
phase: 08-test-infrastructure
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - pyproject.toml
  - src/cli_test.py
  - src/llm_client_test.py
  - tests/conftest.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-06-04T00:00:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Four files reviewed: `pyproject.toml` (test tooling config), `tests/conftest.py` (shared fixtures), `src/cli_test.py` (CLI unit tests), and `src/llm_client_test.py` (LLM client unit tests). All 22 tests currently pass.

The overall test structure is sound — mock targets are correctly named, `@patch` decorator-to-parameter ordering is correct throughout, and the Ollama fixture design uses an appropriate session/function scope split. One critical reliability defect exists in `conftest.py`: an uncaught `requests.Timeout` crashes the entire test session instead of triggering a clean skip. Several warnings cover test isolation brittle-ness, a misleading test assertion, and missing coverage of error paths that are explicitly handled in production code.

---

## Structural Findings (fallow)

No structural pre-pass was provided for this review.

---

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: `requests.Timeout` not caught in `ollama_available` fixture — session crash instead of skip

**File:** `tests/conftest.py:7-12`
**Issue:** The `ollama_available` session-scoped fixture catches only `requests.ConnectionError`. `requests.Timeout` is an independent sibling under `requests.exceptions.RequestException` — confirmed: `issubclass(requests.Timeout, requests.ConnectionError)` returns `False`. If Ollama is listening but responds slowly (i.e., the 3-second timeout fires), `requests.get` raises `requests.Timeout` which propagates unhandled through the fixture, crashing the entire test session with a fixture error rather than returning `False` and allowing `require_ollama` to skip cleanly. This defeats the entire purpose of the guard fixture and will manifest in any CI environment where Ollama is absent but a port is bound.

**Fix:**
```python
@pytest.fixture(scope="session")
def ollama_available() -> bool:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False
```

---

## Warnings

### WR-01: `unittest.TestCase` blocks pytest fixture injection in both test files

**File:** `src/cli_test.py:9,58,90` and `src/llm_client_test.py:9,27,46,82`
**Issue:** All test classes in both files extend `unittest.TestCase`. `unittest.TestCase` methods cannot receive pytest fixtures as parameters — pytest silently ignores extra parameters, they are not injected. This means that if any test in these files ever needs `require_ollama`, `tmp_path`, or any other pytest fixture, the entire test class must be rewritten. All the scaffolding in `tests/conftest.py` (including the `require_ollama` guard) is structurally inaccessible from the test files as written.

**Fix:** New tests should use plain pytest functions, not `unittest.TestCase`. For existing tests, migration is low-risk — `unittest.TestCase` assertions map one-for-one to `assert` statements and `pytest.raises`. Example:

```python
# Before (blocks fixture injection)
class TestInputLoop(unittest.TestCase):
    def test_end_sentinel_breaks_loop(self, ...):
        self.assertIn("line one", call_args[0][1])

# After (fixture-compatible)
def test_end_sentinel_breaks_loop(...):
    assert "line one" in call_args[0][1]
```

### WR-02: `test_success_prints_absolute_path` asserts only the label, not the path value

**File:** `src/cli_test.py:120-134`
**Issue:** The test name claims it verifies that the absolute path is printed, but the assertion at line 133 checks only for `"Tailored resume written to:"` — the label prefix. It does not verify that the resolved path string appears in the output. `output_path.resolve.return_value` is configured as `Path("/tmp/tailored_resume_20260529.tex")` but the assertion would pass even if `cli.py` printed `"Tailored resume written to: None"` or omitted the path value entirely. The test name is actively misleading.

**Fix:**
```python
self.assertTrue(
    any(
        "Tailored resume written to:" in line and "/tmp/tailored_resume_20260529.tex" in line
        for line in printed_lines
    )
)
```

### WR-03: `test_empty_jd_exits_1` does not patch `cli.read_resume` — implicitly depends on call order

**File:** `src/cli_test.py:46-55`
**Issue:** The test for empty job description does not patch `cli.read_resume`. In current `cli.py`, `read_resume` is called inside the `try` block that runs AFTER the empty-check guard, so the test passes because `sys.exit(1)` fires first. However, this relies on the implicit ordering of statements in `main()`. If `cli.py` is ever refactored to call `read_resume` before collecting job-description input (e.g., for eager resume-path validation), this test will fail with a `FileNotFoundError` rather than a clean assertion error, producing a confusing failure message that obscures the regression.

**Fix:**
```python
@patch("sys.argv", ["resume-tailor"])
@patch("cli.read_resume")
@patch("builtins.input")
def test_empty_jd_exits_1(self, mock_input, mock_read):
    mock_input.side_effect = ["END"]
    mock_read.return_value = "resume text"

    with self.assertRaises(SystemExit) as cm:
        with patch("builtins.print"):
            main()

    self.assertEqual(cm.exception.code, 1)
```

### WR-04: `TestErrorHandling` tests do not mock `cli.run_guards` — brittle under refactor

**File:** `src/cli_test.py:63` and `src/cli_test.py:78`
**Issue:** `test_runtime_error_from_llm_exits_1` and `test_value_error_from_llm_exits_1` patch `cli.read_resume` and `cli.generate_tailored_resume` but do not patch `cli.run_guards`. Currently `generate_tailored_resume` raises before `run_guards` is reached, so the tests pass. If `cli.main` is ever refactored to call `run_guards` before or independently of `generate_tailored_resume`, the un-mocked `run_guards` will execute against real production dependencies and these tests will fail for the wrong reason, masking the original intent of verifying the error-handling exit path.

**Fix:** Add `@patch("cli.run_guards")` and corresponding parameter to both test methods:
```python
@patch("sys.argv", ["resume-tailor"])
@patch("cli.generate_tailored_resume")
@patch("cli.read_resume")
@patch("builtins.input")
@patch("cli.run_guards")
def test_runtime_error_from_llm_exits_1(self, mock_guards, mock_input, mock_read, mock_generate):
    ...
```

---

## Info

### IN-01: No test markers applied — `pytest -m unit` collects zero tests

**File:** `src/cli_test.py` (all tests), `src/llm_client_test.py` (all tests)
**Issue:** `pyproject.toml` registers `unit`, `integration`, and `e2e` markers (lines 37-40) specifically so tests can be selected with `-m unit` or excluded with `-m "not integration"`. None of the tests in `cli_test.py` or `llm_client_test.py` carry a `@pytest.mark.unit` decorator. Running `pytest -m unit` returns zero collected tests. The marker system is entirely inert.

**Fix:** Add `@pytest.mark.unit` to each test class. For `unittest.TestCase` classes, apply at the class level:
```python
import pytest

@pytest.mark.unit
class TestInputLoop(unittest.TestCase):
    ...
```

### IN-02: `require_ollama` fixture defined but never consumed

**File:** `tests/conftest.py:15-18`
**Issue:** `require_ollama` is defined but no test in the codebase declares it as a parameter. The `tests/integration/` and `tests/e2e/` directories exist and are empty. The fixture is correct and well-designed, but it is currently dead code. This is expected scaffolding, but given that `unittest.TestCase` (WR-01) structurally blocks fixture injection in the two existing test files, `require_ollama` would also be blocked from `cli_test.py` and `llm_client_test.py` even if needed there.

**Fix:** No immediate action required. When integration tests are added, they should use plain pytest functions (not `unittest.TestCase`) and declare `require_ollama` as a parameter. Track this with the WR-01 migration.

### IN-03: `pyproject.toml` entry point installs a bare top-level `cli` module — namespace collision risk

**File:** `pyproject.toml:10`
**Issue:** The entry point is `resume-tailor = "cli:main"` with `sources = ["src"]`. Hatchling installs `src/cli.py` as `site-packages/cli.py` — a top-level unnamespaced module. Any other installed package that exports a top-level `cli` module will conflict. `CLAUDE.md` specifies the correct namespaced form `resume-tailor = "resume_tailor.cli:main"`, but the actual implementation uses the flat layout. The inconsistency is a maintenance trap for future packaging work.

**Fix:** Either restructure to `src/resume_tailor/cli.py` and update the entry point to `resume-tailor = "resume_tailor.cli:main"`, or explicitly document that the bare-module flat layout is intentional and update `CLAUDE.md` to match. Either choice is acceptable; the inconsistency is the defect.

---

_Reviewed: 2026-06-04T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
