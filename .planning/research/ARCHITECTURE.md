# Test Architecture — Resume Tailor CLI v1.2

**Researched:** 2026-06-02
**Confidence:** HIGH — all patterns verified by running code against the actual workspace

---

## Directory Structure (New vs Existing)

### Recommendation: Add `tests/` alongside `src/`, keep existing `src/*_test.py` files in place

```
resume-tailor/
├── src/
│   ├── cli.py
│   ├── config.py
│   ├── llm_client.py
│   ├── log_manager.py
│   ├── resume_reader.py
│   ├── resume_writer.py
│   ├── cli_test.py          <- existing, keep as-is
│   └── llm_client_test.py   <- existing, keep as-is
├── tests/
│   ├── conftest.py          <- NEW: root conftest, shared fixtures + marker registration
│   ├── unit/
│   │   ├── test_llm_client.py   <- NEW: unit gaps (_build_messages, _check_ollama_health)
│   │   ├── test_reader.py       <- NEW: read_resume isolation tests
│   │   └── test_writer.py       <- NEW: write_resume isolation tests
│   ├── integration/
│   │   └── test_ollama.py       <- NEW: real Ollama health check + generate call
│   └── e2e/
│       └── test_cli.py          <- NEW: subprocess CLI invocation tests
└── pyproject.toml           <- MODIFY: add [tool.pytest.ini_options]
```

**Why keep existing tests in `src/`:**

The 18 existing tests pass and are already collected by pytest without any config. Migrating them disrupts working code for no functional gain. The `sys.path.insert(0, ...)` lines in the existing files are redundant (the editable install via `_editable_impl_resume_tailor.pth` already places `/workspace/src` on `sys.path`) but are harmless. Leave them in place; removing them is a cleanup task, not a blocker.

**Why add `tests/` for new tests:**

Integration and e2e tests are architecturally different from co-located unit tests. They require shared fixtures, skip logic, and marker registration that belong in a `conftest.py`. A separate `tests/` directory makes it unambiguous that these tests are not part of the package being built — the `[tool.hatch.build.targets.wheel]` `include` list already excludes `*_test.py` files by listing modules explicitly, so the package boundary is already protected.

**Tradeoffs explicitly:**

| Factor | Keep in `src/` | Move to `tests/` |
|--------|---------------|-----------------|
| Existing 18 tests | No migration cost | Must update imports, remove `sys.path.insert` |
| New integration/e2e | Conftest scope gets awkward | Clean conftest hierarchy, verified working |
| Import clarity | `sys.path.insert` is redundant noise | Imports work cleanly via editable install |
| Portfolio readability | Co-location is a valid pattern (Go-style) | Conventional Python layout, immediately recognizable |
| Pytest collection | Already working, no config needed | Requires `testpaths` in pyproject.toml |

Decision: hybrid. Existing tests stay in `src/`. New tests go in `tests/`. `pytest` with `testpaths = ["src", "tests"]` collects both.

---

## Import Strategy

### How imports work in `tests/`

The project is installed in editable mode. The file `/workspace/.venv/lib/python3.14/site-packages/_editable_impl_resume_tailor.pth` contains `/workspace/src`, which Python processes at interpreter startup for any invocation using the `.venv` interpreter. This means test files in `tests/` can import project modules with no `sys.path` manipulation:

```python
# In tests/unit/test_reader.py -- no sys.path manipulation needed
from resume_reader import read_resume
from config import BASE_RESUME_PATH
```

Verified: a test file in an unrelated `/tmp/` directory imported `from cli import main` successfully using the venv Python, with no `sys.path.insert`.

### pyproject.toml additions required

```toml
[tool.pytest.ini_options]
testpaths = ["src", "tests"]
markers = [
    "unit: Fast, isolated tests with all external calls mocked",
    "integration: Tests that call real Ollama -- skipped if Ollama is not reachable",
    "e2e: Full subprocess CLI tests requiring real Ollama -- skipped if Ollama is not reachable",
]
```

`testpaths` makes `pytest` (run with no args) collect from both locations. The `pythonpath = ["src"]` option is NOT needed because the editable install already provides this via `.pth` file. Adding it would be harmless but misleading.

