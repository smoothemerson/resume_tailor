# Phase 8: Test Infrastructure - Research

**Researched:** 2026-06-02
**Domain:** pytest configuration, fixture design, test directory layout
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `src/cli_test.py` and `src/llm_client_test.py` stay in `src/` — not moved to `tests/`. The `testpaths = ["src", "tests"]` config ensures pytest discovers them.
- **D-02:** The `sys.path.insert(0, str(Path(__file__).parent))` hacks in both files are **removed** as part of this phase. With `pythonpath = ["src"]` in pytest config, pytest handles path setup automatically — the hacks are redundant and would confuse future test authors.
- **D-03:** Create `tests/unit/`, `tests/integration/`, `tests/e2e/` as **bare directories** (no `__init__.py`). Rootdir-relative layout — pytest's recommended approach for new projects. Avoids module name collisions. No placeholder test files needed.
- **D-04:** `tests/conftest.py` is the only new Python file created in Phase 8 (besides the empty dirs).
- **D-05:** Add the following section to `pyproject.toml` (per TEST-01):
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
- **D-06:** `ollama_available` is a **session-scoped** fixture that performs a single HTTP GET to Ollama's health endpoint and returns `True`/`False`. Runs once per test session.
- **D-07:** The fixture imports `OLLAMA_BASE_URL` from `config` (not hardcoded). Health check endpoint: `f"{OLLAMA_BASE_URL}/api/tags"`.
- **D-08:** `require_ollama` is a **function-scoped** fixture that calls `pytest.skip("Ollama not available")` when `ollama_available` returns `False`. Tests that need Ollama declare `require_ollama` as a fixture parameter.

### Claude's Discretion

None — all areas had clear user decisions.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | pytest configured in pyproject.toml — testpaths includes both `src` and `tests`, pythonpath set to `["src"]`, three markers registered (`unit`, `integration`, `e2e`), `--strict-markers` and `-ra` in addopts | Verified: exact config format tested against pytest 9.0.3 on this machine |
| TEST-02 | `tests/conftest.py` provides a session-scoped `ollama_available` fixture (HTTP probe, runs once per session) and a `require_ollama` fixture that skips the test when Ollama is unreachable | Verified: fixture pattern tested; exit code 0 with SKIPPED confirmed |
| TEST-03 | `tests/` organized into `unit/`, `integration/`, and `e2e/` subdirectories; existing `src/*_test.py` files left in place | Verified: bare directories with no `__init__.py`, rootdir-relative layout |
</phase_requirements>

## Summary

Phase 8 is a pure configuration and scaffolding phase. No new packages are installed — pytest 9.0.3 is already in the project's dev dependencies. The work is: (1) add `[tool.pytest.ini_options]` to `pyproject.toml`, (2) remove the now-redundant `sys.path.insert` hacks from two existing test files, (3) create three empty test subdirectories under `tests/`, and (4) create `tests/conftest.py` with two fixtures.

All three success criteria have been verified live against the actual environment. The 18 existing tests collected in 0.07s with no warnings. The `require_ollama` fixture pattern produces exit code 0 with SKIPPED (not FAILED) when Ollama is down. The `--strict-markers` + marker registration combination causes collection-time errors (exit 2) when test code uses an unregistered marker, and exit 5 (non-zero) when `-m foo` filters to an empty selection.

The project is already installed in editable mode via `uv sync`, so `src/` is on `sys.path` through the `.pth` file in the venv. The `sys.path.insert` hacks are therefore doubly redundant: they existed before the editable install was set up and add `src/` a second time. The `pythonpath = ["src"]` pytest config makes this explicit and guarantees correctness even when running pytest outside the venv.

