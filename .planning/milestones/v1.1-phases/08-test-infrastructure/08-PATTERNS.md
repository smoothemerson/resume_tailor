# Phase 8: Test Infrastructure - Pattern Map

**Mapped:** 2026-06-02
**Files analyzed:** 4 (2 modified, 1 new, 1 config section added)
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pyproject.toml` (add `[tool.pytest.ini_options]`) | config | — | `pyproject.toml` existing sections | exact |
| `src/cli_test.py` (remove sys.path hack) | test | request-response | `src/llm_client_test.py` | exact |
| `src/llm_client_test.py` (remove sys.path hacks + unused imports) | test | request-response | `src/cli_test.py` | exact |
| `tests/conftest.py` (new file) | config/fixture | request-response | `src/llm_client_test.py` (requests usage) | role-match |

## Pattern Assignments

### `pyproject.toml` — add `[tool.pytest.ini_options]` section

**Analog:** `pyproject.toml` existing tool sections

**Existing pyproject.toml structure** (lines 1-33 — full file):
```toml
[project]
name = "resume-tailor"
version = "0.1.0"
description = "Tailor a LaTeX resume to a job description using a local Ollama LLM"
readme = "README.md"
requires-python = ">=3.13"
dependencies = ["requests>=2.32.0"]

[project.scripts]
resume-tailor = "cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

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

[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "ruff",
    "mypy",
]
```

**Section to append** (after line 33 — add at end of file):
```toml
[tool.pytest.ini_options]
testpaths = ["src", "tests"]
pythonpath = ["src"]
markers = [
    "unit: fast isolated tests, no external deps",
    "integration: requires Ollama running locally",
    "e2e: full CLI subprocess invocation",
]
addopts = "--strict-markers -ra"
```

**Key rules:**
- Append after `[dependency-groups]` block — no insertion into existing sections
- `testpaths` must list both `"src"` and `"tests"` — `src/cli_test.py` and `src/llm_client_test.py` live in `src/`
- `pythonpath = ["src"]` is what makes the `sys.path.insert` hacks in the test files redundant

---

### `src/cli_test.py` — remove `sys.path.insert` hack (line 6 only)

**Analog:** `src/llm_client_test.py` (same structure, same hack pattern)

**Current file header** (lines 1-8):
```python
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

from cli import main
```

**After change** (line 6 removed; lines 1, 3 kept):
```python
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli import main
```

**Critical constraint — do NOT remove lines 1 or 3:**
- `import sys` at line 1 is used by `@patch("sys.argv", ...)` decorators (lines 12, 30, 46, 59, 74, 91, 113)
- `from pathlib import Path` at line 3 is used by `Path("/tmp/tailored_resume_test.tex")` (line 21) and similar mock return values

**Verification:** After removal, run `uv run ruff check src/cli_test.py` — expect zero warnings.

---

### `src/llm_client_test.py` — remove sys.path hack AND unused imports (lines 1, 3, 6)

**Analog:** `src/cli_test.py` (same structure — but different imports are in use)

**Current file header** (lines 1-10):
```python
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

import requests

from llm_client import _strip_fences, _validate_latex, generate_tailored_resume
```

**After change** (lines 1, 3, and 6 removed):
```python
import unittest
from unittest.mock import MagicMock, patch

import requests

from llm_client import _strip_fences, _validate_latex, generate_tailored_resume
```

**Why three lines removed here vs one in cli_test.py:**
- `import sys` (line 1): not used anywhere else in `llm_client_test.py` — ruff will flag F401
- `from pathlib import Path` (line 3): not used anywhere else in `llm_client_test.py` — ruff will flag F401
- `sys.path.insert(0, str(Path(__file__).parent))` (line 6): redundant with `pythonpath = ["src"]`

**Verification:** After removal, run `uv run ruff check src/llm_client_test.py` — expect zero warnings.

---

### `tests/conftest.py` — new fixture file

**Analog:** `src/llm_client_test.py` for the `requests` HTTP call pattern (lines 51-55 show `requests.ConnectionError` handling); `src/config.py` for the `OLLAMA_BASE_URL` import source.

**requests usage pattern from analog** (`src/llm_client_test.py` lines 51-55):
```python
@patch("llm_client.requests.get")
def test_health_check_connection_error_raises_runtime_error(self, mock_get):
    mock_get.side_effect = requests.ConnectionError("connection refused")
    with self.assertRaises(RuntimeError):
        generate_tailored_resume("resume text", "job description")