**No `__init__.py` files should be added** to `tests/unit/`, `tests/integration/`, or `tests/e2e/`. Pytest collects test files without package structure. Adding `__init__.py` forces pytest into "package mode" and complicates relative imports for no benefit in this project.

---

## conftest.py Design

Single `conftest.py` at `tests/conftest.py`. Pytest discovers shared fixtures from this file before running any test in the `tests/` subtree.

```python
# tests/conftest.py

import pytest
import requests


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "unit: Fast, isolated tests with all external calls mocked"
    )
    config.addinivalue_line(
        "markers",
        "integration: Tests that call real Ollama -- skipped if Ollama is not reachable",
    )
    config.addinivalue_line(
        "markers",
        "e2e: Full subprocess CLI tests requiring real Ollama -- skipped if Ollama is not reachable",
    )


def _is_ollama_reachable() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def ollama_available() -> bool:
    return _is_ollama_reachable()


@pytest.fixture
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not reachable at http://localhost:11434")
```

**Why `pytest_configure` for markers, not `pyproject.toml` only:**

Both approaches suppress `PytestUnknownMarkWarning` (verified working). `pytest_configure` in `conftest.py` is preferable because it keeps marker descriptions co-located with the fixture logic that implements skip behavior. Markers registered via `pyproject.toml` are also fine if preferred for centralization.

**Why `scope="session"` for `ollama_available`:**

The Ollama health check is a network call. Session scope means it runs exactly once per `pytest` invocation regardless of how many tests request it. Ollama availability does not change mid-session.

**Why `require_ollama` is not `autouse=True`:**

Autouse would skip all tests in `tests/` when Ollama is down, including unit tests. Unit tests must run without Ollama. Only integration and e2e tests use `require_ollama` explicitly.

**Fixture access from subdirectories:**

Verified: `tests/conftest.py` fixtures (`ollama_available`, `require_ollama`) are accessible to test files in `tests/unit/`, `tests/integration/`, and `tests/e2e/` without any additional conftest files in the subdirectories. Pytest fixture scoping propagates down the directory tree automatically.

**Module-level autouse for integration/e2e files:**

To avoid repeating the fixture argument in every test function, use this pattern in files that require Ollama for all tests:

```python
# tests/integration/test_ollama.py

import pytest

pytestmark = [pytest.mark.integration]


@pytest.fixture(autouse=True)
def _require_ollama(require_ollama):  # noqa: PT004
    pass
```

This makes `require_ollama` autouse within the module only. Every test in the file gets the skip logic transparently.

---

## Ollama Availability Fixture

Two patterns available. Both verified working. Use the fixture pattern for integration/e2e files, inline skip for one-off tests.

### Pattern A: Module-level autouse (recommended for integration/e2e files)

```python
pytestmark = [pytest.mark.integration]

@pytest.fixture(autouse=True)
def _require_ollama(require_ollama):
    pass

def test_health_check_returns_without_raising():
    from llm_client import _check_ollama_health
    _check_ollama_health()  # skipped cleanly if Ollama is down
```

### Pattern B: Inline skip (acceptable for individual tests)

```python
def test_something(ollama_available):
    if not ollama_available:
        pytest.skip("Ollama not reachable")
    # test body
```

Pattern A is cleaner for files where all tests need Ollama. Pattern B is adequate for a single isolated test.

### Skip behavior verified

When Ollama is not running (the default in this environment), tests that depend on `require_ollama` show as `SKIPPED` in pytest output. Unit tests with no Ollama dependency pass normally. This was confirmed by running a real test session.

---

## E2E Subprocess Invocation Pattern

### Recommended: `sys.executable + ['-m', 'cli']`

```python
import subprocess
import sys

def test_empty_jd_exits_1():
    result = subprocess.run(
        [sys.executable, '-m', 'cli'],
        input='END\n',
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert 'Job description cannot be empty' in result.stderr
```

`sys.executable` is the venv Python (`/workspace/.venv/bin/python3`). Since the editable install places `src/` on the path via `.pth`, `-m cli` resolves to `src/cli.py`. Verified working.

**Why not the entry point script:**

Using `Path(sys.executable).parent / 'resume-tailor'` couples the test to the venv layout. It works in the current setup (verified: `/workspace/.venv/bin/resume-tailor` exists and works) but breaks in `uv tool install` environments where the script lives in `~/.local/bin/`. `sys.executable + ['-m', 'cli']` has no such dependency.

