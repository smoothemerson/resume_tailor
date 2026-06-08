# Phase 5: Diff View - Pattern Map

**Mapped:** 2026-06-04
**Files analyzed:** 4 (2 new, 2 modified)
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/diff_view.py` | utility | transform | `src/guards.py` | exact (single-concern module, one public entry point, private helpers, never raises) |
| `src/diff_view_test.py` | test | — | `src/guards_test.py` | exact (unittest.TestCase + mock.patch pattern) |
| `src/cli.py` | controller | request-response | `src/cli.py` itself | self (3-line insertion into existing flow) |
| `pyproject.toml` | config | — | `pyproject.toml` itself | self (add one entry to existing `include` list) |

## Pattern Assignments

### `src/diff_view.py` (utility, transform)

**Analog:** `src/guards.py`

**Imports pattern** (`src/guards.py` lines 1-5):
```python
import re
import sys

from log_manager import logger
```

For `diff_view.py`, replace `re` and `log_manager` with `difflib`:
```python
import difflib
import sys
```

**Module-level constants pattern** — no analog in `guards.py` (it uses no constants). Use module-level ANSI escape literals (raw literals, no `colorama`):
```python
_GREEN = "\033[32m"
_RED = "\033[31m"
_RESET = "\033[0m"
```

**Single-concern public entry point pattern** (`src/guards.py` lines 47-50):
```python
def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
```

`show_diff()` follows the same shape — public function delegates to private helpers, returns `None`, never raises:
```python
def show_diff(original: str, tailored: str) -> None:
    if not sys.stdout.isatty():
        return
    norm_orig = _normalize(original)
    norm_tail = _normalize(tailored)
    diff = list(difflib.unified_diff(
        norm_orig.splitlines(),
        norm_tail.splitlines(),
        fromfile="original",
        tofile="tailored",
        lineterm="",
    ))
    if not diff:
        return
    for line in diff:
        print(_colorize(line))
```

**Private helper pattern** (`src/guards.py` lines 9-16 — defensive try/except in each helper):
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

`diff_view.py` private helpers `_normalize()` and `_colorize()` are pure transforms (no I/O, no logging) — they do not need try/except. The never-raises contract is honored because `show_diff()` itself is called outside the try/except in `cli.py`.

**`_normalize()` implementation** (verified algorithm, RESEARCH.md lines 174-189):
```python
def _normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    result: list[str] = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result)
```

**`_colorize()` implementation** — critical: check `+++`/`---` prefix before `+`/`-` to avoid coloring header lines (RESEARCH.md lines 204-213):
```python
def _colorize(line: str) -> str:
    if line.startswith("+") and not line.startswith("+++"):
        return _GREEN + line + _RESET
    if line.startswith("-") and not line.startswith("---"):
        return _RED + line + _RESET
    return line
```

---

### `src/diff_view_test.py` (test)

**Analog:** `src/guards_test.py`

**Test file header pattern** (`src/guards_test.py` lines 1-8):
```python
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

from guards import run_guards
```

For `diff_view_test.py`, omit `sys.path.insert` (pytest handles `pythonpath = ["src"]` via `pyproject.toml`). The existing `cli_test.py` uses `import pytest` + `from unittest.mock import MagicMock, patch` without a `sys.path.insert`. Use that style:
```python
import sys
from unittest.mock import patch

from diff_view import show_diff
```

**TestCase class structure** (`src/guards_test.py` lines 11-38 — group by behavior, one class per concern):
```python
class TestCheckMissingSections(unittest.TestCase):
    def test_missing_section_triggers_warning(self):
        ...
    def test_no_missing_sections_no_warning(self):
        ...
```

**`patch` for TTY detection** — `sys.stdout.isatty` is checked at call time inside `show_diff()`, so patch `diff_view.sys.stdout` or use `patch("sys.stdout")`. From RESEARCH.md lines 408-411:
```python
def test_suppressed_when_not_tty():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = False
        with patch("builtins.print") as mock_print:
            show_diff("original", "tailored changed")
            mock_print.assert_not_called()
```

**Captured-print assertion pattern** (`src/cli_test.py` lines 114-115):
```python
printed_lines = []
with patch("builtins.print", side_effect=lambda *a, **kw: printed_lines.append(a[0] if a else "")):
    main()
