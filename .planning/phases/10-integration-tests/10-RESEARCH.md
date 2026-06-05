# Phase 10: Integration Tests - Research

**Researched:** 2026-06-05
**Domain:** pytest integration testing with live Ollama dependency; skip-on-absent fixture pattern
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Minimal fixture is a bare-bones inline string constant: `\documentclass{article}\begin{document}\section{Summary}AI engineer with 3 years experience.\end{document}` — minimizes inference time.
- **D-02:** Fixture defined as a module-level string constant `MINIMAL_RESUME` inside `tests/integration/test_llm_client.py`. No conftest.py shared fixture.
- **D-03:** TEST-08 calls `_check_ollama_health()` directly and asserts no exception is raised — integration complement to Phase 9's mocked unit test.
- **D-04:** TEST-09 makes all four assertions on the `TailorResult`: `result.content.lstrip().startswith("\\documentclass")`, `result.content.rstrip().endswith("\\end{document}")`, `"```" not in result.content`, `result.fences_stripped == False`.
- **D-05:** Both tests carry `@pytest.mark.integration` — required for `pytest -m integration` selection.
- **D-06:** Both tests use the `require_ollama` fixture from `tests/conftest.py` to skip when Ollama is unreachable. No new fixture needed.

### Claude's Discretion

None specified.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-08 | Integration test: Ollama health endpoint returns 200 when Ollama is running; test skipped (not failed) when Ollama is unreachable | `_check_ollama_health()` raises `RuntimeError` on any failure path; `require_ollama` fixture calls `pytest.skip()` before the test body runs; no assertion needed in test body beyond "does not raise" |
| TEST-09 | Integration test: `generate_tailored_resume()` with minimal synthetic resume and short JD returns string starting with `\documentclass` and ending with `\end{document}` with no markdown fences; skipped when Ollama unreachable | `generate_tailored_resume()` already calls `_validate_latex()` internally but tests must assert the four invariants from D-04 to validate from the caller's perspective; `TailorResult.fences_stripped` is the flag to check for fence presence |
</phase_requirements>

## Summary

Phase 10 creates a single new file: `tests/integration/test_llm_client.py`. The file contains exactly two test functions — one covering TEST-08 (`_check_ollama_health()` live call) and one covering TEST-09 (`generate_tailored_resume()` live call with structural invariant assertions). Both tests skip gracefully when Ollama is unreachable, using the already-present `require_ollama` fixture.

The implementation surface is minimal and fully constrained. All key design choices were locked in CONTEXT.md: the fixture shape, assertion depth, skip mechanism, and marker name. No new project infrastructure is needed — the test directory, pytest config, markers, and conftest fixtures all exist and are verified working via the Phase 8 and Phase 9 deliverables.

The only runtime uncertainty is Ollama availability and model behavior. Ollama is confirmed not running in the research environment (connection refused at `localhost:11434`), which means the skip path can be verified locally but the passing path requires a live Ollama. The TIMEOUT constant (`(10, 300)`) means `_check_ollama_health()` uses a 10-second connect timeout and `generate_tailored_resume()` uses a 300-second read timeout — the integration test must not override these, to avoid test-specific timeout configuration.

**Primary recommendation:** Write `tests/integration/test_llm_client.py` with two functions, a `MINIMAL_RESUME` module-level constant, and both functions accepting `require_ollama` as a parameter to trigger auto-skip.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Live Ollama health probe (TEST-08) | Test layer | API/Backend (llm_client.py) | Test calls the function that owns the HTTP probe; test layer only asserts the function contract |
| LaTeX structural validation (TEST-09) | Test layer | API/Backend (llm_client.py) | `generate_tailored_resume()` owns the actual call + internal validation; tests assert the external contract visible to callers |
| Skip-on-absent gating | Test infrastructure (conftest.py) | — | `require_ollama` fixture already lives in conftest.py; no test should re-implement this |

## Standard Stack

### Core

All dependencies are already installed. No new packages.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.3 (installed) | Test runner, fixture injection, marker system | Already in dev dependencies; provides `@pytest.mark.integration`, `pytest.skip()` |
| requests | 2.32.x (installed) | HTTP calls inside `_check_ollama_health()` and `generate_tailored_resume()` | Project constraint; already in production dependencies |

[VERIFIED: pyproject.toml] — versions confirmed from `/workspace/pyproject.toml` directly.

### Supporting

