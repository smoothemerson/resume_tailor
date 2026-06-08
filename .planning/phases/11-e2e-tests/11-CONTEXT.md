# Phase 11: E2E Tests - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Write `tests/e2e/test_cli.py` with two E2E tests that invoke the CLI as a subprocess — TEST-10 (error path, empty JD, exits 1, no Ollama needed) and TEST-11 (golden path, real JD, exits 0, creates output file, Ollama-skippable). Requirements TEST-10 and TEST-11.

</domain>

<decisions>
## Implementation Decisions

### Subprocess Invocation
- **D-01:** Invoke CLI as `subprocess.run([sys.executable, CLI_PATH, ...])` where `CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"` — absolute path derived from test file location. Works without install, always uses the same Python interpreter as pytest.
- **D-02:** Pass stdin as `input="END\n"` (or `input="<jd text>\nEND\n"`) with `capture_output=True, text=True` — no bytes encoding overhead needed.

### Resume Fixture
- **D-03:** Define a module-level `MINIMAL_RESUME` string constant in `tests/e2e/test_cli.py` — same pattern as Phase 10's integration test. No import from other test files.
- **D-04:** In TEST-11, write `MINIMAL_RESUME` to a `tmp_path / "resume.tex"` file and pass `--resume` pointing to it. Also pass `--output-dir tmp_path` to redirect output away from `resumes/output/`.

### Assertion Scope
- **D-05:** TEST-10 asserts `returncode == 1` and `"Error: Job description cannot be empty." in result.stderr` — exact string match (string is a stable constant in cli.py).
- **D-06:** TEST-11 asserts: `returncode == 0`, `"Tailored resume written to:" in result.stdout`, and one output `.tex` file exists in `tmp_path` with filename matching `tailored_resume_\d{8}_\d{6}\.tex`. No content assertions — LaTeX structure is already covered by integration tests.

### Skip Behavior
- **D-07:** TEST-10 does NOT use `require_ollama` — it tests the empty-JD error path before any Ollama call is made. Must run even when Ollama is absent.
- **D-08:** TEST-11 uses the `require_ollama` fixture from `tests/conftest.py` to skip when Ollama is unreachable.

### Markers
- **D-09:** Every test carries `@pytest.mark.e2e` — required by `pyproject.toml` `--strict-markers` and the `pytest -m e2e` success criterion.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/ROADMAP.md` §Phase 11 — Goal, success criteria (3 items), requirements list (TEST-10, TEST-11)
- `.planning/REQUIREMENTS.md` §E2E Tests — Full requirement text for TEST-10, TEST-11

### Source Files (read before writing tests)
- `src/cli.py` — Entry point under test; inspect how JD input is read, empty JD error path, `--resume` / `--output-dir` flags, and exact stderr message ("Error: Job description cannot be empty.")
- `tests/conftest.py` — Provides `require_ollama` fixture (used in TEST-11 only)

### Prior Phase Context
- `.planning/phases/08-test-infrastructure/08-CONTEXT.md` — pytest config, directory layout, marker definitions
- `.planning/phases/09-unit-test-gaps/09-CONTEXT.md` — naming conventions (`test_*.py` prefix, `@pytest.mark.*`), no `__init__.py`
- `.planning/phases/10-integration-tests/10-CONTEXT.md` — MINIMAL_RESUME constant pattern, `require_ollama` skip pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/conftest.py` `require_ollama` fixture — session-scoped; use as function arg in TEST-11 to auto-skip when Ollama is down. TEST-10 does NOT use it.
- `tests/e2e/` directory — already exists (created in Phase 8), currently empty.
- `MINIMAL_RESUME` pattern from `tests/integration/test_llm_client.py` — define a local copy in `tests/e2e/test_cli.py` (do not import across test files).

### Established Patterns
- `@pytest.mark.e2e` on every test in `tests/e2e/` — required by `--strict-markers`.
- `test_*.py` prefix for discovery; bare directory, no `__init__.py`.
- `subprocess.run` with `capture_output=True, text=True` for clean stdout/stderr capture.

### Integration Points
- `tests/e2e/test_cli.py` is a new file — no existing file to update.
- `pyproject.toml` already includes `testpaths = ["src", "tests"]` and `e2e` marker — no changes needed.

</code_context>

<specifics>
## Specific Ideas

- `CLI_PATH` constant at module level:
  ```python
  CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"
  ```
- `MINIMAL_RESUME` shape (same as integration test):
  ```python
  MINIMAL_RESUME = (
      "\\documentclass{article}\n"
      "\\begin{document}\n"
      "\\section{Summary}\n"
      "AI engineer with 3 years experience.\n"
      "\\end{document}"
  )
  ```
- TEST-10 body outline:
  ```python
  result = subprocess.run(
      [sys.executable, CLI_PATH],
      input="END\n",
      capture_output=True,
      text=True,
  )
  assert result.returncode == 1
  assert "Error: Job description cannot be empty." in result.stderr
  ```
- TEST-11 body outline: write MINIMAL_RESUME to `tmp_path / "resume.tex"`, run subprocess with `--resume` and `--output-dir` flags, assert exit 0, stdout contains success message, one `.tex` file with timestamp pattern exists in `tmp_path`.
- Filename pattern assertion: `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", output_file.name)` — same regex used in Phase 9 writer tests.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-E2E Tests*
*Context gathered: 2026-06-08*
