# Phase 4: Output Reliability Guards - Pattern Map

**Mapped:** 2026-06-02
**Files analyzed:** 5 (2 new, 3 modified)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/guards.py` | utility | transform | `src/llm_client.py` (private helpers + re) | role-match |
| `src/guards_test.py` | test | request-response | `src/llm_client_test.py` | exact |
| `src/llm_client.py` | service | request-response | self (modification) | exact |
| `src/cli.py` | controller | request-response | self (modification) | exact |
| `src/cli_test.py` | test | request-response | self (modification) | exact |

---

## Pattern Assignments

### `src/guards.py` (utility, transform)

**Analog:** `src/llm_client.py` — private helpers pattern (`_strip_fences`, `_validate_latex`)

**Imports pattern** (`src/llm_client.py` lines 1–5):
```python
import re

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT
```
Guards.py uses only stdlib + local module, so:
```python
import re
import sys

from log_manager import logger
```

**Private-helper-plus-public-entry-point pattern** (`src/llm_client.py` lines 103–119):
```python
def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```\s*\w*\s*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _validate_latex(text: str) -> str:
    if not text.lstrip().startswith("\\documentclass"):
        raise ValueError(
            "LLM response does not start with \\documentclass — output is not valid LaTeX."
        )
    if "\\end{document}" not in text:
        raise ValueError(
            "LLM response does not contain \\end{document} — output may be truncated."
        )
    return text
```
Copy this pattern: three private `_check_*` functions each taking string args and returning `None`, with one public `run_guards()` that calls all three.

**Warning output pattern** (`src/log_manager.py` lines 7–9):
```python
def warning(self, message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)
```
Guards call `logger.warning(message)` — never `print(..., file=sys.stderr)` directly.

**Error channel pattern** (`src/cli.py` lines 42–43):
```python
print("Error: Job description cannot be empty.", file=sys.stderr)
sys.exit(1)
```
Guards use the same stderr channel but via `logger.warning()` and never call `sys.exit()`.

**Core guard structure to produce:**
```python
def _check_missing_sections(original: str, tailored: str) -> None:
    original_sections = re.findall(r'\\header\{([^}]+)\}', original)
    for section in original_sections:
        if section not in tailored:
            logger.warning(f'Section "{section}" missing from tailored output.')


def _check_format_violations(tailored: str, fences_stripped: bool) -> None:
    if fences_stripped:
        logger.warning("LLM returned markdown fences that were stripped from output.")
    if "```" in tailored:
        logger.warning("Tailored output contains inline code fences.")
    if re.search(r'(?m)^#{1,6} ', tailored):
        logger.warning("Tailored output contains markdown heading markers.")
    if re.search(r'\*\*\S[^*]*\S\*\*', tailored):
        logger.warning("Tailored output contains markdown bold markers.")


_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')


def _check_hallucinated_employers(original: str, tailored: str) -> None:
    original_employers = _EMPLOYER_PATTERN.findall(original)
    tailored_employers = _EMPLOYER_PATTERN.findall(tailored)
    for name, dates, title in original_employers:
        if (name, dates, title) not in tailored_employers:
            logger.warning(f'Employer "{name}" from original resume not found in tailored output.')


def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
```

---

### `src/guards_test.py` (test, request-response)

**Analog:** `src/llm_client_test.py` — exact match (same project, same unittest.TestCase pattern)

**File-level boilerplate** (`src/llm_client_test.py` lines 1–11):
```python
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

import requests

from llm_client import _strip_fences, _validate_latex, generate_tailored_resume
```
Guards test omits `requests` and imports from `guards` instead:
```python
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

from guards import run_guards
```

**TestCase class structure** (`src/llm_client_test.py` lines 13–28):
```python
class TestStripFences(unittest.TestCase):
    def test_strip_latex_fence(self):
        result = _strip_fences("```latex\n\\documentclass{article}\n```")
        self.assertEqual(result, "\\documentclass{article}")

    def test_no_op_on_clean_input(self):
        result = _strip_fences("\\documentclass{article}")
        self.assertEqual(result, "\\documentclass{article}")