No additional supporting libraries required.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `require_ollama` fixture (conftest.py) | `pytest.importorskip` or manual `if not available: skip` | `require_ollama` is already established and session-scoped — using alternatives would duplicate logic and break the Phase 8 fixture contract |
| Module-level `MINIMAL_RESUME` constant | `@pytest.fixture` | A fixture for a string constant adds ceremony without benefit; D-02 locks this decision |
| Inline JD string | JD from a file | File I/O adds test fragility; inline string is sufficient and matches D-01 spirit |

**Installation:** No installation needed. All dependencies already present.

## Package Legitimacy Audit

No new packages are installed in this phase.

## Architecture Patterns

### System Architecture Diagram

```
pytest -m integration
        |
        v
[session-scoped ollama_available fixture]
  -- probes localhost:11434/api/tags once --
        |
   available?
   /        \
  YES        NO
  |           |
  v           v
[require_ollama]    [require_ollama]
  passes          calls pytest.skip()
  |                     |
  v                [SKIPPED - exit 0]
[test body runs]
  |
  +-- test_ollama_health_check_does_not_raise
  |     calls _check_ollama_health() directly
  |     asserts: no exception raised
  |
  +-- test_generate_tailored_resume_returns_valid_latex
        calls generate_tailored_resume(MINIMAL_RESUME, MINIMAL_JD)
        asserts:
          result.content.lstrip().startswith("\\documentclass")
          result.content.rstrip().endswith("\\end{document}")
          "```" not in result.content
          result.fences_stripped == False
```

### Recommended Project Structure

```
tests/
├── conftest.py              # ollama_available + require_ollama (already exists)
├── unit/
│   └── test_llm_client.py   # Phase 9 — mocked unit tests (already exists)
├── integration/
│   └── test_llm_client.py   # Phase 10 — THIS FILE (new)
└── e2e/
    └── .gitkeep             # Phase 11 (not yet started)
```

### Pattern 1: Integration Test with Conditional Skip via Fixture

**What:** A test function that accepts `require_ollama` as a parameter causes pytest to inject
the fixture. If Ollama is unavailable, the fixture body calls `pytest.skip()` before the test
body runs — the test is marked SKIPPED with a clear reason, and the process exits 0.

**When to use:** Any test that requires a live external dependency and must not fail when the
dependency is absent (CI without Ollama, developer machines without GPU).

```python
# Source: tests/conftest.py (existing), pattern confirmed from codebase
import pytest
from llm_client import _check_ollama_health

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)

@pytest.mark.integration
def test_ollama_health_check_does_not_raise(require_ollama):
    _check_ollama_health()
```

[VERIFIED: codebase] — `require_ollama` fixture confirmed in `tests/conftest.py`; `_check_ollama_health()` signature confirmed in `src/llm_client.py`.

### Pattern 2: TailorResult Structural Assertions

**What:** `generate_tailored_resume()` returns a `TailorResult(content: str, fences_stripped: bool)`. The four assertions from D-04 validate the caller-visible contract without asserting exact LLM output content.

**When to use:** Any integration test of `generate_tailored_resume()` — structural invariants are stable even as LLM output varies.

```python
# Source: src/llm_client.py (TailorResult definition), D-04 from CONTEXT.md
@pytest.mark.integration
def test_generate_tailored_resume_returns_valid_latex(require_ollama):
    MINIMAL_JD = "Python backend engineer with REST API experience"
    result = generate_tailored_resume(MINIMAL_RESUME, MINIMAL_JD)
    assert result.content.lstrip().startswith("\\documentclass")
    assert result.content.rstrip().endswith("\\end{document}")
    assert "```" not in result.content
    assert result.fences_stripped is False
