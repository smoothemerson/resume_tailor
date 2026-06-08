# Phase 11: E2E Tests - Pattern Map

**Mapped:** 2026-06-08
**Files analyzed:** 1 (new file)
**Analogs found:** 1 / 1

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tests/e2e/test_cli.py` | test | request-response (subprocess) | `tests/integration/test_llm_client.py` | role-match |

## Pattern Assignments

### `tests/e2e/test_cli.py` (test, request-response via subprocess)

**Analog:** `tests/integration/test_llm_client.py`

**Imports pattern** (`tests/integration/test_llm_client.py` lines 1-11):
```python
import pytest

from llm_client import _check_ollama_health, generate_tailored_resume

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)
```

For `test_cli.py`, extend the import block with subprocess-specific stdlib imports and add the `CLI_PATH` constant (from CONTEXT.md D-01, D-03):

```python
import re
import subprocess
import sys
from pathlib import Path

import pytest

CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)
```

Key rules:
- `parents[2]` is repo root — `parents[0]` = `tests/e2e`, `parents[1]` = `tests`, `parents[2]` = workspace root
- `MINIMAL_RESUME` is defined locally — never imported from another test file

**Marker pattern** (`tests/integration/test_llm_client.py` lines 14-15, 19-20):
```python
@pytest.mark.integration
def test_ollama_health_check_does_not_raise(require_ollama):
    ...

@pytest.mark.integration
def test_generate_tailored_resume_returns_valid_latex(require_ollama):
    ...
```

For `test_cli.py`, substitute `@pytest.mark.e2e` — required by `--strict-markers` in `pyproject.toml` (`addopts = "--strict-markers -ra --import-mode=importlib"`). Both test functions carry this marker with no exceptions.

**require_ollama skip pattern** (`tests/conftest.py` lines 16-19 + usage in `test_llm_client.py`):
```python
# conftest.py definition (session-scoped, auto-skips when Ollama is down)
@pytest.fixture(scope="session")
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")

# Usage: declare as function argument to auto-skip
@pytest.mark.integration
def test_generate_tailored_resume_returns_valid_latex(require_ollama):
    ...
```

For `test_cli.py`: TEST-11 includes `require_ollama` as a function argument; TEST-10 does NOT — the empty-JD error path exits before any Ollama call, so TEST-10 must run regardless of Ollama availability.

**Core subprocess invocation pattern** (from CONTEXT.md D-01/D-02, verified live against `src/cli.py`):

TEST-10 (empty JD error path — no fixtures):
```python
@pytest.mark.e2e
def test_empty_jd_exits_1_with_stderr_message():
    result = subprocess.run(
        [sys.executable, CLI_PATH],
        input="END\n",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Error: Job description cannot be empty." in result.stderr
```

The exact error string `"Error: Job description cannot be empty."` comes from `src/cli.py` line 45:
```python
print("Error: Job description cannot be empty.", file=sys.stderr)
```

TEST-11 (golden path — Ollama-dependent, uses `tmp_path`):
```python
@pytest.mark.e2e
def test_golden_path_exits_0_creates_output_file(require_ollama, tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text(MINIMAL_RESUME, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, CLI_PATH,
         "--resume", str(resume_file),
         "--output-dir", str(tmp_path)],
        input="Python backend engineer with REST API experience\nEND\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Tailored resume written to:" in result.stdout
    output_files = list(tmp_path.glob("tailored_resume_*.tex"))
    assert len(output_files) == 1
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)
```

The exact success string `"Tailored resume written to:"` comes from `src/cli.py` line 59:
```python
print(f"Tailored resume written to: {output_path.resolve()}")
```

The `--resume` and `--output-dir` flags are confirmed at `src/cli.py` lines 20-21:
```python
parser.add_argument("--resume", type=Path, default=None, help="Path to base .tex resume file")
parser.add_argument("--output-dir", type=Path, default=None, help="Directory for output files")
```

**Filename pattern assertion** (`tests/unit/test_resume_writer.py` line 26):
```python
assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)
```

Applied in TEST-11 via `output_files[0].name` after `tmp_path.glob("tailored_resume_*.tex")`.

**tmp_path + file write pattern** (`tests/unit/test_resume_writer.py` lines 10-13):
```python
def test_write_resume_creates_output_directory(tmp_path):
    output_dir = tmp_path / "new_output"
    ...
    write_resume("content", output_dir)
```

For `test_cli.py` TEST-11: `tmp_path / "resume.tex"` then `.write_text(MINIMAL_RESUME, encoding="utf-8")` to create the fixture file; `--output-dir str(tmp_path)` to direct CLI output into the same isolated directory.

---

## Shared Patterns

### Marker Enforcement
**Source:** `pyproject.toml` lines 39-44 + `tests/integration/test_llm_client.py`
**Apply to:** Both test functions in `tests/e2e/test_cli.py`

`pyproject.toml` registers the `e2e` marker and enforces `--strict-markers`:
```toml
markers = [
    "e2e: full CLI subprocess invocation",
]
addopts = "--strict-markers -ra --import-mode=importlib"
```

Every function in `tests/e2e/` must carry `@pytest.mark.e2e`.

### require_ollama Selective Skip
**Source:** `tests/conftest.py` lines 16-19
**Apply to:** TEST-11 only; TEST-10 must NOT include it

The fixture is session-scoped — it probes Ollama once per test session and short-circuits any test that declares it as an argument. Do not apply to error-path tests that should run without Ollama.

### subprocess.run Call Convention
**Source:** CONTEXT.md D-02, RESEARCH.md Pattern 2
**Apply to:** Both subprocess invocations in `test_cli.py`

Canonical signature:
```python
subprocess.run(
    [sys.executable, CLI_PATH, ...optional_flags...],
    input="<stdin_content>\n",
    capture_output=True,
    text=True,
)
```

- `sys.executable` — never hardcode `python3`; resolves to the active venv interpreter
- `capture_output=True` — equivalent to `stdout=PIPE, stderr=PIPE`; single flag preferred
- `text=True` — returns `str`; no `.decode()` needed
- No `cwd=` argument needed — `/workspace/src` is on `sys.path` via the editable install `.pth` file

### Module-Level Constants
**Source:** `tests/integration/test_llm_client.py` lines 5-11
**Apply to:** `test_cli.py` top of file

Define `CLI_PATH` and `MINIMAL_RESUME` at module level, before all test functions. Do not recompute inside test bodies and do not import from other test files.

---

## No Analog Found

All patterns for this file have direct analogs in the codebase. No patterns need to fall back to RESEARCH.md alone.

---

## Metadata

**Analog search scope:** `tests/integration/`, `tests/unit/`, `tests/conftest.py`, `src/cli.py`
**Files scanned:** 6 (`test_llm_client.py`, `conftest.py`, `test_resume_writer.py`, `test_jd_analyzer.py`, `cli.py`, `pyproject.toml`)
**Pattern extraction date:** 2026-06-08