```

**OLLAMA_BASE_URL source** (`src/config.py` line 5):
```python
OLLAMA_BASE_URL: str = "http://localhost:11434"
```

**Complete new file to create** (`tests/conftest.py`):
```python
import pytest
import requests
from config import OLLAMA_BASE_URL


@pytest.fixture(scope="session")
def ollama_available() -> bool:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return True
    except requests.ConnectionError:
        return False


@pytest.fixture
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")
```

**Fixture design rules:**
- `ollama_available`: `scope="session"` — runs once per test session, not once per test
- `require_ollama`: no scope argument (defaults to `"function"`) — each test that needs Ollama opts in by declaring this fixture parameter
- No `autouse=True` on either fixture — tests must explicitly request `require_ollama`
- Import `OLLAMA_BASE_URL` from `config`, never hardcode the URL
- `timeout=3` on the GET call — prevents session hang if Ollama is slow to start
- Catch only `requests.ConnectionError`, not bare `Exception` — matches the specificity used in production `llm_client.py`

---

### `tests/unit/`, `tests/integration/`, `tests/e2e/` — empty directories

**No analog needed.** These are bare directories with no Python files.

**Creation pattern:**
```bash
mkdir -p /workspace/tests/unit /workspace/tests/integration /workspace/tests/e2e
```

**No `__init__.py` in any directory** — rootdir-relative layout per D-03. Adding `__init__.py` would switch pytest to package mode and can cause module name collisions when two subdirectories contain files with the same name (e.g., `tests/unit/test_client.py` and `tests/integration/test_client.py`).

---

## Shared Patterns

### Import style (no comments, no docstrings)
**Source:** `src/config.py`, `src/cli_test.py`, `src/llm_client_test.py`
**Apply to:** `tests/conftest.py`

The project enforces no inline comments and no docstrings (CLAUDE.md). All existing source files follow this:
```python
# src/config.py — no comments, names are self-documenting
from pathlib import Path

_ROOT = Path(__file__).parent.parent

OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "qwen3:14b"
```

The `tests/conftest.py` file must follow the same rule: no `#` comments, no docstrings on fixtures.

### requests.ConnectionError catch pattern
**Source:** `src/llm_client_test.py` (line 53), implied from production `llm_client.py`
**Apply to:** `tests/conftest.py` `ollama_available` fixture

Catch the specific exception `requests.ConnectionError`, not bare `Exception`:
```python
except requests.ConnectionError:
    return False
```

### Type annotations on all functions
**Source:** `src/config.py` (line 5: `OLLAMA_BASE_URL: str = ...`, line 9: `TIMEOUT: tuple[int, int] = ...`)
**Apply to:** `tests/conftest.py`

All public-facing names carry type annotations. Fixture return types must be annotated:
- `ollama_available() -> bool`
- `require_ollama(ollama_available: bool) -> None`

---

## No Analog Found

All files in this phase have close analogs in the codebase. No files require falling back to RESEARCH.md patterns alone.

| File | Reason |
|------|--------|
| (none) | All patterns sourced from existing codebase files |

---

## Metadata

**Analog search scope:** `/workspace/src/` (all `.py` files), `/workspace/pyproject.toml`
**Files scanned:** 7 (cli_test.py, llm_client_test.py, config.py, cli.py, llm_client.py, log_manager.py, pyproject.toml)
**Pattern extraction date:** 2026-06-02