```

[VERIFIED: codebase] — `TailorResult` fields `.content` and `.fences_stripped` confirmed in `src/llm_client.py` line 9-11.

### Anti-Patterns to Avoid

- **Asserting exact LLM output:** LLM response content is non-deterministic. Assert structural invariants only (starts with `\documentclass`, ends with `\end{document}`), never exact content.
- **Overriding TIMEOUT in tests:** `TIMEOUT = (10, 300)` is defined in `config.py`. Do not monkeypatch it in integration tests — the 300-second read timeout is intentional for slow local models.
- **Using `@pytest.fixture` for MINIMAL_RESUME:** D-02 locks this as a module-level constant. Fixtures are for objects with setup/teardown or shared mutable state — not for string constants.
- **Skipping via `pytest.importorskip` or `skipif`:** The established project pattern is `require_ollama` fixture injection. Using a different skip mechanism creates inconsistency with how Phase 8 defined the skip contract.
- **Adding `require_ollama` to conftest.py:** The fixture already exists there. Do not redefine it.
- **Calling `generate_tailored_resume()` without `require_ollama`:** Without the fixture, the test will attempt a real HTTP call and produce a hard failure (not a skip) when Ollama is down.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ollama availability check | Manual `try/except requests.get` inside the test | `require_ollama` fixture from conftest.py | Already exists, session-scoped (probe runs once), skip message is consistent |
| LaTeX structural validation | Custom regex inside test | Assert the four invariants from D-04 directly | `generate_tailored_resume()` already calls `_validate_latex()` internally; test only needs to verify the external contract |
| Minimal resume fixture | File-based fixture or `@pytest.fixture` | Module-level `MINIMAL_RESUME` constant | D-02 locks this; string constant is sufficient |

**Key insight:** The entire skip mechanism, Ollama probe, and test infrastructure was built in Phase 8. This phase is purely additive — add one file, do not modify any existing infrastructure.

## Common Pitfalls

### Pitfall 1: `fences_stripped` Assertion Fragility

**What goes wrong:** Asserting `result.fences_stripped is False` assumes the model returns clean LaTeX without markdown fences. If a model version or temperature setting causes the model to add fences, `generate_tailored_resume()` strips them and sets `fences_stripped = True`, causing the test to fail.

**Why it happens:** `fences_stripped` reflects actual model behavior, not a contract invariant. D-04 explicitly includes this assertion, so it is intentional — but it should be understood as testing the expected behavior of a well-configured model, not a structural invariant.

**How to avoid:** Accept D-04 as specified. If the assertion fails in CI, the root cause is model configuration, not a code bug. The assertion exists to detect model regression.

**Warning signs:** Test passes locally (Ollama running) but fails in CI (different model loaded).

### Pitfall 2: `require_ollama` is a Function-Scope Fixture

**What goes wrong:** `require_ollama` in `tests/conftest.py` has default (function) scope, while `ollama_available` is session-scoped. This means `require_ollama` is called once per test function, but the probe (`ollama_available`) only runs once per session. This is correct behavior, but confusing: each test function needs to accept `require_ollama` as a parameter individually.

**Why it happens:** Function scope is correct — the skip check must be evaluated per test. Session scope on the probe avoids repeated HTTP calls.

**How to avoid:** Both test functions must independently accept `require_ollama` as a parameter. Do not try to share it at module level or class level.

**Warning signs:** Only one of the two tests skips when Ollama is down.

### Pitfall 3: Import Path for `_check_ollama_health`

**What goes wrong:** `_check_ollama_health` is a private function (leading underscore). It is importable but some developers assume private functions should not be imported in tests.

**Why it happens:** Python convention — underscore prefix signals "internal", not "inaccessible". The unit tests in Phase 9 already import and test it directly (`from llm_client import _check_ollama_health`).

**How to avoid:** Import directly: `from llm_client import _check_ollama_health, generate_tailored_resume`. Same pattern as `tests/unit/test_llm_client.py`.

**Warning signs:** `ImportError` or overly indirect call path through `generate_tailored_resume()` for TEST-08.

### Pitfall 4: `tests/integration/` Has No `__init__.py`

**What goes wrong:** Adding an `__init__.py` to `tests/integration/` breaks the rootdir-relative import layout established in Phase 8.

**Why it happens:** Developers used to package-style layouts assume all directories need `__init__.py`.

**How to avoid:** Leave `tests/integration/` as a bare directory. `pythonpath = ["src"]` in pyproject.toml handles `from llm_client import ...` imports. No `__init__.py` needed anywhere in `tests/`.

**Warning signs:** `ModuleNotFoundError` for `llm_client` imports after adding `__init__.py`.

## Code Examples

### Complete `tests/integration/test_llm_client.py`

```python
# Source: CONTEXT.md D-01 through D-06, confirmed against src/llm_client.py
import pytest

from llm_client import _check_ollama_health, generate_tailored_resume

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)


@pytest.mark.integration
def test_ollama_health_check_does_not_raise(require_ollama):
    _check_ollama_health()


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

[VERIFIED: codebase] — function signatures, `TailorResult` fields, and fixture names all confirmed from source files.

### Running integration tests

