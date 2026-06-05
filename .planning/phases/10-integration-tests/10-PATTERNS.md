# Phase 10: Integration Tests - Pattern Map

**Mapped:** 2026-06-05
**Files analyzed:** 1 (new file)
**Analogs found:** 1 / 1

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tests/integration/test_llm_client.py` | test | request-response | `tests/unit/test_llm_client.py` | role-match (same module under test; different dependency strategy: live vs mocked) |

## Pattern Assignments

### `tests/integration/test_llm_client.py` (test, request-response)

**Analog:** `tests/unit/test_llm_client.py`

**Imports pattern** (lines 1-11 of analog):
```python
import pytest
import requests
from unittest.mock import MagicMock, patch

from llm_client import (
    _build_messages,
    _check_ollama_health,
    _strip_fences,
    _validate_latex,
    generate_tailored_resume,
)
```

Integration variant — drop `unittest.mock` imports (no mocking needed), keep only the two functions under test:
```python
import pytest

from llm_client import _check_ollama_health, generate_tailored_resume
```

**Module-level constant pattern** — no analog in unit tests (unit tests use inline literals). Shape locked by D-01/D-02:
```python
MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)
```

**Marker pattern** (lines 14, 21, 27, ... of analog — every test function):
```python
@pytest.mark.unit
def test_<name>():
    ...
```

Integration variant — replace `unit` with `integration` on every test function:
```python
@pytest.mark.integration
def test_<name>(require_ollama):
    ...
```

**Skip-via-fixture pattern** — sourced from `tests/conftest.py` lines 15-18:
```python
@pytest.fixture
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")
```

Consumed in tests by accepting `require_ollama` as a positional parameter. pytest injects it automatically; if Ollama is down the fixture calls `pytest.skip()` before the test body runs. Each test function must independently declare the parameter — do not share at module or class level (see Research Pitfall 2).

**"Does not raise" assertion pattern** (analog: lines 93-101 of `tests/unit/test_llm_client.py`):
```python
@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_200_does_not_raise(mock_get):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    _check_ollama_health()
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
```

Integration variant — no patching, no assertions beyond "no exception raised". The call itself is the full test body:
```python
@pytest.mark.integration
def test_ollama_health_check_does_not_raise(require_ollama):
    _check_ollama_health()
```

**TailorResult assertion pattern** (analog: lines 155-169 of `tests/unit/test_llm_client.py`):
```python
@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_returns_tailor_result(mock_post, mock_health):
    valid_latex = "\\documentclass{article}\nbody\n\\end{document}"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": valid_latex},
    }
    mock_post.return_value = mock_response
    result = generate_tailored_resume("resume", "job desc")
    assert result.content == valid_latex
    assert result.fences_stripped is False
```

Integration variant — no patching. Assert structural invariants (D-04) rather than exact content. Inline JD string, use module-level `MINIMAL_RESUME`:
```python
@pytest.mark.integration
def test_generate_tailored_resume_returns_valid_latex(require_ollama):
    result = generate_tailored_resume(
        MINIMAL_RESUME,
        "Python backend engineer with REST API experience",
    )
    assert result.content.lstrip().startswith("\\documentclass")
    assert result.content.rstrip().endswith("\\end{document}")
    assert "```" not in result.content
    assert result.fences_stripped is False
```

---

## Shared Patterns

### Skip-on-Absent Guard
**Source:** `tests/conftest.py` lines 6-18
**Apply to:** Both test functions in `tests/integration/test_llm_client.py`

The `require_ollama` fixture depends on the session-scoped `ollama_available` fixture (which probes `localhost:11434/api/tags` once). Each test function must declare `require_ollama` as a parameter individually:

```python
# tests/conftest.py lines 6-18 (full fixture pair)
@pytest.fixture(scope="session")
def ollama_available() -> bool:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False

@pytest.fixture
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")
```

### Import Convention
**Source:** `tests/unit/test_llm_client.py` lines 5-11
**Apply to:** `tests/integration/test_llm_client.py`

Import from `llm_client` directly (no package prefix). `pythonpath = ["src"]` in `pyproject.toml` makes `src/` a root for test imports. No `__init__.py` in `tests/integration/`.

```python
from llm_client import _check_ollama_health, generate_tailored_resume
```

### Marker Discipline
**Source:** `pyproject.toml` lines 39-44 + `tests/unit/test_llm_client.py` (every test function)
**Apply to:** Both test functions in `tests/integration/test_llm_client.py`

`addopts = "--strict-markers"` means an unregistered marker causes collection failure. `integration` is registered. Every test function must carry `@pytest.mark.integration` — no exceptions.

```toml
# pyproject.toml
markers = [
    "unit: fast isolated tests, no external deps",
    "integration: requires Ollama running locally",
    "e2e: full CLI subprocess invocation",
]
addopts = "--strict-markers -ra"
```

---

## No Analog Found

None — the unit test file is a strong role-match analog. All patterns are covered.

---

## Metadata

**Analog search scope:** `tests/unit/`, `tests/conftest.py`, `src/llm_client.py`, `pyproject.toml`
**Files scanned:** 4
**Pattern extraction date:** 2026-06-05
