# Phase 13: Guard Expansion - Pattern Map

**Mapped:** 2026-06-09
**Files analyzed:** 2
**Analogs found:** 2 / 2

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/guards.py` (modified) | utility / guard | transform | `src/guards.py` itself (existing guard functions) | exact |
| `tests/unit/test_guards.py` | test | request-response | `tests/unit/test_resume_writer.py` + `src/guards_test.py` | exact |

## Pattern Assignments

### `src/guards.py` — add `_check_technology_substitution` and `_check_protected_sections`

**Analog:** `src/guards.py` existing guard functions (same file — same role, same data flow)

**Imports pattern** (`src/guards.py` lines 1-6):
```python
import re
import sys

from log_manager import logger

_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
```
New guards need no new imports — `re`, `logger`, and `_EMPLOYER_PATTERN` are already present.

**Never-raise wrapper pattern** (`src/guards.py` lines 9-16 and 33-44):
```python
def _check_missing_sections(original: str, tailored: str) -> None:
    try:
        # ... all logic here ...
    except Exception as exc:
        logger.warning(f"Section check failed: {exc}")


def _check_hallucinated_employers(original: str, tailored: str) -> None:
    try:
        # ... all logic here ...
    except Exception as exc:
        logger.warning(f"Employer check failed: {exc}")
```
Copy this shell verbatim for both new guards; only the function name and the failure-message string change.

**Section-boundary regex pattern** (`src/guards.py` lines 11-12):
```python
original_sections = re.findall(r'\\header\{([^}]+)\}', original)
```
For section *content* extraction (needed in new guards) extend this into a `re.search` with lookahead and `re.DOTALL`:
```python
# Derived from the pattern above — produces body text between two \header{} calls
pattern = rf'\\header\{{{re.escape(section_name)}\}}(.*?)(?=\\header\{{|$)'
m = re.search(pattern, text, re.DOTALL)
return m.group(1) if m else None
```

**`_EMPLOYER_PATTERN` reuse** (`src/guards.py` lines 6, 35-43):
```python
_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')

# In _check_hallucinated_employers — reuse the same findall + set-diff idiom:
original_employers = _EMPLOYER_PATTERN.findall(original)
tailored_employers = _EMPLOYER_PATTERN.findall(tailored)
for name, dates, title in original_employers:
    if (name, dates, title) not in tailored_employers:
        logger.warning(f'Employer "{name}" from original resume not found in tailored output.')
```
In `_check_protected_sections`, convert to `set()` for O(1) diff:
```python
original_headers = set(_EMPLOYER_PATTERN.findall(original))
tailored_headers = set(_EMPLOYER_PATTERN.findall(tailored))
for header in original_headers - tailored_headers:
    logger.warning(f'Employer header changed or removed: "{header[0]}"')
```

**`run_guards()` integration point** (`src/guards.py` lines 47-50):
```python
def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
    # Add two new lines here:
    # _check_technology_substitution(original_text, tailored_text)
    # _check_protected_sections(original_text, tailored_text)
```

---

### `tests/unit/test_guards.py` (new test file)

**Analog 1:** `tests/unit/test_resume_writer.py` — pytest function style, `@pytest.mark.unit`, direct import from module
**Analog 2:** `src/guards_test.py` — `patch("guards.logger")` pattern, `call_args_list` assertion idiom, `run_guards(None, None)` never-raise test

**Imports pattern** (`tests/unit/test_resume_writer.py` lines 1-6 + `src/guards_test.py` lines 1-8):
```python
import pytest
from unittest.mock import patch

from guards import _check_technology_substitution, _check_protected_sections, run_guards
```
No `sys.path.insert` needed — `pyproject.toml` has `pythonpath = ["src"]` and `--import-mode=importlib`.

**Test function skeleton** (`tests/unit/test_resume_writer.py` lines 9-11):
```python
@pytest.mark.unit
def test_write_resume_creates_output_directory(tmp_path):
    ...
```
Every test function in the new file must be decorated with `@pytest.mark.unit` — no exceptions.

**`patch("guards.logger")` mock pattern** (`src/guards_test.py` lines 14-17 and 46-50):
```python
with patch("guards.logger") as mock_logger:
    run_guards(original, tailored)
    mock_logger.warning.assert_called_once_with('Section "Skills" missing from tailored output.')
