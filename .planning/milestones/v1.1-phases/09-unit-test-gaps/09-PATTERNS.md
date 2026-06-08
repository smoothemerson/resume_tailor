# Phase 9: Unit Test Gaps - Pattern Map

**Mapped:** 2026-06-04
**Files analyzed:** 3 new test files
**Analogs found:** 3 / 3

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `tests/unit/test_llm_client.py` | test | request-response | `src/llm_client_test.py` | exact |
| `tests/unit/test_resume_reader.py` | test | file-I/O | `src/llm_client_test.py` (structure); `src/resume_reader.py` (source under test) | role-match |
| `tests/unit/test_resume_writer.py` | test | file-I/O | `src/llm_client_test.py` (structure); `src/resume_writer.py` (source under test) | role-match |

---

## Pattern Assignments

### `tests/unit/test_llm_client.py` (test, request-response)

**Analog:** `src/llm_client_test.py`

**Imports pattern** (`src/llm_client_test.py` lines 1-6):
```python
import pytest
from unittest.mock import MagicMock, patch

import requests

from llm_client import TailorResult, _strip_fences, _validate_latex, generate_tailored_resume
```
New file adapts this to import `_build_messages` and `_check_ollama_health` instead of the public API:
```python
import pytest
import requests
from unittest.mock import MagicMock, patch

from llm_client import _build_messages, _check_ollama_health
```

**Marker pattern** — every test function in `tests/unit/` must carry `@pytest.mark.unit` (D-03). The existing `src/llm_client_test.py` has no markers (D-04 — do not add them). The new files differ from the analog in this one respect.

**Pure-function test pattern** — `_build_messages` needs no mocking (`src/llm_client.py` lines 26-109 confirm it is pure):
```python
@pytest.mark.unit
def test_build_messages_returns_two_element_list():
    result = _build_messages("resume text", "job description")
    assert len(result) == 2

@pytest.mark.unit
def test_build_messages_role_ordering():
    result = _build_messages("resume text", "job description")
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"
```
Assert structural markers and XML tags only — do NOT assert exact prompt prose (ROADMAP success criteria item 2).

Tags verified in source (`src/llm_client.py` lines 28, 70, 98-103):
- System message contains: `<PERSONA>`, `<CONSTRAINTS>`
- User message contains: `<job_description>`, `<resume>`

**Patch-decorator pattern for `_check_ollama_health`** (`src/llm_client_test.py` lines 50-54):
```python
@patch("llm_client.requests.get")
def test_health_check_connection_error_raises_runtime_error(mock_get):
    mock_get.side_effect = requests.ConnectionError("connection refused")
    with pytest.raises(RuntimeError):
        generate_tailored_resume("resume text", "job description")
```
New tests call `_check_ollama_health()` directly instead of through `generate_tailored_resume()`. Patch target is the same: `"llm_client.requests.get"`.

**ConnectionError and Timeout paths** — use `side_effect` directly on `mock_get` (`src/llm_client.py` lines 18-21 show `requests.get()` raises these):
```python
@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_connection_error_raises_runtime_error(mock_get):
    mock_get.side_effect = requests.ConnectionError("connection refused")
    with pytest.raises(RuntimeError):
        _check_ollama_health()

@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_timeout_raises_runtime_error(mock_get):
    mock_get.side_effect = requests.Timeout("timed out")
    with pytest.raises(RuntimeError):
        _check_ollama_health()
```

**HTTPError path** — `HTTPError` is raised by `response.raise_for_status()`, NOT by `requests.get()`. Set side_effect on the response mock's method, not on `mock_get` directly (`src/llm_client.py` line 17 shows `response.raise_for_status()` is the call site):
```python
@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_http_error_raises_runtime_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("503")
    mock_get.return_value = mock_response
    with pytest.raises(RuntimeError):
        _check_ollama_health()
```

**HTTP 200 / no-raise path** — `MagicMock` auto-stubs `raise_for_status()` as a no-op. Confirmed by `src/llm_client_test.py` lines 60-61 where `mock_get.return_value = MagicMock(status_code=200)` is the established pattern:
```python
@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_200_does_not_raise(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    _check_ollama_health()
```

---

### `tests/unit/test_resume_reader.py` (test, file-I/O)

**Analog:** `src/llm_client_test.py` for test file structure; `src/resume_reader.py` for the source under test.

**Imports pattern:**
```python
import pytest
from resume_reader import read_resume
```
`pathlib.Path` is NOT imported — `tmp_path` yields a `Path` directly; no import needed.

**Source under test** (`src/resume_reader.py` lines 1-8 — full file):
```python
from pathlib import Path

def read_resume(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Base resume not found at {path}") from exc
```
Key observation: the function re-raises a NEW `FileNotFoundError` (not the original). Tests use `pytest.raises(FileNotFoundError)` only — do not inspect `excinfo.value.__cause__` or assert on the message text.

