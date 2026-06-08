---
phase: 11-e2e-tests
reviewed: 2026-06-08T00:00:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - tests/e2e/test_cli.py
findings:
  critical: 0
  warning: 4
  info: 1
  total: 5
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-06-08
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

`tests/e2e/test_cli.py` contains two E2E tests exercising the CLI via `subprocess.run`. The empty-JD sad-path test is well-structured and passes. The golden-path happy test exercises the full Ollama-backed flow but has reliability and completeness gaps: no subprocess timeout (infinite hang risk), no validation of output file contents, and a weaker filename regex than intended. The `require_ollama` fixture in `tests/conftest.py` is correctly wired for the happy-path test but has a type annotation inconsistency.

---

## Warnings

### WR-01: No `timeout` on `subprocess.run` — test suite can hang indefinitely

**File:** `tests/e2e/test_cli.py:21` and `tests/e2e/test_cli.py:37`

**Issue:** Both `subprocess.run(...)` calls omit the `timeout` parameter. If the CLI subprocess hangs (e.g., Ollama stops responding mid-request, or the `input()` loop never terminates), the test process blocks forever with no way for pytest to interrupt it. This is especially dangerous for the empty-JD test (line 21), which is not guarded by `require_ollama` — it runs in every CI environment regardless of Ollama availability.

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
Add `timeout=30` (or a reasonable ceiling) to both calls. Wrap in `pytest.raises(subprocess.TimeoutExpired)` if testing timeout behavior specifically; otherwise let the `TimeoutExpired` propagate as a test error, which is the correct failure mode.

---

### WR-02: Golden-path test never validates output file contents

**File:** `tests/e2e/test_cli.py:47-49`

**Issue:** After the golden-path run, the test checks that exactly one `tailored_resume_*.tex` file exists and that its name matches a timestamp pattern. It never reads the file to verify the content is valid LaTeX (or even non-empty). The CLI could write an empty file, write literal `None`, or write a prose error message and this test would still pass. The core contract — "output contains LaTeX" — is unverified.

**Fix:**
```python
output_file = output_files[0]
content = output_file.read_text(encoding="utf-8")
assert content.strip(), "Output file is empty"
assert "\\documentclass" in content or "\\begin{document}" in content, \
    "Output does not appear to be valid LaTeX"
```
A minimal structural check (`\\documentclass` or `\\begin{document}` present) is sufficient to catch the most common failure modes (empty output, prose leakage, markdown fences).

---

### WR-03: `re.match` instead of `re.fullmatch` for filename pattern assertion

**File:** `tests/e2e/test_cli.py:49`

**Issue:** `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)` only anchors at the start of the string. Any filename that starts with the expected pattern but has additional characters appended (e.g., `tailored_resume_20240101_120000.tex.bak`) would pass the assertion. While the `glob("tailored_resume_*.tex")` pre-filter reduces practical exposure, the assertion's stated intent is to verify the exact filename format and `re.match` does not enforce that.

**Fix:**
```python
assert re.fullmatch(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)
```
`re.fullmatch` anchors at both ends, making the assertion match its intent precisely.

---

### WR-04: `require_ollama` fixture type annotation is misleading

**File:** `tests/conftest.py:17`

**Issue:** The fixture is declared as `def require_ollama(ollama_available: bool) -> None`. The parameter `ollama_available` is a pytest fixture, not a raw `bool` argument. Annotating it as `bool` implies it can be passed any boolean at call sites — it cannot; pytest resolves it by name from the fixture registry. If a developer attempts to call `require_ollama(False)` directly (e.g., in a unit test for the fixture itself), the annotation misleads them into thinking it is valid Python. More critically, a type-checker running `mypy` will flag callers that pass the fixture value as a boolean argument.

**Fix:**
```python
@pytest.fixture(scope="session")
def require_ollama(ollama_available: bool) -> None:  # type annotation is pytest-idiomatic; acceptable
    if not ollama_available:
        pytest.skip("Ollama not available")
```
The annotation is technically harmless in runtime pytest use, but removing the `bool` hint from the parameter (leaving it unannotated) avoids confusion:
```python
@pytest.fixture(scope="session")
def require_ollama(ollama_available) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")
```

---

## Info

### IN-01: `CLI_PATH` computed via magic `parents[2]` index with no guard

**File:** `tests/e2e/test_cli.py:8`

**Issue:** `CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"` hard-codes the assumption that `test_cli.py` lives exactly two levels below the project root (`tests/e2e/test_cli.py` → `tests/e2e/` → `tests/` → root). If the file is ever moved, `parents[2]` silently resolves to a different directory with no assertion failure at import time — the failure only surfaces as a confusing `FileNotFoundError` inside the subprocess. There is also no existence check to fail fast at collection time.

**Fix:**
```python
_PROJECT_ROOT = Path(__file__).parents[2]
CLI_PATH = _PROJECT_ROOT / "src" / "cli.py"
assert CLI_PATH.exists(), f"CLI not found at {CLI_PATH}"
```
Adding the `assert` at module level causes pytest collection to fail immediately with a clear message if the path is wrong, rather than letting bad subprocess calls fail with opaque errors at runtime.

---

_Reviewed: 2026-06-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
