# Phase 07: JD Keyword Match Summary - Pattern Map

**Mapped:** 2026-06-08
**Files analyzed:** 3 (1 new module, 1 new test file, 1 modified integration file)
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/keyword_matcher.py` | utility/display module | transform | `src/diff_view.py` | exact |
| `src/keyword_matcher_test.py` | test | — | `src/diff_view_test.py` | exact |
| `src/cli.py` (modified) | CLI entry point | request-response | `src/cli.py` itself (current state) | self |

## Pattern Assignments

### `src/keyword_matcher.py` (utility/display, transform)

**Analog:** `src/diff_view.py`

**Imports pattern** (`src/diff_view.py` lines 1-2):
```python
import difflib
import sys
```
For `keyword_matcher.py`, substitute:
```python
import re
import sys
```
No project-local imports needed. No `from` imports — module is self-contained.

**TTY gate pattern** (`src/diff_view.py` lines 32-34):
```python
def show_diff(original: str, tailored: str) -> None:
    if not sys.stdout.isatty():
        return
```
`show_keyword_match` copies this exact guard as first statement in the public function. Return immediately — no exception, no output.

**Never-raises pattern** — `diff_view.py` does not use `try/except` at the top level because it has no external calls. `keyword_matcher.py` DOES wrap the body in `try/except Exception` because matching logic is nontrivial. Pattern from `src/guards.py` (each private function, lines 9-16):
```python
def _check_missing_sections(original: str, tailored: str) -> None:
    try:
        original_sections = re.findall(r'\\header\{([^}]+)\}', original)
        for section in original_sections:
            if f'\\header{{{section}}}' not in tailored:
                logger.warning(f'Section "{section}" missing from tailored output.')
    except Exception as exc:
        logger.warning(f"Section check failed: {exc}")
```
For `keyword_matcher.py`, the `try/except Exception` wraps the public function body (after the TTY check) and silently returns on any exception — no logging, matching a non-fatal display module:
```python
def show_keyword_match(analysis: dict, tailored_text: str) -> None:
    if not sys.stdout.isatty():
        return
    try:
        # ... matching logic ...
    except Exception:
        return
```

**Module-level constant pattern** — project uses module-level constants in `src/config.py` (plain uppercase names). Apply same to `STOP_WORDS`:
```python
STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "to", "for",
    "with", "is", "are", "be", "on", "at",
})
```
Placed at module top, after imports, before function definitions.

**Private helper naming convention** — `src/diff_view.py` uses `_normalize` and `_colorize` (single underscore prefix). `src/guards.py` uses `_check_missing_sections`, `_check_format_violations`, `_check_hallucinated_employers`. Follow the same `_verb_noun` snake_case pattern:
- `_collect_keywords(analysis: dict) -> list[str]`
- `_match_keywords(keywords: list[str], tailored_text: str) -> list[str]`
- `_print_summary(matched: list[str], total: int) -> None`

**`re` usage pattern** — `src/guards.py` lines 1, 6, 11-12 show how `re` is used in this codebase:
```python
import re
_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
# ...
original_sections = re.findall(r'\\header\{([^}]+)\}', original)
```
For keyword matching, use `re.compile()` per keyword inside the loop (compile then `.search()`), consistent with the codebase's explicitness:
```python
pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b", re.IGNORECASE)
if pattern.search(tailored_lower):
    matched.append(kw)
```

**Analysis dict access pattern** — `src/jd_analyzer.py` lines 38-43 defines the canonical dict shape:
```python
required_keys = {"technologies", "requirements", "emphasis_areas"}
# ...
return {k: parsed[k] for k in required_keys}
```
Access all three keys via `.get(field, [])` to pool keywords:
```python
for field in ("technologies", "requirements", "emphasis_areas"):
    raw.extend(analysis.get(field, []))
```

**Print output pattern** — `src/cli.py` uses bare `print(...)` for all stdout user-facing output (lines 27-31, 59). No `flush=True` for post-processing display (only progress messages use `flush=True`). Match summary uses:
```python
print(f"Keyword match: {len(matched)}/{total}")
if matched:
    print(f"  {', '.join(matched)}")
```

---

### `src/keyword_matcher_test.py` (test)

**Analog:** `src/diff_view_test.py`

**Imports pattern** (`src/diff_view_test.py` lines 1-6):
```python
import sys
import unittest
from unittest.mock import patch

from diff_view import show_diff
```
For `keyword_matcher_test.py`, substitute:
```python
import sys
import unittest
from unittest.mock import patch

from keyword_matcher import show_keyword_match
```

**Test class organization pattern** (`src/diff_view_test.py` lines 8-96) — group tests by behavior in `unittest.TestCase` subclasses with descriptive class names:
```python
class TestShowDiffTTYGate(unittest.TestCase): ...
class TestShowDiffNormalization(unittest.TestCase): ...
class TestShowDiffColors(unittest.TestCase): ...
class TestShowDiffNeverRaises(unittest.TestCase): ...
```
Mirror structure for `keyword_matcher_test.py`:
- `TestShowKeywordMatchTTYGate`
- `TestShowKeywordMatchMatching`
- `TestShowKeywordMatchStopWords`
- `TestShowKeywordMatchOutput`
- `TestShowKeywordMatchNeverRaises`

**TTY simulation pattern** (`src/diff_view_test.py` lines 9-14):
```python
def test_suppressed_when_not_tty(self):
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = False
        with patch("builtins.print") as mock_print:
            show_diff("original", "tailored changed")
            mock_print.assert_not_called()
