---
phase: 08-test-infrastructure
reviewed: 2026-06-02T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - pyproject.toml
  - tests/conftest.py
  - src/cli_test.py
  - src/llm_client_test.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-06-02T00:00:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Four files reviewed: `pyproject.toml` (test tooling config), `tests/conftest.py` (shared fixtures), `src/cli_test.py` (CLI unit tests), and `src/llm_client_test.py` (LLM client unit tests).

The overall test structure is sound — mock targets are correctly named, `@patch` decorator-to-parameter ordering is correct throughout, and the Ollama fixture design matches the session/function scope architecture described in the research phase. However, one critical reliability defect exists in `conftest.py` (uncaught `requests.Timeout` crashes the test session), and several warnings exist around test isolation, coverage gaps, and a misleading test name.

The documented project pitfall regarding `unittest.TestCase` incompatibility with pytest fixtures is realized: both `src/cli_test.py` and `src/llm_client_test.py` use `unittest.TestCase`, which blocks any future use of `require_ollama` or `tmp_path` fixtures within those files.

---

## Structural Findings (fallow)

No structural pre-pass was provided for this review.

---

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: `requests.Timeout` not caught in `ollama_available` fixture — session crash instead of skip

**File:** `tests/conftest.py:8-12`
**Issue:** The `ollama_available` fixture catches only `requests.ConnectionError`. If Ollama is bound and listening but responds slowly (i.e., the 3-second timeout fires), `requests.get` raises `requests.Timeout`, which is NOT a subclass of `requests.ConnectionError`. This exception propagates unhandled through the session-scoped fixture, crashing the entire test session with a fixture error rather than returning `False` and triggering a clean skip. This defeats the entire purpose of the guard fixture.

The `requests` exception hierarchy is: `requests.exceptions.Timeout` → `requests.exceptions.ConnectionError` is a sibling, not a parent. `Timeout` does NOT inherit from `ConnectionError`.

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
**Issue:** All test classes in both files extend `unittest.TestCase`. As documented in the project's own `PITFALLS.md` (line 572), `unittest.TestCase` methods cannot receive pytest fixtures as parameters. This means that if any test in these files ever needs `require_ollama`, `tmp_path`, or any other pytest fixture, the test class must be rewritten. The project's research already flagged this pattern as a blocker for integration test extensibility, yet both newly added test files repeat it. The current unit tests work fine, but the structural choice locks out the fixture-based skip pattern from ever being used in these files.

**Fix:** New tests should use plain pytest functions, not `unittest.TestCase`. For existing tests, migration is low-risk since `unittest.TestCase` assertions (`assertEqual`, `assertRaises`, etc.) can be replaced one-for-one with `assert` statements and `pytest.raises`. Example conversion:

```python
# Before (unittest.TestCase — cannot use pytest fixtures)
class TestInputLoop(unittest.TestCase):
    @patch("sys.argv", ["resume-tailor"])
    def test_end_sentinel_breaks_loop(self, ...):
        self.assertIn("line one", call_args[0][1])

# After (plain pytest — fixture-compatible)
@patch("sys.argv", ["resume-tailor"])
def test_end_sentinel_breaks_loop(...):
    assert "line one" in call_args[0][1]
```

### WR-02: `test_success_prints_absolute_path` asserts only the label, not the path value

**File:** `src/cli_test.py:120-134`
**Issue:** The test name asserts that the output includes the absolute path, but the assertion at line 133 only checks for `"Tailored resume written to:"` — the label prefix. It does not verify that the resolved path string appears in the output. The `output_path.resolve.return_value` is configured as `Path("/tmp/tailored_resume_20260529.tex")`, but the assertion would pass even if `cli.py` printed `"Tailored resume written to: None"` or omitted the path entirely. The test name is actively misleading.

**Fix:**
```python
self.assertTrue(
    any(
        "Tailored resume written to:" in line and "/tmp/tailored_resume_20260529.tex" in line
        for line in printed_lines
    )
)
```

### WR-03: `test_empty_jd_exits_1` does not patch `cli.read_resume` — couples test to filesystem