```
For tests where multiple warnings are expected, use `call_args_list` + `any()` (not `assert_called_once_with`):
```python
with patch("guards.logger") as mock_logger:
    run_guards("", tailored, fences_stripped=True)
    calls = [str(c) for c in mock_logger.warning.call_args_list]
    self.assertTrue(any("LLM returned markdown fences" in c for c in calls))
```
New test file uses the same `call_args_list` idiom but in pytest function style (no `self`):
```python
with patch("guards.logger") as mock_logger:
    _check_technology_substitution(original, tailored)
    calls = [str(c) for c in mock_logger.warning.call_args_list]
    assert any("Java" in c for c in calls)
    assert any("Go" in c for c in calls)
```

**Never-raise test pattern** (`src/guards_test.py` lines 102-107):
```python
class TestRunGuardsNeverRaises(unittest.TestCase):
    def test_run_guards_empty_strings_no_exception(self):
        run_guards("", "")

    def test_run_guards_malformed_input_no_exception(self):
        run_guards(None, None)
```
In pytest function style (new file):
```python
@pytest.mark.unit
def test_technology_substitution_malformed_input_no_raise():
    _check_technology_substitution(None, None)  # must not raise

@pytest.mark.unit
def test_protected_sections_empty_strings_no_raise():
    _check_protected_sections("", "")  # must not raise
```

**Inline LaTeX fixture pattern** (`src/guards_test.py` lines 13-14, 46-47):
```python
original = "\\header{Skills}\n\\header{Experience}"
tailored = "\\header{Experience}"
```
Use raw-string literals for test fixtures that contain LaTeX backslash sequences:
```python
original = r"\header{Skills}" + "\nPython, Java\n" + r"\header{Education}"
tailored = r"\header{Skills}" + "\nPython, Go\n" + r"\header{Education}"
```

---

## Shared Patterns

### Never-Raise Guard Wrapper
**Source:** `src/guards.py` lines 9-16 (and 19-30, 33-44)
**Apply to:** Both `_check_technology_substitution` and `_check_protected_sections`
```python
def _check_NAME(original: str, tailored: str) -> None:
    try:
        # all logic
    except Exception as exc:
        logger.warning(f"NAME check failed: {exc}")
```
All three existing guards follow this pattern without variation. Do not add any extra `if original is None` guards — the `try/except` is sufficient and is the established convention.

### `patch("guards.logger")` Test Target
**Source:** `src/guards_test.py` line 15
**Apply to:** Every test in `tests/unit/test_guards.py` that asserts warning behavior
```python
with patch("guards.logger") as mock_logger:
    ...
    calls = [str(c) for c in mock_logger.warning.call_args_list]
    assert any("expected text" in c for c in calls)
```
The mock target string is `"guards.logger"` — the module-level name where the logger object lives, not the logger's own module path.

### `@pytest.mark.unit` Decorator
**Source:** `tests/unit/test_resume_writer.py` lines 9, 17, 23, 29
**Apply to:** Every test function in `tests/unit/test_guards.py`
The pytest config has `--strict-markers`, so any test missing the marker or using an unregistered marker will cause a collection error.

### `call_args_list` + `any()` Assertion Pattern
**Source:** `src/guards_test.py` lines 46-50
**Apply to:** All multi-warning tests (substitution case, removal-only case, addition-only case, protected-section per-element tests)
```python
calls = [str(c) for c in mock_logger.warning.call_args_list]
assert any("expected substring" in c for c in calls)
```
Use `mock_logger.warning.assert_not_called()` only when the guard must be fully silent (identical content, no-skills-section).

---

## No Analog Found

All files have close analogs. No entries in this section.

---

## Metadata

**Analog search scope:** `src/`, `tests/unit/`
**Files scanned:** `src/guards.py`, `src/guards_test.py`, `tests/unit/test_resume_writer.py`, `tests/unit/test_jd_analyzer.py`
**Pattern extraction date:** 2026-06-09