**Primary recommendation:** Implement in the order: pyproject.toml first (so all subsequent pytest invocations use the registered config), then conftest.py, then directory creation, then sys.path cleanup last (to verify tests still pass).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Test configuration | pyproject.toml | — | pytest reads ini options from `[tool.pytest.ini_options]` at project root |
| Ollama availability probe | tests/conftest.py (session fixture) | — | Session-scoped = runs once, not on every test; conftest.py = auto-loaded by pytest |
| Skip-when-down guard | tests/conftest.py (function fixture) | — | Function-scoped so each test that needs Ollama declares it explicitly |
| Test discovery (src/) | pytest testpaths config | sys.path via editable install | Already works; `testpaths = ["src", "tests"]` makes it explicit |
| Test discovery (tests/) | pytest testpaths config | — | Empty dirs require no special config; pytest traverses and finds nothing |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.3 [VERIFIED: npm registry] | Test runner, fixture system, marker system | Already installed in dev deps; the standard Python test runner |
| requests | 2.34.2 [VERIFIED: pypi] | HTTP probe in conftest.py `ollama_available` fixture | Already a project dependency; the only HTTP client permitted by project constraints |

No new packages required for this phase.

## Package Legitimacy Audit

No new packages are installed in Phase 8. pytest 9.0.3 and requests 2.34.2 are existing project dependencies confirmed via `uv run pytest --version` and `uv run python -c "import requests; print(requests.__version__)"`. No slopcheck required.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
pyproject.toml [tool.pytest.ini_options]
  ├── testpaths = ["src", "tests"]
  │     ├── src/cli_test.py          (18 existing tests, unittest-style)
  │     ├── src/llm_client_test.py   (unittest-style)
  │     └── tests/
  │           ├── conftest.py        (ollama_available, require_ollama fixtures)
  │           ├── unit/              (empty — Phase 9 populates)
  │           ├── integration/       (empty — Phase 10 populates)
  │           └── e2e/              (empty — Phase 11 populates)
  ├── pythonpath = ["src"]           (guarantees src imports without hacks)
  ├── markers = [unit, integration, e2e]
  └── addopts = "--strict-markers -ra"

conftest.py fixture chain:
  ollama_available (session-scoped)
    └── require_ollama (function-scoped)
          └── pytest.skip() if not available
```

### Recommended Project Structure
```
workspace/
├── pyproject.toml         # add [tool.pytest.ini_options] section
├── src/
│   ├── cli_test.py        # remove line 6 only (sys.path.insert)
│   ├── llm_client_test.py # remove lines 1, 3, 6 (sys/Path imports + sys.path.insert)
│   ├── config.py          # unchanged — exports OLLAMA_BASE_URL
│   └── ...
└── tests/
    ├── conftest.py        # new: ollama_available + require_ollama fixtures
    ├── unit/              # new: empty directory
    ├── integration/       # new: empty directory
    └── e2e/               # new: empty directory
```

### Pattern 1: pytest ini_options in pyproject.toml

**What:** Configures pytest via `[tool.pytest.ini_options]` in `pyproject.toml`. The TOML string format for `addopts` is valid (confirmed via live test).
**When to use:** Always for modern Python projects using pyproject.toml.
**Example:**
```toml
# Source: verified live against pytest 9.0.3
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

### Pattern 2: Session-scoped availability fixture + function-scoped skip guard

**What:** Two-fixture pattern: one expensive session-scoped probe, one cheap function-scoped skip. Tests only request the skip guard, not the probe directly.
**When to use:** Any external service that is optional during testing (Ollama, databases, APIs).
**Example:**
```python
# Source: verified live against pytest 9.0.3; pattern from pytest docs
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

### Pattern 3: Minimal sys.path cleanup per file

**What:** Remove only the lines that are actually unnecessary. Different lines need removing in each file.
**When to use:** When removing path hacks — verify other usages before deleting imports.

For `src/cli_test.py` — remove ONE line only:
```python
# REMOVE this line (line 6):
sys.path.insert(0, str(Path(__file__).parent))