```
Copy verbatim — replace `show_diff` with `show_keyword_match` and supply an `analysis` dict.

**TTY=True pattern** (`src/diff_view_test.py` lines 16-22):
```python
def test_shows_diff_on_tty(self):
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        printed = []
        with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
            show_diff("line 1\nline 2", "line 1\nline 2 changed")
        self.assertTrue(any("line 2 changed" in line for line in printed))
```
Apply same `printed = []` + `side_effect` capture idiom to test that matched keywords appear in output.

**Never-raises pattern** (`src/diff_view_test.py` lines 83-92):
```python
class TestShowDiffNeverRaises(unittest.TestCase):
    def test_empty_strings_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            show_diff("", "")

    def test_not_tty_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            show_diff("", "")
```
Extend for `keyword_matcher_test.py`: pass `None` analysis fields, empty lists, malformed values — none should raise.

**Module footer pattern** (`src/diff_view_test.py` line 96):
```python
if __name__ == "__main__":
    unittest.main()
```
Include verbatim at end of `keyword_matcher_test.py`.

**pytest marker** — `src/cli_test.py` uses `@pytest.mark.unit` on every test. Check whether `diff_view_test.py` and `guards_test.py` also use it (they do not — no marker). `keyword_matcher_test.py` should follow the same style as its direct analog `diff_view_test.py`: no marker.

---

### `src/cli.py` (modified — integration point)

**Analog:** `src/cli.py` current state (lines 1-66)

**Current import block** (`src/cli.py` lines 1-11):
```python
import argparse
import sys
from pathlib import Path

from config import BASE_RESUME_PATH, OUTPUT_DIR
from diff_view import show_diff
from guards import run_guards
from jd_analyzer import analyze_job_description
from llm_client import TailorResult, generate_tailored_resume
from resume_reader import read_resume
from resume_writer import write_resume
```
Add one import in alphabetical order among the project-local `from` imports:
```python
from keyword_matcher import show_keyword_match
```
Slot between `from jd_analyzer import ...` and `from llm_client import ...`.

**Integration call site** (`src/cli.py` lines 56-59 — current state):
```python
run_guards(resume_text, result.content, result.fences_stripped)
output_path = write_resume(result.content, output_dir)
show_diff(resume_text, result.content)
print(f"Tailored resume written to: {output_path.resolve()}")
```
After integration (new lines between `show_diff` and `print`):
```python
run_guards(resume_text, result.content, result.fences_stripped)
output_path = write_resume(result.content, output_dir)
show_diff(resume_text, result.content)
if analysis is not None:
    show_keyword_match(analysis, result.content)
print(f"Tailored resume written to: {output_path.resolve()}")
```

**`cli_test.py` patching concern** — `test_generate_called_with_analysis_dict_when_analysis_succeeds` (`src/cli_test.py` lines 241-259) mocks `analyze_job_description` to return a non-None dict. After integration, `show_keyword_match` will be called. In the test environment, `sys.stdout.isatty()` returns `False`, so `show_keyword_match` exits immediately — the test likely passes without adding `@patch("cli.show_keyword_match")`. Verify by running the full suite; add the patch only if a test fails. All other existing tests mock `analyze_job_description` returning `None`, so they are unaffected.

---

## Shared Patterns

### TTY Gate
**Source:** `src/diff_view.py` lines 33-34
**Apply to:** `src/keyword_matcher.py` public function
```python
if not sys.stdout.isatty():
    return
```
First statement in the public entry point, before any logic.

### Never-Raises (try/except Exception)
**Source:** `src/guards.py` — each private helper wraps in `try/except Exception`. For `keyword_matcher.py`, the public function wraps its full body (after TTY check):
```python
try:
    ...
except Exception:
    return
```
Silent failure — no logging, no re-raise. A keyword match failure must not abort the CLI run.

### No Comments or Docstrings
**Source:** `src/diff_view.py`, `src/guards.py`, `src/jd_analyzer.py` — none contain inline comments, module-level comments, or docstrings.
**Apply to:** Both `src/keyword_matcher.py` and `src/keyword_matcher_test.py`. Names and types are sufficient per CLAUDE.md conventions.

### Type Hints on Public Functions
**Source:** `src/diff_view.py` line 32, `src/guards.py` line 47, `src/jd_analyzer.py` line 46 — all public functions carry full type annotations:
```python
def show_diff(original: str, tailored: str) -> None:
def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
def analyze_job_description(job_description: str, model: str | None = None) -> dict | None:
```
Apply same to:
```python
def show_keyword_match(analysis: dict, tailored_text: str) -> None:
```
Private helpers also annotated fully.

### frozenset for O(1) Constant Lookup
**Source:** Decision D-04 + stdlib built-in. No codebase analog — this is the first `frozenset` constant in the project. Declare at module level after imports, before functions, with explicit type annotation:
```python
STOP_WORDS: frozenset[str] = frozenset({...})
```

## No Analog Found

All three files have strong analogs. No entries required here.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | — |

## Metadata

**Analog search scope:** `src/` directory (all 13 files)
**Files scanned:** `diff_view.py`, `guards.py`, `jd_analyzer.py`, `cli.py`, `diff_view_test.py`, `cli_test.py`
**Pattern extraction date:** 2026-06-08