**File:** `src/cli_test.py:46-55`
**Issue:** The test for empty job description does not patch `cli.read_resume`. In `cli.py`, `read_resume` is called AFTER the empty-check guard, so the test happens to pass because `sys.exit(1)` fires before `read_resume` is reached. However, this relies on implicit ordering of statements in `main()`. If `cli.py` is ever refactored to call `read_resume` before collecting job description input (e.g., for eager validation of the resume path), this test will fail with a `FileNotFoundError` rather than a clean assertion error, producing a confusing failure message. The test should be self-contained.

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

### WR-04: `_strip_fences` called twice in `generate_tailored_resume` — redundant computation and divergence risk

**File:** `src/llm_client.py:173-174` (referenced from `src/llm_client_test.py`)
**Issue:** `generate_tailored_resume` calls `_strip_fences(raw)` twice — once to compute `fences_stripped` and once to get `content`. This is not tested for correctness at the unit level: no test verifies that `content` equals `_strip_fences(raw)` when fences ARE present (i.e., the result in `TailorResult.content` is the stripped version, not the raw). The test `test_content_field_is_stripped_latex` (line 127-137) does cover this via the full `generate_tailored_resume` call, but there is no test that isolates the interaction between `fences_stripped` detection and content assignment.

More importantly, calling `_strip_fences` twice on the same input is fragile: if the function were ever made non-idempotent (e.g., if future regex changes strip more than one layer of fences), the `fences_stripped` flag and the actual `content` could diverge because they are computed from separate calls. The correct pattern is to call `_strip_fences` once, store the result, then compare:

```python
# In generate_tailored_resume (src/llm_client.py:173-175):
content = _strip_fences(raw)
fences_stripped = raw.strip() != content
_validate_latex(content)
return TailorResult(content=content, fences_stripped=fences_stripped)
```

The tests should verify this pattern holds and cover the production code path — currently `test_fences_stripped_true_when_raw_had_fences` and `test_content_field_is_stripped_latex` test this through the full function but not in isolation.

---

## Info

### IN-01: No test markers applied — tests are not selectable by `-m unit`

**File:** `src/cli_test.py` (all tests), `src/llm_client_test.py` (all tests)
**Issue:** `pyproject.toml` registers `unit`, `integration`, and `e2e` markers specifically so tests can be selected with `-m unit` or excluded with `-m "not integration"`. None of the tests in `cli_test.py` or `llm_client_test.py` carry a `@pytest.mark.unit` decorator. This means running `pytest -m unit` returns zero collected tests, giving developers false confidence that all unit tests ran. The marker system is essentially inert.

**Fix:** Add `@pytest.mark.unit` to each test class or test function. For `unittest.TestCase` classes, apply at the class level:
```python
@pytest.mark.unit
class TestInputLoop(unittest.TestCase):
    ...
```

### IN-02: `require_ollama` fixture defined but never consumed

**File:** `tests/conftest.py:15-18`
**Issue:** `require_ollama` is defined but no test in the codebase declares it as a parameter. The `tests/integration/` and `tests/e2e/` directories exist but are empty. The fixture is correct and well-designed, but it is currently dead code. This is expected scaffolding for future tests, but worth noting.

**Fix:** No immediate action required. When integration tests are added to `tests/integration/`, they should declare `require_ollama` as a parameter. Ensure the fixture remains in `tests/conftest.py` (not `src/`) so it is discoverable by all test directories.

### IN-03: `pyproject.toml` entry point does not match documented package namespace

**File:** `pyproject.toml:10`
**Issue:** The CLAUDE.md technology stack specifies the entry point as `resume-tailor = "resume_tailor.cli:main"` (namespaced under `resume_tailor`), but the actual `pyproject.toml` uses `resume-tailor = "cli:main"` (bare module). With `sources = ["src"]`, hatchling installs `src/cli.py` as `site-packages/cli.py` — a top-level unnamespaced module. This is a collision risk if the wheel is installed in an environment with any other package that exports a top-level `cli` module.

**Fix:** Either restructure the source layout to use a package (`src/resume_tailor/cli.py`) and update the entry point to `resume-tailor = "resume_tailor.cli:main"`, or explicitly document that the bare-module layout is intentional and update CLAUDE.md to match.

---

_Reviewed: 2026-06-02T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