**Why not `python src/cli.py`:**

Works locally (verified) but requires knowing the repo root path at test time, introduces a hardcoded path, and does not reflect how the tool runs in production.

### Stdin injection

Job description input is piped via the `input=` parameter. The sentinel `END` must be on its own line:

```python
result = subprocess.run(
    [sys.executable, '-m', 'cli', '--output-dir', str(tmp_path)],
    input='Senior ML Engineer at Acme Corp\nEND\n',
    capture_output=True,
    text=True,
)
```

Use `input=` (not `stdin=subprocess.PIPE` + `.communicate()`) -- it is synchronous, captures all output, and avoids deadlock risk.

### Output file validation

Use pytest's `tmp_path` fixture for `--output-dir` to avoid polluting `resumes/output/` during tests:

```python
def test_output_file_written(require_ollama, tmp_path):
    result = subprocess.run(
        [sys.executable, '-m', 'cli',
         '--output-dir', str(tmp_path),
         '--resume', str(BASE_RESUME_PATH)],
        input='Software Engineer at Acme\nEND\n',
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    tex_files = list(tmp_path.glob('tailored_resume_*.tex'))
    assert len(tex_files) == 1
    assert tex_files[0].stat().st_size > 0
```

### Filename pattern validation

```python
import re
assert re.match(r'tailored_resume_\d{8}_\d{6}\.tex', tex_files[0].name)
```

### Error path coverage without Ollama

Two error paths can be tested without Ollama being available:
1. Empty JD: `input='END\n'` triggers the empty-JD guard before any LLM call.
2. Missing resume file: `--resume /nonexistent/path.tex` triggers `FileNotFoundError` before any LLM call.

The "Ollama unreachable" e2e path (exit 1, "Ollama is not reachable" in stderr) is covered by the existing `test_health_check_connection_error_raises_runtime_error` unit test in `src/llm_client_test.py`. There is no need to duplicate it as an e2e subprocess test.

---

## Suggested Build Order

Each phase is runnable and independently verifiable before the next begins.

### Phase 1: Test Infrastructure

Create the scaffolding that all subsequent tests depend on.

1. Add `[tool.pytest.ini_options]` to `pyproject.toml` with `testpaths = ["src", "tests"]` and the three `markers` entries.
2. Create `tests/conftest.py` with `pytest_configure`, `ollama_available`, and `require_ollama`.
3. Create the `tests/unit/`, `tests/integration/`, `tests/e2e/` directories (empty, no `__init__.py`).
4. Verify: `pytest` collects exactly the existing 18 tests, zero `PytestUnknownMarkWarning`, `pytest -m unit` selects 0 tests, `pytest -m "not integration and not e2e"` selects 18.

This phase does not modify any existing test or source file.

### Phase 2: Unit Test Gaps

Add missing unit coverage for functions not yet tested by `src/*_test.py`.

**`tests/unit/test_llm_client.py`** -- cover:
- `_build_messages()`: returns list of length 2, first role is `"system"`, second role is `"user"`, user content contains `<job_description>` and `<resume>` XML tags, system content contains `\documentclass`.
- `_check_ollama_health()` in isolation: `ConnectionError` raises `RuntimeError`, `Timeout` raises `RuntimeError`, 200 OK response does not raise.

**`tests/unit/test_reader.py`** -- cover:
- `read_resume()`: existing file returns its content, missing file raises `FileNotFoundError` with path in message.

