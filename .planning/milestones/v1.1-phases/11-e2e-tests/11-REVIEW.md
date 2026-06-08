---
phase: 11-e2e-tests
reviewed: 2026-06-08T00:00:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - tests/e2e/test_cli.py
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-06-08
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

Reviewed `tests/e2e/test_cli.py`, which contains two end-to-end tests that invoke the CLI via `subprocess.run`. Cross-referenced `tests/conftest.py`, `src/cli.py`, `src/config.py`, `src/guards.py`, `src/resume_writer.py`, and `pyproject.toml` for context.

No critical issues found. The test structure is fundamentally sound: both tests carry the registered `@pytest.mark.e2e` marker, the `require_ollama` skip guard is correctly applied only to the test that reaches Ollama, fixture scoping is correct, and the subprocess input/output plumbing is accurate. Two warnings and two info items follow.

## Warnings

### WR-01: `re.match` Without End Anchor on Filename Assertion

**File:** `tests/e2e/test_cli.py:49`

**Issue:** `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)` uses `re.match`, which anchors only at the start of the string, not the end. A filename such as `tailored_resume_20260608_123456.tex.bak` or `tailored_resume_20260608_123456.tex.gz` would satisfy this assertion, silently masking an incorrect output filename. While the `glob("tailored_resume_*.tex")` pre-filter reduces practical exposure today, the assertion's stated intent is to verify the exact filename format and `re.match` does not enforce that.

**Fix:**
```python
assert re.fullmatch(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)
```
`re.fullmatch` anchors at both ends, making the assertion match its stated intent.

---

### WR-02: Golden-Path Test Makes No Assertion on Output File Contents

**File:** `tests/e2e/test_cli.py:32-49`

**Issue:** `test_golden_path_exits_0_creates_output_file` verifies only that an output file exists with the right name. It never reads the file. The CLI could write an empty string, write `None`, or write a prose response with markdown fences, and this test would still pass. The core contract — "output contains valid LaTeX" — is unverified. A regression in `write_resume`, in the fence-stripping guard, or in the LLM response extraction would not be caught here.

**Fix:**
```python
content = output_files[0].read_text(encoding="utf-8")
assert content.strip(), "Output file must not be empty"
assert "\\documentclass" in content or "\\begin{document}" in content, \
    "Output file does not appear to contain LaTeX markup"
```

---

## Info

### IN-01: No `timeout` on `subprocess.run` — Suite Can Hang Indefinitely

**File:** `tests/e2e/test_cli.py:21` and `tests/e2e/test_cli.py:37`

**Issue:** Both `subprocess.run(...)` calls omit the `timeout` parameter. If the CLI subprocess hangs (Ollama stops responding mid-request, or the `input()` loop never terminates), the test process blocks forever with no way for pytest to interrupt it. The empty-JD test (line 21) is particularly notable: it is not guarded by `require_ollama` and runs in every environment, yet a future refactor that moves JD validation after a slow operation would cause it to block indefinitely.

**Fix:**
```python
result = subprocess.run(
    [sys.executable, CLI_PATH],
    input="END\n",
    capture_output=True,
    text=True,
    timeout=30,
)
```
Apply `timeout=30` to the empty-JD test and a larger value (e.g., `timeout=120`) to the golden-path test. `subprocess.TimeoutExpired` propagates as a test error, which is the correct failure mode.

---

### IN-02: No E2E Test for Missing Resume File Error Path

**File:** `tests/e2e/test_cli.py` (whole file)

**Issue:** The error path where `--resume` points to a nonexistent file is not covered in the e2e suite. `cli.py` catches `OSError` at line 60 and exits 1 with a message, but no test pins that contract from the outside. A refactor that removes the `OSError` handler or changes the exit code would go undetected.

**Fix:** Add a test:
```python
@pytest.mark.e2e
def test_missing_resume_exits_1_with_stderr_message(tmp_path):
    result = subprocess.run(
        [sys.executable, CLI_PATH,
         "--resume", str(tmp_path / "nonexistent.tex")],
        input="Some job description\nEND\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert result.stderr
```

---

_Reviewed: 2026-06-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