**`tmp_path` fixture pattern** — built-in pytest fixture, no import, no conftest entry:
```python
@pytest.mark.unit
def test_read_resume_returns_file_content(tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text("\\documentclass{article}", encoding="utf-8")
    assert read_resume(resume_file) == "\\documentclass{article}"

@pytest.mark.unit
def test_read_resume_missing_file_raises_file_not_found_error(tmp_path):
    missing = tmp_path / "nonexistent.tex"
    with pytest.raises(FileNotFoundError):
        read_resume(missing)
```

---

### `tests/unit/test_resume_writer.py` (test, file-I/O)

**Analog:** `src/llm_client_test.py` for test file structure; `src/resume_writer.py` for the source under test.

**Imports pattern:**
```python
import re
import pytest
from pathlib import Path
from resume_writer import write_resume
```
`re` is needed for the filename pattern assertion (D-05). `Path` is needed for `isinstance(result, Path)` assertion.

**Source under test** (`src/resume_writer.py` lines 1-10 — full file):
```python
from datetime import datetime
from pathlib import Path

def write_resume(content: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tailored_resume_{timestamp}.tex"
    output_path.write_text(content, encoding="utf-8")
    return output_path
```
Key observations:
- `mkdir(parents=True, exist_ok=True)` — directory creation must be exercised; pass a sub-path that does not yet exist (e.g., `tmp_path / "new_output"`), not `tmp_path` directly.
- `strftime("%Y%m%d_%H%M%S")` — produces the pattern `\d{8}_\d{6}`.
- Returns the written `Path` object.

**`write_resume` test pattern** — four tests covering all four TEST-07 sub-requirements:
```python
@pytest.mark.unit
def test_write_resume_creates_output_directory(tmp_path):
    output_dir = tmp_path / "new_output"
    assert not output_dir.exists()
    write_resume("content", output_dir)
    assert output_dir.exists()

@pytest.mark.unit
def test_write_resume_returns_path(tmp_path):
    result = write_resume("content", tmp_path / "out")
    assert isinstance(result, Path)

@pytest.mark.unit
def test_write_resume_filename_matches_timestamp_pattern(tmp_path):
    result = write_resume("content", tmp_path / "out")
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)

@pytest.mark.unit
def test_write_resume_content_equals_input_string(tmp_path):
    content = "\\documentclass{article}\n\\end{document}"
    result = write_resume(content, tmp_path / "out")
    assert result.read_text(encoding="utf-8") == content
```
Note: each test uses a fresh `tmp_path / "out"` sub-path. Since `write_resume` calls `mkdir(exist_ok=True)`, reusing the same sub-path across tests is safe but using unique sub-paths per test is clearer.

---

## Shared Patterns

### `@pytest.mark.unit` Marker
**Source:** `pyproject.toml` lines 37-41 (marker declaration); D-03 (locked decision)
**Apply to:** Every test function in all three new files — no exceptions.
```toml
[tool.pytest.ini_options]
markers = [
    "unit: fast isolated tests, no external deps",
    ...
]
addopts = "--strict-markers -ra"
```
`--strict-markers` is already in `addopts`. A test without `@pytest.mark.unit` will still run with `pytest tests/unit/` but will be silently excluded from `pytest -m unit tests/unit/` — the required ROADMAP command.

### Patch Target Convention
**Source:** `src/llm_client_test.py` lines 50-54, 57-58
**Apply to:** All `_check_ollama_health()` tests in `test_llm_client.py`

Patch at the name as it appears in the module under test, not at the definition site:
```python
# Correct — patches the name 'requests' as bound in llm_client module
@patch("llm_client.requests.get")

# Wrong — patches the requests module globally, does not intercept the call in llm_client
@patch("requests.get")
```

### `pytest.raises` Pattern
**Source:** `src/llm_client_test.py` lines 53-54, 83-84
**Apply to:** All error-path tests across all three new files
```python
with pytest.raises(RuntimeError):
    _check_ollama_health()

with pytest.raises(FileNotFoundError):
    read_resume(missing)
```

### Multi-decorator Stacking Order
**Source:** `src/llm_client_test.py` lines 57-59 (two decorators)
**Apply to:** Any test that stacks multiple `@patch` decorators

Decorators apply bottom-up; mock arguments match in reverse order:
```python
@patch("llm_client.requests.post")   # second decorator → second mock arg
@patch("llm_client.requests.get")    # first decorator  → first mock arg
def test_example(mock_get, mock_post):
    ...
```
The new `test_llm_client.py` tests only need one `@patch` per test — no stacking needed. But this pattern documents the convention if stacking is later required.

---

## No Analog Found

No files fall into this category. All three new test files have a direct analog in `src/llm_client_test.py`.

---

## Metadata

**Analog search scope:** `/workspace/src/`, `/workspace/tests/`
**Files scanned:** `src/llm_client_test.py`, `src/llm_client.py`, `src/resume_reader.py`, `src/resume_writer.py`, `tests/conftest.py`, `pyproject.toml`
**Pattern extraction date:** 2026-06-04
