# Phase 2: LLM Integration - Pattern Map

**Mapped:** 2026-05-28
**Files analyzed:** 1 new file (`src/llm_client.py`) with 4 private helper functions
**Analogs found:** 4 / 4 (all from real codebase files)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/llm_client.py` | service | request-response | `src/resume_reader.py` | role-match (same module structure, same logger import) |
| `src/llm_client.py` — config imports | config consumer | — | `src/config.py` | exact (same constants file) |
| `src/llm_client.py` — logging | utility consumer | — | `src/log_manager.py` | exact (same `logger` instance) |
| `src/llm_client.py` — file write handoff | service boundary | — | `src/resume_writer.py` | partial (downstream caller pattern) |

---

## Pattern Assignments

### `src/llm_client.py` (service, request-response)

**Primary analog:** `src/resume_reader.py`

**Imports pattern** (`src/resume_reader.py` lines 1–4):
```python
import sys
from pathlib import Path

from log_manager import logger
```

For `llm_client.py`, substitute the stdlib and third-party imports needed by this module:
```python
import re

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT
from log_manager import logger
```

Key conventions to copy:
- `from log_manager import logger` — bare module import, not `import log_manager`
- `from config import <CONSTANT>` — named constant import, not `import config`
- Third-party (`requests`) listed after stdlib (`re`), separated by a blank line (ruff I001 / isort convention observed in codebase)

---

**Logging call pattern** (`src/resume_reader.py` lines 11–12):
```python
logger.error(f"Base resume not found at {path}")
```

Copy this f-string call style for all `logger.info`, `logger.error`, and `logger.warning` calls in `llm_client.py`. The `CustomLogger` methods accept a plain `str`; f-strings are the idiomatic format throughout the codebase.

Available methods on `logger` (from `src/log_manager.py` lines 35–48):
```python
logger.info(message: str) -> None
logger.warning(message: str) -> None
logger.error(message: str) -> None
logger.debug(message: str) -> None
logger.critical(message: str) -> None
```

---

**Error handling pattern** (`src/resume_reader.py` lines 8–12):
```python
try:
    return path.read_text(encoding="utf-8")
except FileNotFoundError:
    logger.error(f"Base resume not found at {path}")
    sys.exit(1)
```

**Important divergence for `llm_client.py`:** `resume_reader.py` calls `sys.exit(1)` directly. `llm_client.py` must NOT do this — per D-08 and the accumulated context decision, `llm_client.py` raises exceptions; `main.py` (Phase 3) calls `sys.exit`. Copy the `try/except` + `logger.error` structure, but replace `sys.exit(1)` with `raise RuntimeError(...) from exc` or `raise ValueError(...)`.

Correct pattern for `llm_client.py`:
```python
try:
    response = requests.post(...)
    response.raise_for_status()
except requests.ConnectionError as exc:
    logger.error(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
    raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}") from exc
except requests.Timeout as exc:
    logger.error(f"Ollama request timed out (timeout={TIMEOUT})")
    raise RuntimeError(f"Ollama request timed out (timeout={TIMEOUT})") from exc
except requests.HTTPError as exc:
    logger.error(f"Ollama returned HTTP error: {exc}")
    raise RuntimeError(f"Ollama returned HTTP error: {exc}") from exc
```

---

**Module-level function signature style** (`src/resume_reader.py` line 7, `src/resume_writer.py` line 5):
```python
# resume_reader.py
def read_resume(path: Path) -> str:

# resume_writer.py
def write_resume(content: str, output_dir: Path) -> Path:
```

Copy this style — type-annotated parameters and return type, no docstring, no inline comment. The public function for `llm_client.py`:
```python
def generate_tailored_resume(resume_text: str, job_description: str) -> str:
```

Private helpers use the same convention with a leading underscore:
```python
def _check_ollama_health() -> None:
def _build_messages(resume_text: str, job_description: str) -> list[dict]:
def _strip_fences(text: str) -> str:
def _validate_latex(text: str) -> str:
```

---

### Config constants (`src/config.py` lines 1–9)

**Analog:** `src/config.py` (consumed directly — no analog needed, this IS the source)

```python
OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "mistral-small3.2:24b"
TIMEOUT: tuple[int, int] = (10, 300)
```

Import pattern for `llm_client.py`:
```python
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT
```

Usage notes:
- `TIMEOUT` passed directly to `requests.post(..., timeout=TIMEOUT)` — the tuple is the connect/read timeout pair
- `TIMEOUT[0]` (= `10`) used for the health check GET — connect-only timeout; `/api/tags` responds instantly
- `OLLAMA_MODEL` used in the payload dict, never hardcoded in `llm_client.py`
- `OLLAMA_BASE_URL` used to build endpoint URLs: `f"{OLLAMA_BASE_URL}/api/chat"`, `f"{OLLAMA_BASE_URL}/api/tags"`

---

### Logger instance (`src/log_manager.py` lines 51–53)

**Analog:** `src/log_manager.py` (consumed directly)

```python
standard_logger = setup_logger(__name__)
logger = CustomLogger(standard_logger)
```

`logger` is a module-level `CustomLogger` instance. Import it with:
```python
from log_manager import logger
```

No instantiation needed in `llm_client.py` — just import and call methods.

---

### File write handoff boundary (`src/resume_writer.py` lines 5–10)

**Analog:** `src/resume_writer.py` (downstream caller, not directly copied — defines the contract `llm_client.py` must satisfy)

```python
def write_resume(content: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tailored_resume_{timestamp}.tex"
    output_path.write_text(content, encoding="utf-8")
    return output_path
```

`generate_tailored_resume()` returns a plain `str` (the validated LaTeX). Phase 3's `main.py` passes that string to `write_resume(content, OUTPUT_DIR)`. `llm_client.py` does no `Path` operations and does not import `resume_writer`.

---

## Shared Patterns

### Logger import and usage
**Source:** `src/resume_reader.py` line 4; `src/log_manager.py` lines 51–53
**Apply to:** `llm_client.py` (the only new file this phase)
```python
from log_manager import logger

logger.info("Checking Ollama health...")
logger.info(f"Calling Ollama /api/chat with model {OLLAMA_MODEL}")
logger.error(f"Ollama not reachable at {OLLAMA_BASE_URL}")
```

### Raise-not-exit error handling
**Source:** Divergence from `src/resume_reader.py` lines 11–12 — copy the `try/except` structure but replace `sys.exit(1)` with `raise`
**Apply to:** All `except` blocks in `llm_client.py`
```python
except requests.ConnectionError as exc:
    logger.error("...")
    raise RuntimeError("...") from exc
```

### No comments or docstrings
**Source:** `CLAUDE.md` Conventions section; confirmed in all existing `src/` files
**Apply to:** `llm_client.py` — no inline comments, no module-level docstring, no function docstrings. Names and type annotations are the only documentation.

### Type annotations on all function signatures
**Source:** `src/resume_reader.py` line 7, `src/resume_writer.py` line 5, `src/config.py` lines 5–9
**Apply to:** All functions in `llm_client.py` — every parameter and return type annotated.

---

## No Analog Found

No files in this phase lack a codebase analog. All patterns (module structure, logger import, config import, exception handling shape) have direct references in `src/resume_reader.py`, `src/log_manager.py`, `src/config.py`, and `src/resume_writer.py`.

The Ollama-specific patterns (`/api/chat` request body, `done_reason` check, fence stripping, LaTeX validation) have no codebase analog — these are novel to this phase and must follow the `02-RESEARCH.md` Code Examples section (the full `llm_client.py` skeleton at lines 392–491).

---

## Metadata

**Analog search scope:** `src/` (all 5 existing files read in full)
**Files scanned:** `src/config.py`, `src/log_manager.py`, `src/resume_reader.py`, `src/resume_writer.py`, `src/cli.py`
**Pattern extraction date:** 2026-05-28