```bash
# Run only integration tests (requires Ollama running)
uv run pytest -m integration

# Run with verbose output to see skip reasons
uv run pytest -m integration -v

# Run full suite (integration tests skip if Ollama is down)
uv run pytest
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `src/*_test.py` colocation | `tests/unit/`, `tests/integration/`, `tests/e2e/` subdirectory layout | Phase 8 | Integration tests go in `tests/integration/`, not `src/` |
| Direct `pytest.skip()` in test body | `require_ollama` fixture injection | Phase 8 | Cleaner separation; fixture handles skip uniformly; session-scoped probe avoids repeated HTTP calls |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Model loaded in Ollama (when running) is `qwen3:14b` as set in `config.py` | Code Examples / TEST-09 | If no model is loaded, `generate_tailored_resume()` returns HTTP 404/500 → `RuntimeError`, test fails rather than skips |
| A2 | The model will return clean LaTeX without markdown fences for the minimal resume | Pitfall 1 / TEST-09 | `result.fences_stripped is False` assertion fails if model adds fences |

**If A1 or A2 cause test failures:** The test code is correct; the environment configuration needs adjustment. A1 is addressed by ensuring a model is pulled before running integration tests. A2 is addressed by model selection and prompt adherence.

## Open Questions

1. **Model must be pulled before TEST-09 can pass**
   - What we know: `config.py` specifies `OLLAMA_MODEL = "qwen3:14b"`. Ollama will return an error if the model is not pulled.
   - What's unclear: Whether CI or the local environment will have `qwen3:14b` pulled.
   - Recommendation: TEST-09 failing with a RuntimeError about model availability is acceptable test infrastructure — the skip only fires on connection failure, not on missing model. Document this in the plan's success verification step.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Ollama (localhost:11434) | TEST-08, TEST-09 | No (connection refused in research env) | — | Tests skip with exit code 0 |
| uv | Test runner | Yes | installed | — |
| pytest | Test runner | Yes (via uv) | 9.0.3 | — |
| Python 3.13 | Runtime | Yes (uv managed) | 3.13 | — |

**Missing dependencies with no fallback:** None — Ollama absence is handled by the skip mechanism; it does not block test collection or non-integration tests.

**Missing dependencies with fallback:** Ollama — graceful skip via `require_ollama` fixture.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest -m integration` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-08 | `_check_ollama_health()` does not raise when Ollama is running; skips when absent | integration | `uv run pytest -m integration -k health` | No — Wave 0 |
| TEST-09 | `generate_tailored_resume()` returns structurally valid LaTeX; skips when absent | integration | `uv run pytest -m integration -k latex` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest -m "not integration"` (fast suite; integration tests not required per commit)
- **Per wave merge:** `uv run pytest` (full suite; integration tests skip cleanly if Ollama down)
- **Phase gate:** `uv run pytest -m integration` passing (with Ollama running) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/integration/test_llm_client.py` — covers TEST-08, TEST-09 (the entire phase deliverable)

*(No framework install or config gaps — pytest is already configured and `tests/integration/` already exists.)*

## Security Domain

This phase adds test-only code that makes local HTTP calls to `localhost:11434`. No new attack surface is introduced.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth layer; localhost-only |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | Local dev tool |
| V5 Input Validation | No | Test inputs are hardcoded constants |
| V6 Cryptography | No | Plain HTTP to localhost; no TLS |

**Threat model:** Not applicable for test-only code calling localhost.

## Sources

### Primary (HIGH confidence)

- `src/llm_client.py` (codebase) — `_check_ollama_health()` signature, `generate_tailored_resume()` signature, `TailorResult` NamedTuple fields confirmed
- `src/config.py` (codebase) — `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `TIMEOUT` constants confirmed
- `tests/conftest.py` (codebase) — `ollama_available` and `require_ollama` fixture scope and implementation confirmed
- `pyproject.toml` (codebase) — pytest markers (`integration` registered), `pythonpath = ["src"]`, `addopts = "--strict-markers -ra"` confirmed
- `tests/unit/test_llm_client.py` (codebase) — import pattern (`from llm_client import ...`), `@pytest.mark.unit` pattern confirmed
- `.planning/phases/10-integration-tests/10-CONTEXT.md` — all locked decisions D-01 through D-06

### Secondary (MEDIUM confidence)

- `.planning/phases/09-unit-test-gaps/09-CONTEXT.md` — naming conventions and raise-not-exit pattern cross-reference
- `.planning/phases/08-test-infrastructure/08-CONTEXT.md` — directory layout and fixture design reference

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all dependencies verified from pyproject.toml and codebase
- Architecture: HIGH — all design decisions locked in CONTEXT.md, verified against actual source files
- Pitfalls: HIGH — derived from actual code inspection (function signatures, fixture scopes, TIMEOUT values)

**Research date:** 2026-06-05
**Valid until:** 2026-07-05 (stable — all constraints are from the local codebase, not external registries)