# KEEP: import sys   (used by @patch("sys.argv"))
# KEEP: from pathlib import Path   (used by Path("/tmp/tailored_resume_test.tex"))
```

For `src/llm_client_test.py` — remove THREE lines:
```python
# REMOVE line 1:
import sys
# REMOVE line 3:
from pathlib import Path
# REMOVE line 6:
sys.path.insert(0, str(Path(__file__).parent))
# (neither sys nor Path is used anywhere else in this file)
```

### Anti-Patterns to Avoid

- **Removing the wrong imports:** `cli_test.py` uses `sys` (for `@patch("sys.argv")`) and `Path` (for mock return values) — do not remove these imports, only remove the `sys.path.insert` call.
- **Adding `__init__.py` to test directories:** Rootdir-relative layout (no `__init__.py`) is the recommended pytest approach for new projects. Adding `__init__.py` switches to package mode, which can cause module name conflicts across subdirectories.
- **Hardcoding Ollama URL in conftest.py:** Always import `OLLAMA_BASE_URL` from `config` — the production code already owns that URL as its single source of truth.
- **Making `require_ollama` session-scoped:** It must be function-scoped (the default) so individual tests can be skipped independently. If session-scoped, one skip skips all remaining tests.
- **Using `autouse=True` on `require_ollama`:** Tests must opt-in by declaring the fixture parameter. Autouse would skip ALL tests under tests/ when Ollama is down, including unit tests that don't need it.
- **Adding placeholder test files to empty directories:** Empty directories work fine — pytest traverses them, finds nothing, and continues without warnings. Placeholder files create noise in `pytest --co` output.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ollama availability probe | Custom socket check, subprocess ping | `requests.get(..., timeout=3)` + catch `ConnectionError` | Requests is already a dependency; this is the idiomatic Python approach; matches what production code does |
| Marker enforcement | Custom validation in conftest.py | `--strict-markers` in addopts | pytest's built-in mechanism; catches marker typos at collection time, not at runtime |
| sys.path management | `sys.path.insert` in every test file | `pythonpath = ["src"]` in pytest config | One config entry covers all test files past and future; per-file hacks accumulate over time |

**Key insight:** All problems in this phase already have standard pytest solutions. The phase is entirely configuration, not implementation.

## Common Pitfalls

### Pitfall 1: conftest.py not visible to src/*_test.py tests

**What goes wrong:** Fixtures defined in `tests/conftest.py` are NOT visible to `src/cli_test.py` or `src/llm_client_test.py`. pytest's conftest.py discovery only propagates DOWN a directory tree, not laterally.
**Why it happens:** conftest.py files serve the directory they are in and all subdirectories. `tests/conftest.py` serves `tests/unit/`, `tests/integration/`, `tests/e2e/` — but not `src/`.
**How to avoid:** This is the intended design (per CONTEXT.md code_context note). The existing `src/*_test.py` tests are pure unit tests with no Ollama dependency, so they don't need the fixture. Integration and E2E tests live under `tests/` where they can see the fixture.
**Warning signs:** If a future test in `src/` needs `require_ollama`, it won't find it — the solution would be to move that test to `tests/integration/`.

### Pitfall 2: --strict-markers behavior with -m expression

**What goes wrong:** `pytest -m foo --strict-markers` with `foo` not in the registered markers does NOT exit with an error at collection time — it exits with code 5 (no tests collected) because the -m filter finds nothing. It only exits with code 2 (error) when a TEST is DECORATED with an unregistered marker (`@pytest.mark.badmarker`).
**Why it happens:** The `-m` expression is a filter on the collected tests, not a marker registration check. `--strict-markers` enforces that markers USED IN TEST DECORATORS are registered.
**How to avoid:** The success criterion "exits non-zero immediately" is satisfied by exit 5 (which is non-zero). The behavior is correct; the success criterion language is slightly imprecise. Both exit 2 (unregistered decorator) and exit 5 (no matching tests) are non-zero.
**Warning signs:** None — this is correct behavior.

### Pitfall 3: testpaths includes non-existent directory

**What goes wrong:** If `tests/` doesn't exist when `testpaths = ["src", "tests"]` is configured, pytest still works — it finds the 18 tests in `src/` and reports them. The missing `tests/` directory is not an error.
**Why it happens:** pytest silently skips testpaths entries that don't exist.
**How to avoid:** Create `tests/` directories before or after adding the config — either order is safe. Recommended: add config first, create dirs second, run `pytest --co` to verify.
**Warning signs:** Running `pytest --co` after config but before dirs shows only 18 tests, not 0 — this is correct.

### Pitfall 4: Wrong removal in llm_client_test.py

**What goes wrong:** Removing only `sys.path.insert` but leaving `from pathlib import Path` and `import sys` — these become unused imports that ruff will flag.
**Why it happens:** Both files have the same pattern at lines 1, 3, and 6, but `cli_test.py` still uses `sys` and `Path` elsewhere while `llm_client_test.py` does not.
**How to avoid:** After removing `sys.path.insert` from `llm_client_test.py`, also remove lines 1 (`import sys`) and 3 (`from pathlib import Path`) since neither is used elsewhere.
**Warning signs:** `uv run ruff check src/llm_client_test.py` will report `F401 'sys' imported but unused` and `F401 'pathlib.Path' imported but unused`.

### Pitfall 5: Fixture timeout for Ollama probe

**What goes wrong:** Using no timeout in `requests.get` for the `ollama_available` fixture — if Ollama is starting up slowly, the fixture hangs the test session.
**Why it happens:** `requests.get` without timeout blocks indefinitely.
**How to avoid:** Use `timeout=3` (3 seconds) for the health probe. This is shorter than production's `TIMEOUT[0] = 10` — fast enough for a test probe, not so fast it false-negatives a slow start.
**Warning signs:** Test suite hangs at session setup for > 5 seconds when Ollama is starting.

## Code Examples

Verified patterns from live testing:

### tests/conftest.py (complete)
```python
# Source: verified live against pytest 9.0.3; decisions per 08-CONTEXT.md D-06/D-07/D-08
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

### pyproject.toml addition (complete section)
```toml
# Source: verified format against pytest 9.0.3; from 08-CONTEXT.md D-05
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

### cli_test.py after cleanup (changed lines only)
```python
# Before (line 6): sys.path.insert(0, str(Path(__file__).parent))
# After: (line removed entirely)
# Lines 1 and 3 (import sys, from pathlib import Path) remain unchanged
```

### llm_client_test.py after cleanup (removed lines)
```python
# Before line 1:  import sys           <- REMOVE
# Before line 3:  from pathlib import Path  <- REMOVE
# Before line 6:  sys.path.insert(0, str(Path(__file__).parent))  <- REMOVE
# Everything else unchanged
```

### Creating empty test directories
```bash
mkdir -p tests/unit tests/integration tests/e2e
# No __init__.py -- rootdir-relative layout per D-03
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `sys.path.insert` in each test file | `pythonpath = ["src"]` in pytest config | pytest 7.0 (2022) | One config replaces per-file hacks |
| `pytest.ini` or `setup.cfg` | `[tool.pytest.ini_options]` in `pyproject.toml` | pytest 6.0 (2020) | Single pyproject.toml for all tooling |
| `requirements.txt` for dev tools | `[dependency-groups] dev = [...]` in `pyproject.toml` | PEP 735 / uv support 2024 | Already used in this project |

**Deprecated/outdated:**
- `pytest.ini` as a separate file: still works but `pyproject.toml` is the modern location
- `sys.path.insert` hacks in test files: redundant with `pythonpath = ["src"]`
- `__init__.py` in test directories: package mode is rarely needed; rootdir-relative is simpler

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `timeout=3` for health probe is appropriate | Code Examples | Low — if too short, increase to 5; the decision is not locked |
| A2 | The health endpoint `/api/tags` is stable and returns 200 when Ollama is running | Code Examples | Low — if endpoint changes, update conftest.py; production code already uses this endpoint |

**Note:** Both assumptions are low-risk implementation details not covered by locked decisions. A1 is a sensible default; A2 is consistent with production code in `llm_client.py`.

## Open Questions (RESOLVED)

1. **Timeout value for ollama_available fixture** — RESOLVED: D-07 locks `timeout=3`
   - What we know: production code uses `TIMEOUT[0] = 10` seconds; decisions don't specify
   - Resolution: CONTEXT.md D-07 locks the health probe endpoint as `f"{OLLAMA_BASE_URL}/api/tags"` with `timeout=3`; this is the authoritative value

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | Test runner | Yes | 9.0.3 | — |
| requests | conftest.py health probe | Yes | 2.34.2 | — |
| uv | Running tests via `uv run pytest` | Yes | (installed) | `python -m pytest` if venv activated |
| Ollama | TEST-02 skip fixture | No | — | Tests skip (not fail) — correct behavior |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** Ollama is not running — the skip fixture handles this correctly.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (added in this phase) |
| Quick run command | `uv run pytest --co -q` |
| Full suite command | `uv run pytest -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | `pytest --co` discovers 18 tests, no warnings, exit 0 | smoke | `uv run pytest --co -q` | n/a — this IS the test |
| TEST-01 | `pytest -m foo` exits non-zero with strict-markers | smoke | `uv run pytest -m foo; test $? -ne 0` | n/a — this IS the test |
| TEST-02 | Integration tests skip (exit 0) when Ollama is down | smoke | `uv run pytest -m integration` (with Ollama down) | ❌ Wave 0 — tests/conftest.py |
| TEST-03 | `tests/unit/`, `tests/integration/`, `tests/e2e/` exist | structural | `ls tests/unit tests/integration tests/e2e` | ❌ Wave 0 — create dirs |

### Sampling Rate

- **Per task commit:** `uv run pytest --co -q` (collect-only, < 1s)
- **Per wave merge:** `uv run pytest -v` (full suite, ~0.15s for 18 tests)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/conftest.py` — provides `ollama_available` and `require_ollama` fixtures (REQ TEST-02)
- [ ] `tests/unit/` directory — empty (REQ TEST-03)
- [ ] `tests/integration/` directory — empty (REQ TEST-03)
- [ ] `tests/e2e/` directory — empty (REQ TEST-03)
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` section — configuration (REQ TEST-01)

## Security Domain

This phase introduces no authentication, network services, user input handling, or data storage. The only external call is a read-only HTTP GET to `localhost:11434` (an optional probe). No ASVS categories apply.

## Sources

### Primary (HIGH confidence)
- pytest 9.0.3 installed at `/workspace/.venv/bin/pytest` — all behaviors verified via live `uv run pytest` invocations
- `pyproject.toml` `[tool.pytest.ini_options]` — verified format via temp config file test against live pytest
- Official pytest docs: https://docs.pytest.org/en/9.0.x/reference/customize.html — configuration options confirmed

### Secondary (MEDIUM confidence)
- pytest fixture scoping: https://docs.pytest.org/en/9.0.x/how-to/fixtures.html — session-scope and conftest.py discovery rules
- Editable install `.pth` file at `/workspace/.venv/lib/python3.14/site-packages/_editable_impl_resume_tailor.pth` — verified why current sys.path.insert is redundant

### Tertiary (LOW confidence / ASSUMED)
- A1 (timeout=3): from first principles, not from documented standard

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; pytest 9.0.3 already installed and verified
- Architecture: HIGH — all decisions locked in CONTEXT.md; no alternatives to evaluate
- Pitfalls: HIGH — most pitfalls verified live via `uv run pytest` invocations
- Fixture pattern: HIGH — skip behavior (exit 0, SKIPPED) verified live

**Research date:** 2026-06-02
**Valid until:** 2026-12-02 (pytest 9.x is stable; no moving targets in this phase)
