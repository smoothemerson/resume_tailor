# Phase 9: Unit Test Gaps - Research

**Researched:** 2026-06-04
**Domain:** pytest unit testing, unittest.mock, Python stdlib
**Confidence:** HIGH

## Summary

Phase 9 adds isolated unit tests for four functions that have no direct coverage in the
existing `src/*_test.py` suite: `_build_messages()`, `_check_ollama_health()`,
`read_resume()`, and `write_resume()`. All source functions are pure or near-pure Python
(no subprocesses, no network I/O that can't be patched) making them straightforward to
test with `unittest.mock.patch` and pytest's built-in `tmp_path` fixture.

The test infrastructure from Phase 8 is already complete: `pyproject.toml` has
`testpaths`, `pythonpath`, markers, and `--strict-markers` configured; `tests/unit/` exists
as an empty directory (confirmed: only `.gitkeep` present). No infrastructure work is
needed in this phase — it is purely test-writing work.

Every new test carries `@pytest.mark.unit` and lives in `tests/unit/`. The existing
`src/*_test.py` files are left untouched (D-04). The three new files map one-to-one to
source modules: `test_llm_client.py`, `test_resume_reader.py`, `test_resume_writer.py`.

**Primary recommendation:** Write the three test files directly into `tests/unit/` using
the established `@patch("llm_client.requests.get")` pattern from `src/llm_client_test.py`.
No new dependencies, no configuration changes, no fixtures beyond `tmp_path`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** New test files go in `tests/unit/` using `test_*.py` prefix (pytest default
discovery pattern) — not `*_test.py` like `src/`.

**D-02:** One file per source module: `test_llm_client.py` (covers `_build_messages` +
`_check_ollama_health`), `test_resume_reader.py`, `test_resume_writer.py`.

**D-03:** Every new test in `tests/unit/` carries `@pytest.mark.unit` — required for
`pytest -m unit tests/unit/` (ROADMAP success criteria command).

**D-04:** `src/*_test.py` files are left as-is — no markers added to existing tests.
They are not in scope for Phase 9.

**D-05:** Use `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", path.name)` to assert
filename pattern — no datetime mocking needed.

**D-06:** Assert both filename pattern AND that `path.read_text(encoding="utf-8") ==
input_string` (covers full TEST-07 requirement).

**D-07:** Use pytest's `tmp_path` fixture for the output directory in `write_resume()`
tests.

**D-08:** Tests call `_check_ollama_health()` directly (not through
`generate_tailored_resume()`), patching `llm_client.requests.get`.

**D-09:** Cover all three paths: `ConnectionError` → `RuntimeError`, `Timeout` →
`RuntimeError`, HTTP 200 → no raise.

**D-10:** Also cover the `HTTPError` path (non-200 response raises `RuntimeError`) even
though TEST-05 doesn't explicitly list it — it's already in the function body and costs
one test.

**D-11:** Keep the existing `test_health_check_connection_error_raises_runtime_error` in
`src/llm_client_test.py` — it tests at the `generate_tailored_resume()` level, which is
a different layer from the new direct `_check_ollama_health()` tests. Both are valid; no
duplication to remove.

### Claude's Discretion

None specified — all implementation decisions were locked in the CONTEXT.md session.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-04 | `_build_messages()` tested: returns 2-element list with roles `"system"` then `"user"`; user content contains `<job_description>` and `<resume>` XML tags embedding the provided inputs; system content contains `<PERSONA>` and `<CONSTRAINTS>` markers | Source inspection confirms exact tag names. Function takes `(resume_text: str, job_description: str)` and returns `list[dict]`. No mocking needed — pure function. |
| TEST-05 | `_check_ollama_health()` tested in isolation: raises `RuntimeError` on `ConnectionError`; raises `RuntimeError` on `Timeout`; does not raise when response status is 200 | Source inspection confirms the three exception branches. Patch target: `llm_client.requests.get`. D-10 adds a fourth path (HTTPError) at no extra cost. |
| TEST-06 | `read_resume()` tested: returns file text content when file exists; raises `FileNotFoundError` when file does not exist | Source inspection: `path.read_text(encoding="utf-8")` wrapped in try/except. Use `tmp_path` to create a real file for the happy-path test. |
| TEST-07 | `write_resume()` tested: creates output directory if it does not exist; returns a `Path`; written filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex` pattern; file content equals the input string | Source inspection confirms `mkdir(parents=True, exist_ok=True)` and `datetime.now().strftime`. D-05 + D-06 cover all four sub-requirements. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Unit test isolation | Test layer (pytest) | unittest.mock | Tests own their isolation boundary; source code is not modified |
| Patch target resolution | Test layer | — | Patch at the module where the name is looked up (`llm_client.requests.get`), not the definition site (`requests.get`) |
| Filesystem fixtures | Test layer (tmp_path) | — | Built-in pytest fixture; no shared conftest needed for unit tests |
| Test discovery | pytest config (pyproject.toml) | — | `testpaths = ["src", "tests"]` already covers `tests/unit/` |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.3 | Test runner, fixtures, markers | [VERIFIED: pyproject.toml dependency-groups.dev] — already installed |
| unittest.mock | stdlib | `patch`, `MagicMock` | [VERIFIED: codebase] — already used in `src/llm_client_test.py` |
| re | stdlib | Regex assertion for timestamp filename | [VERIFIED: codebase] — `re.match` per D-05 |
| pathlib.Path | stdlib | `tmp_path` yields `Path`; `read_resume` accepts `Path` | [VERIFIED: codebase] — used throughout source |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests.exceptions | 2.32.x | `ConnectionError`, `Timeout`, `HTTPError` side_effect values | Set as `side_effect` on the mock to simulate error paths |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `re.match` for filename | `datetime.strptime` parse | `strptime` validates the timestamp is a valid date; `re.match` only validates format. Per D-05, regex is the locked decision. |
| `@patch` decorator | `with patch(...)` context manager | Equivalent in behavior; decorator form matches existing `src/llm_client_test.py` style — use decorator for consistency. |

**Installation:** None — all dependencies already present.

## Package Legitimacy Audit

No new packages are installed in this phase. All tooling (`pytest`, `unittest.mock`, `re`,
`pathlib`, `requests`) is either already installed or part of the Python stdlib.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
tests/unit/
    test_llm_client.py
        ├── _build_messages() ──→ [no mocking] ──→ assert list structure + tag presence
        └── _check_ollama_health()
                ├── @patch("llm_client.requests.get", side_effect=ConnectionError) → RuntimeError
                ├── @patch("llm_client.requests.get", side_effect=Timeout)         → RuntimeError
                ├── @patch("llm_client.requests.get", side_effect=HTTPError)       → RuntimeError
                └── @patch("llm_client.requests.get", return_value=MagicMock(200)) → no raise

    test_resume_reader.py
        └── read_resume(path)
                ├── tmp_path / "resume.tex" (exists, has content) → returns string
                └── tmp_path / "missing.tex" (does not exist)    → FileNotFoundError

    test_resume_writer.py
        └── write_resume(content, output_dir)
                ├── output_dir = tmp_path / "new_subdir" (does not exist yet) → mkdir called
                ├── return value is Path
                ├── path.name matches re pattern
                └── path.read_text(encoding="utf-8") == input_string
```

### Recommended Project Structure

```
tests/
├── conftest.py          # Ollama fixtures (existing, untouched)
├── unit/
│   ├── test_llm_client.py     # NEW — _build_messages + _check_ollama_health
│   ├── test_resume_reader.py  # NEW — read_resume
│   └── test_resume_writer.py  # NEW — write_resume
├── integration/
│   └── .gitkeep               # untouched
└── e2e/
    └── .gitkeep               # untouched
```

### Pattern 1: Patching module-level imports

**What:** When a function under test calls `requests.get`, and `requests` was imported at
the top of `llm_client.py`, the patch target must be the name as it appears in the
module under test: `llm_client.requests.get`, not `requests.get`.

**When to use:** Every `_check_ollama_health()` test.

**Example:**
```python
# Source: src/llm_client_test.py (established pattern, confirmed by codebase inspection)
@patch("llm_client.requests.get")
def test_health_check_timeout_raises_runtime_error(mock_get):
    mock_get.side_effect = requests.Timeout("timed out")
    with pytest.raises(RuntimeError):
        _check_ollama_health()
```

### Pattern 2: MagicMock for successful health check

**What:** For the 200-OK path, the mock must survive `response.raise_for_status()` being
called without raising. `MagicMock` auto-stubs all method calls, so `raise_for_status()`
returns `None` by default — no explicit configuration needed beyond `status_code=200`.

**When to use:** The HTTP-200 / no-raise test for `_check_ollama_health()`.

**Example:**
```python
# Source: src/llm_client_test.py lines 61-62 (established pattern)
@patch("llm_client.requests.get")
def test_health_check_200_does_not_raise(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    _check_ollama_health()  # must not raise
```

### Pattern 3: HTTPError side_effect setup

**What:** `requests.HTTPError` is raised by `response.raise_for_status()`, not by
`requests.get()` itself. To simulate it, configure `raise_for_status` on the mock
response, not on the `get` call.

**When to use:** D-10 — the HTTPError path for `_check_ollama_health()`.

**Example:**
```python
# Source: derived from source code inspection of llm_client.py lines 17-23
import requests as req_lib

@patch("llm_client.requests.get")
def test_health_check_http_error_raises_runtime_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = req_lib.HTTPError("503")
    mock_get.return_value = mock_response
    with pytest.raises(RuntimeError):
        _check_ollama_health()
```

### Pattern 4: Pure function testing (_build_messages)

**What:** `_build_messages()` is a pure function — it takes two strings, builds a list of
dicts, returns it. No mocking needed. Call it directly, assert the return value.

**When to use:** All TEST-04 assertions.

**Example:**
```python
# Source: derived from source code inspection of llm_client.py lines 26-109
from llm_client import _build_messages

def test_build_messages_returns_two_element_list():
    result = _build_messages("resume text", "job description")
    assert len(result) == 2

def test_build_messages_role_ordering():
    result = _build_messages("resume text", "job description")
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"

def test_build_messages_system_contains_persona_tag():
    result = _build_messages("resume text", "job description")
    assert "<PERSONA>" in result[0]["content"]

def test_build_messages_system_contains_constraints_tag():
    result = _build_messages("resume text", "job description")
    assert "<CONSTRAINTS>" in result[0]["content"]

def test_build_messages_user_contains_job_description_xml():
    result = _build_messages("my resume", "python developer")
    assert "<job_description>" in result[1]["content"]
    assert "python developer" in result[1]["content"]

def test_build_messages_user_contains_resume_xml():
    result = _build_messages("my resume", "python developer")
    assert "<resume>" in result[1]["content"]
    assert "my resume" in result[1]["content"]
```

### Pattern 5: tmp_path for file I/O tests

**What:** `tmp_path` is a built-in pytest fixture that yields a fresh `pathlib.Path` to a
temporary directory per test. Use it directly — no import, no conftest entry needed.

**When to use:** `read_resume()` (create real file) and `write_resume()` (pass as
output_dir).

**Example:**
```python
# Source: pytest documentation; tmp_path is pytest core (ASSUMED)
import re
from resume_reader import read_resume
from resume_writer import write_resume

def test_read_resume_returns_content(tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text("\\documentclass{article}", encoding="utf-8")
    assert read_resume(resume_file) == "\\documentclass{article}"

def test_write_resume_filename_matches_pattern(tmp_path):
    result = write_resume("content", tmp_path)
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)

def test_write_resume_content_roundtrips(tmp_path):
    result = write_resume("\\documentclass{article}", tmp_path)
    assert result.read_text(encoding="utf-8") == "\\documentclass{article}"
```

### Anti-Patterns to Avoid

- **Patching `requests.get` instead of `llm_client.requests.get`:** The import is at the
  module level in `llm_client.py`; patching the wrong target leaves the real function
  reachable and causes actual network calls.
- **Mocking `datetime.now` for the timestamp test:** D-05 explicitly locks the approach
  as regex-match on `path.name`. Datetime mocking is more complex, fragile, and
  unnecessary given the pattern-match approach.
- **Adding `@pytest.mark.unit` to `src/*_test.py` files:** D-04 locks this out of scope.
  Adding markers to existing tests is not part of Phase 9.
- **Asserting exact prompt prose in `_build_messages` tests:** ROADMAP success criteria
  item 2 explicitly forbids this. Assert structural markers and XML tags only.
- **Using `conftest.py` Ollama fixtures in unit tests:** `require_ollama` is for
  integration/e2e tests. Unit tests must pass with zero Ollama dependency.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Temporary file/dir creation | Custom `os.makedirs` + `tempfile` setup/teardown | `tmp_path` (pytest fixture) | Built-in, auto-cleaned, yields a `Path` directly |
| HTTP error simulation | Custom subclass of `requests.HTTPError` | `side_effect = requests.HTTPError(...)` on mock | `MagicMock.side_effect` is the stdlib mock pattern; no subclassing needed |
| Regex timestamp validation | `datetime.strptime` parse attempt | `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", path.name)` | Locked per D-05; simpler, no false negatives from invalid date values |

**Key insight:** All the machinery needed (patch, MagicMock, tmp_path) ships with Python
and pytest. This phase is entirely about writing test logic, not wiring infrastructure.

## Common Pitfalls

### Pitfall 1: Wrong patch target for HTTPError

**What goes wrong:** `_check_ollama_health()` raises `HTTPError` via
`response.raise_for_status()`, not via `requests.get()`. Setting
`mock_get.side_effect = requests.HTTPError(...)` causes the mock to raise before the
function body even calls `raise_for_status()` — the test passes but tests the wrong code
path.

**Why it happens:** `ConnectionError` and `Timeout` are raised by `requests.get()` itself,
so `side_effect` on the mock is correct for those. `HTTPError` is raised by a method on
the response object — a different mock level.

**How to avoid:** For the `HTTPError` path, set the side_effect on `raise_for_status` of
the mock response object (see Pattern 3 above).

**Warning signs:** Test passes even when `except requests.HTTPError` block is deleted from
source.

### Pitfall 2: Missing `@pytest.mark.unit` marker

**What goes wrong:** `pytest --strict-markers` rejects any test that uses an undeclared
marker. An undecorated test runs fine with `pytest tests/unit/` but the required command
`pytest -m unit tests/unit/` collects zero tests.

**Why it happens:** `--strict-markers` is already in `addopts` (pyproject.toml line 43),
but a test without `@pytest.mark.unit` is simply not matched by `-m unit` — it doesn't
error, it's just silently excluded.

**How to avoid:** Apply `@pytest.mark.unit` to every test function in every new file.
Verify with `pytest -m unit tests/unit/ --co` before committing.

**Warning signs:** `pytest -m unit tests/unit/` collects 0 items despite files existing.

### Pitfall 3: read_resume FileNotFoundError wraps the original

**What goes wrong:** The source re-raises as a new `FileNotFoundError` with a custom
message (`raise FileNotFoundError(...) from exc`). A test that uses `pytest.raises` and
then inspects `excinfo.value.__cause__` may be surprised.

**Why it happens:** The function wraps: `except FileNotFoundError as exc: raise
FileNotFoundError(...) from exc`. The raised exception is a new `FileNotFoundError`
instance, not the original.

**How to avoid:** The test only needs `pytest.raises(FileNotFoundError)` — no need to
inspect the cause chain. Keep the assertion simple.

**Warning signs:** Test attempts `assert "not found" in str(excinfo.value)` and fails
because the custom message differs from the pattern expected.

### Pitfall 4: write_resume creates dir if missing — test must use a sub-path

**What goes wrong:** If the test passes `tmp_path` directly as `output_dir`, the directory
already exists and the "creates output directory" behavior is never exercised.

**Why it happens:** `tmp_path` is created before the test function runs. Passing it
directly means `mkdir(parents=True, exist_ok=True)` is a no-op.

**How to avoid:** Pass `tmp_path / "output"` (a subdirectory that does not yet exist) as
`output_dir`. The function will create it.

**Warning signs:** The `mkdir` call path is never hit; coverage shows it as uncovered.

## Code Examples

Verified patterns from official sources:

### Complete test_llm_client.py structure

```python
# Source: derived from codebase inspection of src/llm_client.py and src/llm_client_test.py
import pytest
import requests
from unittest.mock import MagicMock, patch

from llm_client import _build_messages, _check_ollama_health


@pytest.mark.unit
def test_build_messages_returns_two_element_list():
    result = _build_messages("resume text", "job description")
    assert len(result) == 2


@pytest.mark.unit
def test_build_messages_role_ordering():
    result = _build_messages("resume text", "job description")
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"


@pytest.mark.unit
def test_build_messages_system_contains_persona_tag():
    result = _build_messages("resume text", "job description")
    assert "<PERSONA>" in result[0]["content"]


@pytest.mark.unit
def test_build_messages_system_contains_constraints_tag():
    result = _build_messages("resume text", "job description")
    assert "<CONSTRAINTS>" in result[0]["content"]


@pytest.mark.unit
def test_build_messages_user_contains_job_description_xml_tag():
    result = _build_messages("resume text", "job description")
    assert "<job_description>" in result[1]["content"]


@pytest.mark.unit
def test_build_messages_user_embeds_job_description_content():
    result = _build_messages("resume text", "python developer")
    assert "python developer" in result[1]["content"]


@pytest.mark.unit
def test_build_messages_user_contains_resume_xml_tag():
    result = _build_messages("resume text", "job description")
    assert "<resume>" in result[1]["content"]


@pytest.mark.unit
def test_build_messages_user_embeds_resume_content():
    result = _build_messages("my specific resume", "job description")
    assert "my specific resume" in result[1]["content"]


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


@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_http_error_raises_runtime_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("503")
    mock_get.return_value = mock_response
    with pytest.raises(RuntimeError):
        _check_ollama_health()


@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_200_does_not_raise(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    _check_ollama_health()
```

### Complete test_resume_reader.py structure

```python
# Source: derived from codebase inspection of src/resume_reader.py
import pytest
from pathlib import Path

from resume_reader import read_resume


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

### Complete test_resume_writer.py structure

```python
# Source: derived from codebase inspection of src/resume_writer.py
import re
import pytest
from pathlib import Path

from resume_writer import write_resume


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

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pytest.ini` or `setup.cfg` for pytest config | `pyproject.toml [tool.pytest.ini_options]` | pytest 6+ | Already in use in this project |
| `tempfile.mkdtemp()` + manual cleanup | `tmp_path` fixture | pytest 3.9+ | Already available; no setup needed |

**Deprecated/outdated:**
- `@pytest.yield_fixture`: Replaced by `@pytest.fixture` with `yield`. Not applicable here
  but noted for completeness.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `tmp_path` fixture behavior (auto-cleanup, yields fresh dir per test) | Code Examples, Pattern 5 | LOW — well-documented pytest feature; behavior unchanged since pytest 3.9 |
| A2 | `MagicMock()` auto-stubs `raise_for_status()` as a no-op by default | Pattern 2 | LOW — confirmed by codebase usage in `src/llm_client_test.py` lines 62, 67, 73 where `raise_for_status.return_value = None` is set explicitly on some mocks; Pattern 2 relies on the default MagicMock behavior being a no-op, which is standard |

**Note on A2:** Existing test code sometimes sets `mock_response.raise_for_status.return_value = None` explicitly (lines 67, 73, 80). For the 200-OK health check test, using `MagicMock(status_code=200)` without an explicit `raise_for_status` config also works because `MagicMock` auto-creates attribute methods. To be safe and match the established style, consider setting `mock_response.raise_for_status.return_value = None` explicitly.

## Open Questions

1. **Should the health check 200 test assert the return value is `None`?**
   - What we know: `_check_ollama_health()` has no `return` statement, so it returns
     `None` implicitly.
   - What's unclear: Whether ROADMAP success criteria "does not raise" is sufficient or
     if an explicit `assert result is None` adds value.
   - Recommendation: Add `assert _check_ollama_health() is None` for explicitness —
     documents the contract without adding complexity.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All tests | Yes | 3.11.2 (system) / 3.13+ (uv venv) | — |
| pytest | Test runner | Yes | 9.0.3 (uv run pytest) | — |
| requests | side_effect values | Yes | pinned >=2.32.0 in pyproject.toml | — |
| uv | Run tests | Yes | 0.11.17 | `python3 -m pytest` fallback |

**Missing dependencies with no fallback:** None — all present.

**Run command:** `uv run pytest -m unit tests/unit/`

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest -m unit tests/unit/ -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-04 | `_build_messages()` returns 2-element list, correct role order, XML tags present | unit | `uv run pytest -m unit tests/unit/test_llm_client.py -x` | No — Wave 0 |
| TEST-05 | `_check_ollama_health()` raises RuntimeError on ConnectionError, Timeout; no raise on 200 | unit | `uv run pytest -m unit tests/unit/test_llm_client.py -x` | No — Wave 0 |
| TEST-06 | `read_resume()` returns content when file exists; raises FileNotFoundError when not | unit | `uv run pytest -m unit tests/unit/test_resume_reader.py -x` | No — Wave 0 |
| TEST-07 | `write_resume()` creates dir, returns Path, filename matches pattern, content roundtrips | unit | `uv run pytest -m unit tests/unit/test_resume_writer.py -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest -m unit tests/unit/ -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_llm_client.py` — covers TEST-04 and TEST-05
- [ ] `tests/unit/test_resume_reader.py` — covers TEST-06
- [ ] `tests/unit/test_resume_writer.py` — covers TEST-07

*(All three files must be created in Wave 1 — they are the phase deliverable.)*

## Security Domain

Security enforcement applies but this phase has no security-relevant surface. All changes
are test-only files in `tests/unit/`. No input validation, authentication, cryptography,
or external service calls are introduced. ASVS categories V2–V6 do not apply.

## Sources

### Primary (HIGH confidence)
- Codebase: `src/llm_client.py` — inspected directly; all function signatures, exception
  types, and XML tag names verified
- Codebase: `src/resume_reader.py` — inspected directly; exception chain behavior confirmed
- Codebase: `src/resume_writer.py` — inspected directly; `datetime.strftime` format
  confirmed
- Codebase: `src/llm_client_test.py` — inspected directly; patch target pattern
  `llm_client.requests.get` and `MagicMock(status_code=200)` pattern confirmed
- Codebase: `pyproject.toml` — inspected directly; pytest config, markers, addopts
  confirmed
- Codebase: `tests/conftest.py` — inspected directly; no unit-test fixtures; `tmp_path`
  confirmed as built-in

### Secondary (MEDIUM confidence)
- None required — all information sourced directly from the codebase

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools confirmed present in pyproject.toml and `uv run pytest --version`
- Architecture: HIGH — all source functions inspected directly; signatures, exception types, and tag names are facts, not estimates
- Pitfalls: HIGH — derived from direct source code inspection, not training data

**Research date:** 2026-06-04
**Valid until:** Stable indefinitely — no external dependencies; only changes if source files change