```
One `TestCase` class per guard function. Use `self.assertEqual`, `self.assertIn`, `self.assertNotIn`.

**Stderr capture pattern** (`src/cli_test.py` lines 103–110):
```python
printed_lines = []
with patch("builtins.print", side_effect=lambda *a, **kw: printed_lines.append(a[0] if a else "")):
    main()

self.assertTrue(
    any("Tailoring resume" in line for line in printed_lines),
)
```
For guards tests, patch `log_manager.logger.warning` to capture calls:
```python
with patch("guards.logger") as mock_logger:
    run_guards(original, tailored, fences_stripped=False)
    mock_logger.warning.assert_not_called()
```

**File entry point** (`src/llm_client_test.py` lines 86–87):
```python
if __name__ == "__main__":
    unittest.main()
```
Copy verbatim.

---

### `src/llm_client.py` (service, request-response) — modification

**What changes:** `generate_tailored_resume()` return type changes from `str` to `TailorResult` NamedTuple. The `fences_stripped` boolean is computed before stripping and bundled into the return value.

**Current return type** (`src/llm_client.py` lines 122–124):
```python
def generate_tailored_resume(
    resume_text: str, job_description: str, model: str | None = None
) -> str:
```

**Current strip/validate block** (`src/llm_client.py` lines 163–168):
```python
    try:
        content = data["message"]["content"]
    except KeyError as exc:
        raise RuntimeError(f"Unexpected Ollama response structure: {data}") from exc
    content = _strip_fences(content)
    return _validate_latex(content)
```

**New additions at top of file** (after existing `import re`):
```python
from typing import NamedTuple


class TailorResult(NamedTuple):
    content: str
    fences_stripped: bool
```

**New strip/validate block** (replaces lines 163–168):
```python
    try:
        raw = data["message"]["content"]
    except KeyError as exc:
        raise RuntimeError(f"Unexpected Ollama response structure: {data}") from exc
    fences_stripped = raw.strip() != _strip_fences(raw)
    content = _strip_fences(raw)
    _validate_latex(content)
    return TailorResult(content=content, fences_stripped=fences_stripped)
```

**Existing error handling pattern to preserve** (`src/llm_client.py` lines 136–155):
```python
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.ConnectionError as exc:
        raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        raise RuntimeError(f"Ollama request timed out (timeout={TIMEOUT})") from exc
    except requests.HTTPError as exc:
        raise RuntimeError(f"Ollama returned HTTP error: {exc}") from exc
```
This block is unchanged — the refactor touches only the final lines.

---

### `src/cli.py` (controller, request-response) — modification

**What changes:** Import `run_guards` and `TailorResult`; change `content = generate_tailored_resume(...)` to `result = generate_tailored_resume(...)`; call `run_guards()` before `write_resume()`.

**Current import block** (`src/cli.py` lines 1–8):
```python
import argparse
import sys
from pathlib import Path

from config import BASE_RESUME_PATH, OUTPUT_DIR
from llm_client import generate_tailored_resume
from resume_reader import read_resume
from resume_writer import write_resume
```
Add to imports:
```python
from guards import run_guards
from llm_client import TailorResult, generate_tailored_resume
```

**Current try block** (`src/cli.py` lines 47–53):
```python
    try:
        resume_text = read_resume(resume_path)
        content = generate_tailored_resume(resume_text, job_description, model=args.model)
        output_path = write_resume(content, output_dir)
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```
Modified try block:
```python
    try:
        resume_text = read_resume(resume_path)
        result = generate_tailored_resume(resume_text, job_description, model=args.model)
        run_guards(resume_text, result.content, result.fences_stripped)
        output_path = write_resume(result.content, output_dir)
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```
The `except` clause and `sys.exit(1)` pattern are unchanged.

---

### `src/cli_test.py` (test, request-response) — modification

**What changes:** Five mock return values for `generate_tailored_resume` change from plain `str` to `TailorResult`. Also add patches for `run_guards`.

**Affected test locations** (all 5 occurrences of `mock_generate.return_value`):
- Line 20: `TestInputLoop.test_end_sentinel_breaks_loop`
- Line 38: `TestInputLoop.test_eof_treated_as_submission`
- Line 99: `TestSuccessPath.test_progress_message_printed`
- Line 122: `TestSuccessPath.test_success_prints_absolute_path`
- (Line 64–66 / 78–80: `mock_generate.side_effect = RuntimeError(...)` — these raise, not return, so they are unaffected)

**Current mock pattern** (`src/cli_test.py` lines 19–21):
```python
mock_read.return_value = "resume text"
mock_generate.return_value = "\\documentclass{article}\n\\end{document}"
mock_write.return_value = Path("/tmp/tailored_resume_test.tex")
```

**New mock pattern** (import `TailorResult` at top of `cli_test.py`, then):
```python
from llm_client import TailorResult