```

Apply same pattern for `test_shows_diff_on_tty`:
```python
def test_shows_diff_on_tty():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        printed = []
        with patch("builtins.print", side_effect=lambda *a: printed.append(a[0])):
            show_diff("line 1\nline 2", "line 1\nline 2 changed")
        assert any("line 2 changed" in line for line in printed)
```

**Never-raises guard test** (`src/guards_test.py` lines 102-107):
```python
class TestRunGuardsNeverRaises(unittest.TestCase):
    def test_run_guards_empty_strings_no_exception(self):
        run_guards("", "")
    def test_run_guards_malformed_input_no_exception(self):
        run_guards(None, None)
```

Apply to `diff_view_test.py` — `show_diff("", "")` with TTY mocked to True must not raise.

**`if __name__ == "__main__":` footer** (`src/guards_test.py` line 113-114):
```python
if __name__ == "__main__":
    unittest.main()
```

---

### `src/cli.py` (controller, request-response — modification)

**Analog:** `src/cli.py` itself (3-line insertion)

**Import block to extend** (`src/cli.py` lines 1-9):
```python
import argparse
import sys
from pathlib import Path

from config import BASE_RESUME_PATH, OUTPUT_DIR
from guards import run_guards
from llm_client import TailorResult, generate_tailored_resume
from resume_reader import read_resume
from resume_writer import write_resume
```

Add one import line following the existing alphabetical-by-module style:
```python
from diff_view import show_diff
```

**Integration insertion point** (`src/cli.py` lines 48-57 — current state):
```python
    try:
        resume_text = read_resume(resume_path)
        result = generate_tailored_resume(resume_text, job_description, model=args.model)
        run_guards(resume_text, result.content, result.fences_stripped)
        output_path = write_resume(result.content, output_dir)
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Tailored resume written to: {output_path.resolve()}")
```

After modification (insert `show_diff` call OUTSIDE the try/except, between it and the final print):
```python
    try:
        resume_text = read_resume(resume_path)
        result = generate_tailored_resume(resume_text, job_description, model=args.model)
        run_guards(resume_text, result.content, result.fences_stripped)
        output_path = write_resume(result.content, output_dir)
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    show_diff(resume_text, result.content)
    print(f"Tailored resume written to: {output_path.resolve()}")
```

**Why outside the try/except:** `show_diff()` is non-fatal per the raise-not-exit pattern. `run_guards()` is also non-fatal but sits inside the try/except because it was already there; `show_diff()` is new and must follow the pattern of not letting a display concern kill the confirmation print.

---

### `pyproject.toml` (config — modification)

**Analog:** `pyproject.toml` itself

**Wheel include block** (`pyproject.toml` lines 16-25 — current state):
```toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

After modification (add `src/diff_view.py` in alphabetical order):
```toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/diff_view.py",
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

---

## Shared Patterns

### Never-Raises Contract
**Source:** `src/guards.py` (every helper wrapped in `try/except Exception`)
**Apply to:** `src/diff_view.py` — `show_diff()` must not raise under any input. Pure transform helpers `_normalize()` and `_colorize()` cannot raise on valid string input; no try/except needed inside them. If extra defensive wrapping is desired, wrap the body of `show_diff()` in `try/except Exception` with a silent return.

### Module-Per-Concern Structure
**Source:** `src/guards.py`, `src/resume_reader.py`
**Apply to:** `src/diff_view.py` — one file, one public function, private helpers prefixed with `_`, no global mutable state, no side-effects at import time.

### `patch("builtins.print")` for stdout assertion in tests
**Source:** `src/cli_test.py` lines 114-115 and 21
**Apply to:** `src/diff_view_test.py` — all tests that verify print output or absence of output use `patch("builtins.print")`. Pair with `patch("sys.stdout")` to control `isatty()` return value.

### Alphabetical import ordering
**Source:** `src/cli.py` lines 5-9 (stdlib first, then local modules alphabetically)
**Apply to:** `src/cli.py` import addition — insert `from diff_view import show_diff` after `from config import ...` and before `from guards import ...` to maintain alphabetical order.

---

## No Analog Found

All files have clear analogs in the codebase. No entries.

---

## Metadata

**Analog search scope:** `/workspace/src/` (all `.py` files: `cli.py`, `cli_test.py`, `config.py`, `guards.py`, `guards_test.py`, `llm_client.py`, `llm_client_test.py`, `log_manager.py`, `resume_reader.py`, `resume_writer.py`); `/workspace/pyproject.toml`
**Files scanned:** 11
**Pattern extraction date:** 2026-06-04