**`tests/unit/test_writer.py`** -- cover:
- `write_resume()`: creates `output_dir` if it does not exist, filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex` pattern, file contains the exact content passed in.

All these tests use `unittest.mock.patch` or `tmp_path`. No Ollama needed. Add `pytestmark = [pytest.mark.unit]` at module level.

**Test style note:** Existing tests use `unittest.TestCase`. New tests in `tests/` should use pytest-native style (plain functions, `assert` statements, fixtures as function arguments). The two styles coexist in the same pytest session without conflict.

### Phase 3: Integration Tests

Tests that call real Ollama directly (not through subprocess).

**`tests/integration/test_ollama.py`** -- cover:
- `_check_ollama_health()`: real call returns without raising.
- `generate_tailored_resume()`: returns string starting with `\documentclass`, contains `\end{document}`, contains no markdown code fences.
- Use the module-level autouse `_require_ollama` fixture pattern. The entire file skips cleanly when Ollama is down.
- Pass a minimal synthetic `.tex` snippet as `resume_text` rather than the real `resumes/english.tex`. This keeps token usage low and avoids coupling integration tests to the actual resume content. Example:

```python
MINIMAL_RESUME = r"""\documentclass{article}
\begin{document}
\section{Summary}
Software engineer with 5 years experience.
\end{document}"""
```

### Phase 4: E2E Tests

Tests that exercise the full CLI through `subprocess.run`.

**`tests/e2e/test_cli.py`** -- cover:
- Error paths that do NOT need Ollama (no skip required):
  - Empty JD: exit code 1, "Job description cannot be empty" in stderr.
  - Missing resume file: exit code 1, path mentioned in stderr.
- Golden path (needs Ollama, gated by `require_ollama`):
  - Output file created in `tmp_path`, filename matches timestamp pattern, file is non-empty.
  - Stdout contains "Tailored resume written to:".
  - Exit code 0.

**Build order rationale:**
- Phase 1 (infrastructure) before Phase 2 (unit) so markers and skip logic work from the start.
- Phase 2 (unit) before Phase 3 (integration) because unit tests expose import or interface issues cheaply before spending LLM inference time on them.
- Phase 3 (integration) before Phase 4 (e2e) because a broken integration layer causes e2e failures with misleading symptoms.
- Error-path e2e tests (Ollama not required) can be written in Phase 4 regardless of Ollama availability.

---

## Files to Create or Modify

| File | Status | Action |
|------|--------|--------|
| `pyproject.toml` | Modify | Add `[tool.pytest.ini_options]` block |
| `tests/conftest.py` | Create | Marker registration, `ollama_available`, `require_ollama` fixtures |
| `tests/unit/test_llm_client.py` | Create | `_build_messages`, `_check_ollama_health` unit tests |
| `tests/unit/test_reader.py` | Create | `read_resume` unit tests |
| `tests/unit/test_writer.py` | Create | `write_resume` unit tests |
| `tests/integration/test_ollama.py` | Create | Real Ollama health + generate tests |
| `tests/e2e/test_cli.py` | Create | Subprocess CLI tests |
| `src/cli_test.py` | No change | Existing tests stay; `sys.path.insert` is redundant but harmless |
| `src/llm_client_test.py` | No change | Existing tests stay; `sys.path.insert` is redundant but harmless |

---

## Constraints Carried Forward

- No new production dependencies. `pytest`, `ruff`, `mypy` are already in `[dependency-groups] dev`.
- The `requests` import in `conftest.py` is fine -- it is already a production dependency and is available in the dev environment.
- Do not add `pytest-mock` or any other pytest plugin. `unittest.mock` covers all mocking needs in this codebase.
- Do not add `pytest-subprocess` or `pytest-asyncio` -- `subprocess.run` with `input=` handles all e2e cases directly.
- The `[tool.hatch.build.targets.wheel]` `include` list in `pyproject.toml` already excludes test files by listing only source modules explicitly. The `tests/` directory does not affect the built wheel.

---

## Sources

- Codebase inspection: `/workspace/src/` and `/workspace/pyproject.toml` (all files read directly -- HIGH confidence)
- Editable install path confirmed: `/workspace/.venv/lib/python3.14/site-packages/_editable_impl_resume_tailor.pth` contains `/workspace/src`
- Pytest 9.0.3 marker registration: verified `PytestUnknownMarkWarning` appears without registration, disappears with `pytest_configure` (runtime test)
- Pytest `pythonpath` ini option: verified adds path to `sys.path` (runtime test with isolated temp directory)
- `subprocess.run` with `input=`: verified stdin piping for empty JD and Ollama-unreachable error paths (runtime test)
- `sys.executable + ['-m', 'cli']`: verified exit code 0 for `--help` and correct exit code 1 for error paths (runtime test)
- Conftest fixture hierarchy: verified `tests/conftest.py` fixtures accessible from `tests/unit/` and `tests/integration/` subdirectories (runtime test)
- Session-scoped Ollama skip: verified tests skip cleanly when Ollama is not running (runtime test in current environment where Ollama is not available)
