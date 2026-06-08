# Phase 8: Test Infrastructure - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Configure pytest (pyproject.toml), create the `tests/` directory hierarchy (`unit/`, `integration/`, `e2e/`), and provide the Ollama skip fixture in `tests/conftest.py` — so that all test layers in Phases 9-11 can be added without any additional setup work. Existing `src/*_test.py` files are left in place (moved only internally to remove the now-redundant sys.path hacks).

</domain>

<decisions>
## Implementation Decisions

### Existing test files (src/*_test.py)
- **D-01:** `src/cli_test.py` and `src/llm_client_test.py` stay in `src/` — not moved to `tests/`. The `testpaths = ["src", "tests"]` config ensures pytest discovers them.
- **D-02:** The `sys.path.insert(0, str(Path(__file__).parent))` hacks in both files are **removed** as part of this phase. With `pythonpath = ["src"]` in pytest config, pytest handles path setup automatically — the hacks are redundant and would confuse future test authors.

### tests/ directory structure
- **D-03:** Create `tests/unit/`, `tests/integration/`, `tests/e2e/` as **bare directories** (no `__init__.py`). Rootdir-relative layout — pytest's recommended approach for new projects. Avoids module name collisions (two `test_client.py` in different subdirs both work). No placeholder test files needed; pytest traverses the dirs and finds nothing without warnings.
- **D-04:** `tests/conftest.py` is the only new Python file created in Phase 8 (besides the empty dirs).

### pytest configuration (pyproject.toml [tool.pytest.ini_options])
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

### Ollama fixture (tests/conftest.py)
- **D-06:** `ollama_available` is a **session-scoped** fixture that performs a single HTTP GET to Ollama's health endpoint and returns `True`/`False`. Runs once per test session.
- **D-07:** The fixture imports `OLLAMA_BASE_URL` from `config` (not hardcoded). Note: the config constant is named `OLLAMA_BASE_URL`, not `OLLAMA_URL`. Health check endpoint: `f"{OLLAMA_BASE_URL}/"` (or `/api/tags`).
- **D-08:** `require_ollama` is a **function-scoped** fixture that calls `pytest.skip("Ollama not available")` when `ollama_available` returns `False`. Tests that need Ollama declare `require_ollama` as a fixture parameter.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/ROADMAP.md` §Phase 8 — Goal, success criteria, requirements list (TEST-01, TEST-02, TEST-03)
- `.planning/REQUIREMENTS.md` §Test Infrastructure — Full requirement text for TEST-01, TEST-02, TEST-03

### Source Files (must read before planning)
- `src/config.py` — Exports `OLLAMA_BASE_URL` (the constant the conftest fixture must import; confirm exact name)
- `src/cli_test.py` — Existing unittest-style tests in `src/`; remove `sys.path.insert()` hack per D-02
- `src/llm_client_test.py` — Existing unittest-style tests in `src/`; remove `sys.path.insert()` hack per D-02
- `pyproject.toml` — Add `[tool.pytest.ini_options]` section per D-05

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `OLLAMA_BASE_URL` in `src/config.py` — single source of truth for Ollama URL; conftest must import this rather than hardcoding

### Established Patterns
- **raise-not-exit pattern**: `llm_client.py` raises errors, `cli.py` handles exits — test isolation is already designed in; unit tests can mock freely without sys.exit side effects
- **`sys.stderr` for errors**: existing tests use `patch("builtins.print")` — pattern to follow for new unit tests in Phase 9

### Integration Points
- `pyproject.toml` — new `[tool.pytest.ini_options]` section added here
- `tests/conftest.py` — new file; fixtures declared here are available to all tests under `tests/`; `src/*_test.py` tests do NOT see this conftest (conftest.py is only inherited by tests in its directory subtree and below)
- `src/cli_test.py` and `src/llm_client_test.py` — minimal changes: only `sys.path.insert()` line removed

### Fixture scope note
`tests/conftest.py` fixtures are NOT visible to `src/*_test.py` tests. This is fine for Phase 8 since the existing tests are pure unit tests with no Ollama dependency. Integration and E2E tests (Phases 10-11) will live under `tests/`, where they can see the fixture.

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard pytest patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 8-Test Infrastructure*
*Context gathered: 2026-06-02*