# in each test:
mock_generate.return_value = TailorResult(
    content="\\documentclass{article}\n\\end{document}",
    fences_stripped=False,
)
```

**Existing patch decorator pattern** (`src/cli_test.py` lines 12–16):
```python
@patch("sys.argv", ["resume-tailor"])
@patch("cli.write_resume")
@patch("cli.generate_tailored_resume")
@patch("cli.read_resume")
@patch("builtins.input")
def test_end_sentinel_breaks_loop(self, mock_input, mock_read, mock_generate, mock_write):
```
Add `@patch("cli.run_guards")` to each test that exercises the success path (where `run_guards` is now called). Add `mock_guards` parameter accordingly. Tests that use `side_effect = RuntimeError(...)` on `mock_generate` do not reach `run_guards` and do not need the additional patch.

---

## Shared Patterns

### Warning Output
**Source:** `src/log_manager.py` lines 7–9
**Apply to:** `src/guards.py` (all `_check_*` functions)
```python
def warning(self, message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)
```
Import as `from log_manager import logger` and call `logger.warning(message)`. Never use `print(..., file=sys.stderr)` directly in `guards.py`.

### Fatal Error / Raise-Not-Exit
**Source:** `src/llm_client.py` lines 11–14, 143–148
```python
    except requests.ConnectionError as exc:
        raise RuntimeError(f"Ollama is not reachable at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        raise RuntimeError("Ollama health check timed out") from exc
```
**Apply to:** `src/guards.py` — the inverse: guards NEVER raise. Any exception inside a `_check_*` function must be caught internally and converted to a `logger.warning()` call to satisfy GUARD-04.

### Error Handling in cli.py
**Source:** `src/cli.py` lines 51–53
```python
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```
**Apply to:** `src/cli.py` (modification) — this block is preserved exactly. Guards warnings go to stderr via `log_manager`, not through this exception path.

### sys.path Bootstrap in Tests
**Source:** `src/llm_client_test.py` lines 6–7 and `src/cli_test.py` lines 6–7
```python
sys.path.insert(0, str(Path(__file__).parent))
```
**Apply to:** `src/guards_test.py` — copy verbatim as the first executable line after imports.

### NamedTuple Return Value
**Source:** Python stdlib `typing.NamedTuple` (no existing analog in codebase — this is new)
**Apply to:** `src/llm_client.py` (new `TailorResult` class), `src/cli.py` (consumes `.content` and `.fences_stripped`), `src/cli_test.py` (mock return value)
```python
from typing import NamedTuple

class TailorResult(NamedTuple):
    content: str
    fences_stripped: bool
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/guards.py` (the guard logic itself) | utility | transform | No existing non-fatal warning module exists; closest structural analog is the private-helper pattern in `llm_client.py`, but the semantics (warn-not-raise) are new to the codebase |

---

## Metadata

**Analog search scope:** `/workspace/src/` (all `.py` files)
**Files scanned:** 6 (`cli.py`, `cli_test.py`, `llm_client.py`, `llm_client_test.py`, `log_manager.py`, `config.py`)
**Pattern extraction date:** 2026-06-02
