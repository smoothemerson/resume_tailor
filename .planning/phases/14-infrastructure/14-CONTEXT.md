# Phase 14: Infrastructure - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the packaging gap, ship CI, fill unit test gaps, and remove `.claude/` from git tracking. This phase delivers no new features — it closes infrastructure debt in packaging, CI, test coverage, and repository hygiene accumulated during v1.1 and v1.2 feature work.

</domain>

<decisions>
## Implementation Decisions

### Test Placement
- **D-01:** Add `src/jd_analyzer_test.py`, `src/resume_reader_test.py`, `src/resume_writer_test.py` as REQUIREMENTS.md specifies — colocated with source, following the existing pattern of `llm_client_test.py`, `guards_test.py`, etc.
- **D-02:** `src/jd_analyzer_test.py` tests `_parse_analysis_response()` **directly** (no mocking — pure string in/out). This is additive to the existing `tests/unit/test_jd_analyzer.py` which tests `analyze_job_description()` with mocked HTTP. Both coexist.
- **D-03:** `src/resume_reader_test.py` and `src/resume_writer_test.py` coexist with the identical tests already in `tests/unit/`. Acceptable duplication — files are tiny and the `src/` pattern is already established.
- **D-04:** All new tests tagged `@pytest.mark.unit`. Use `tmp_path` fixture for file-system tests.

### CI Workflow
- **D-05:** Use `astral-sh/setup-uv@v4` action to install uv — official Astral action, handles binary caching automatically.
- **D-06:** Include both `ruff check src/` **and** `ruff format --check src/` in the CI lint step. Formatting gate added beyond the strict CI-01 spec requirement (user approved).
- **D-07:** Trigger on push and pull_request to main. Runner: ubuntu-latest, Python 3.13.
- **D-08:** Use `uv sync` to install dependencies (installs project + dev dependencies from lock file).

### .gitignore
- **D-09:** Create a standard Python `.gitignore` — not just `.claude/`. Include: `.claude/`, `__pycache__/`, `*.py[cod]`, `.venv/`, `dist/`, `*.egg-info/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`. Portfolio project should look complete.

### Repository Hygiene
- **D-10:** Remove `.claude/` from git tracking via `git rm -r --cached .claude/` then commit. Local directory is preserved. `.gitignore` entry prevents re-tracking.

### Claude's Discretion
- CI job name, step names, timeout values — standard conventions are fine.
- `uv sync --dev` vs `uv sync` — use `uv sync` (includes dev dependencies by default from `[dependency-groups]`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — PKG-01, CI-01, TEST-14, TEST-15, TEST-16, REPO-01 fully defined with exact test case lists and success criteria

### Source Files Under Test
- `src/jd_analyzer.py` — `_parse_analysis_response()` is the target function for TEST-14; read before writing tests
- `src/resume_reader.py` — `read_resume()` target for TEST-15; trivial (4 lines)
- `src/resume_writer.py` — `write_resume()` target for TEST-16

### Existing Tests (do not duplicate)
- `tests/unit/test_jd_analyzer.py` — tests `analyze_job_description()` with mocked HTTP; NOT `_parse_analysis_response()` directly
- `tests/unit/test_resume_reader.py` — already covers TEST-15 cases; new `src/` file is additive
- `tests/unit/test_resume_writer.py` — already covers TEST-16 cases; new `src/` file is additive

### Packaging
- `pyproject.toml` — `[tool.hatch.build.targets.wheel]` include list needs `src/jd_analyzer.py` and `src/keyword_matcher.py` added

### Existing Test Pattern
- `src/llm_client_test.py` — reference for `@pytest.mark.unit` style in `src/`
- `src/guards_test.py` — reference for test structure in `src/`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_parse_analysis_response(content: str) -> dict | None` in `src/jd_analyzer.py` — strips fences, parses JSON, validates keys and list types; all test cases are pure string inputs, no mocking needed
- `tmp_path` pytest fixture — used in `tests/unit/test_resume_writer.py`; apply same pattern in `src/resume_writer_test.py`

### Established Patterns
- Tests in `src/` use `*_test.py` naming (not `test_*.py`)
- Tests in `tests/unit/` use `test_*.py` naming — both are in `testpaths`
- `@pytest.mark.unit` is the marker for all fast isolated tests
- `--strict-markers` is set — all tests must use a declared marker

### Integration Points
- `pyproject.toml` `[tool.hatch.build.targets.wheel]` include list — add 2 entries
- `.github/workflows/ci.yml` — new file, no existing workflow to extend
- `.gitignore` — new file, no existing entries to preserve

</code_context>

<specifics>
## Specific Ideas

- `ruff format --check src/` added to CI beyond the spec requirement — user confirmed this is the right call for a portfolio project
- `astral-sh/setup-uv@v4` is the correct action reference (Astral's official GitHub Action for uv)
- Test cases for `_parse_analysis_response` that are NOT covered by existing tests/unit/: `non-list value` (e.g., keys exist but values are strings not lists), `empty string` input

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 14-Infrastructure*
*Context gathered: 2026-06-09*
