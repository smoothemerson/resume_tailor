# Phase 10: Integration Tests - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Write two integration tests in `tests/integration/test_llm_client.py` that make real Ollama calls — TEST-08 verifies `_check_ollama_health()` does not raise when Ollama is running, TEST-09 verifies `generate_tailored_resume()` returns structurally valid LaTeX. Both tests skip gracefully when Ollama is absent. Requirements TEST-08 and TEST-09.

</domain>

<decisions>
## Implementation Decisions

### Minimal Resume Fixture
- **D-01:** Use a bare-bones inline fixture — `\documentclass{article}\begin{document}\section{Summary}AI engineer with 3 years experience.\end{document}` — to minimize inference time.
- **D-02:** Define the fixture as a module-level string constant (`MINIMAL_RESUME`) inside `tests/integration/test_llm_client.py`. No conftest.py shared fixture — Phase 11 defines its own when needed.

### TEST-08 Scope
- **D-03:** TEST-08 calls `_check_ollama_health()` directly and asserts no exception is raised. This tests our function's behavior against live Ollama — the integration complement to Phase 9's mocked unit test. Does NOT hit `/api/tags` raw (that's already what `ollama_available` in conftest.py does).

### TEST-09 Assertion Depth
- **D-04:** TEST-09 makes all four assertions on the `TailorResult`:
  1. `result.content.lstrip().startswith("\\documentclass")`
  2. `result.content.rstrip().endswith("\\end{document}")`
  3. `"```" not in result.content`
  4. `result.fences_stripped == False`
- **D-05:** Both tests carry `@pytest.mark.integration` — required for `pytest -m integration` to select them.

### Skip Behavior
- **D-06:** Both tests use the `require_ollama` fixture from `tests/conftest.py` to skip (not fail) when Ollama is unreachable. No new fixture needed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/ROADMAP.md` §Phase 10 — Goal, success criteria (3 items), requirements list (TEST-08, TEST-09)
- `.planning/REQUIREMENTS.md` §Integration Tests — Full requirement text for TEST-08, TEST-09

### Source Files (read before writing tests)
- `src/llm_client.py` — Contains `_check_ollama_health()` and `generate_tailored_resume()` — inspect signatures, exception types, and `TailorResult` NamedTuple before writing tests
- `src/config.py` — Contains `OLLAMA_BASE_URL` and `OLLAMA_MODEL` constants used in tests
- `tests/conftest.py` — Provides `ollama_available` and `require_ollama` fixtures; `require_ollama` is the skip mechanism for both tests

### Prior Phase Context (test infrastructure decisions)
- `.planning/phases/08-test-infrastructure/08-CONTEXT.md` — pytest config, directory layout, and marker definitions
- `.planning/phases/09-unit-test-gaps/09-CONTEXT.md` — naming conventions (`test_*.py` prefix, `@pytest.mark.unit`), patch patterns, and raise-not-exit pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/conftest.py` `require_ollama` fixture — session-scoped; accepts it as a function arg to auto-skip when Ollama is down
- `tests/integration/` directory — already exists (created in Phase 8), currently empty
- `TailorResult` NamedTuple in `src/llm_client.py`: fields are `.content` (str) and `.fences_stripped` (bool)

### Established Patterns
- **`@pytest.mark.integration` on every test** — required by `pyproject.toml` `--strict-markers` + `pytest -m integration` success criterion
- **raise-not-exit pattern**: `_check_ollama_health()` raises `RuntimeError` on failure; `generate_tailored_resume()` raises `RuntimeError`/`ValueError`. Tests call functions directly.
- **No `__init__.py` in tests/**: bare directory layout; `pythonpath = ["src"]` in pyproject.toml handles imports.

### Integration Points
- `tests/integration/test_llm_client.py` is a new file — no existing file to update
- `pyproject.toml` already includes `testpaths = ["src", "tests"]` — no changes needed

</code_context>

<specifics>
## Specific Ideas

- `MINIMAL_RESUME` constant shape:
  ```python
  MINIMAL_RESUME = (
      "\\documentclass{article}\n"
      "\\begin{document}\n"
      "\\section{Summary}\n"
      "AI engineer with 3 years experience.\n"
      "\\end{document}"
  )
  ```
- Minimal JD string for TEST-09: a short inline string like `"Python backend engineer with REST API experience"` — no need to read from a file.
- TEST-08 test body: `_check_ollama_health()` with no assertion needed — if it doesn't raise, the test passes.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-Integration Tests*
*Context gathered: 2026-06-05*
