# Phase 14: Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-09
**Phase:** 14-Infrastructure
**Areas discussed:** Test placement strategy, CI workflow setup, .gitignore scope

---

## Test Placement Strategy

### resume_reader and resume_writer test files

| Option | Description | Selected |
|--------|-------------|----------|
| Add src/ files as spec'd | Create src/resume_reader_test.py and src/resume_writer_test.py. Coexists with tests/unit/. Satisfies spec cleanly. | ✓ |
| Extend tests/unit/ only | Don't add src/ files. Update REQUIREMENTS.md to reflect the change in file location. | |
| Add src/ for jd_analyzer only | Skip creating duplicate src/ files for reader/writer. | |

**User's choice:** Add src/ files as spec'd (Recommended)
**Notes:** Minimal duplication accepted — files are tiny, src/ pattern already established.

---

### jd_analyzer test file

| Option | Description | Selected |
|--------|-------------|----------|
| Add src/jd_analyzer_test.py for _parse_analysis_response | Direct unit tests of the parse function. Complements existing mocked tests in tests/unit/. | ✓ |
| Replace tests/unit/ test | Move and expand tests/unit/test_jd_analyzer.py to src/, consolidating both levels. | |

**User's choice:** Yes — add src/jd_analyzer_test.py for _parse_analysis_response (Recommended)
**Notes:** Two-level coverage: tests/unit/ tests public API with mocked HTTP; src/ tests internal parse function directly.

---

## CI Workflow Setup

### uv installation method

| Option | Description | Selected |
|--------|-------------|----------|
| astral-sh/setup-uv@v4 action | Official GitHub Action, auto-handles caching. 2025 standard. | ✓ |
| pip install uv | Simpler, no external action dependency. Slower, no cache. | |

**User's choice:** astral-sh/setup-uv@v4 action (Recommended)
**Notes:** Official action from Astral.

---

### Lint checks in CI

| Option | Description | Selected |
|--------|-------------|----------|
| ruff check src/ only | Exactly what CI-01 requires. | |
| ruff check src/ + ruff format --check | Adds formatting gate. Better for portfolio project. | ✓ |

**User's choice:** ruff check src/ + ruff format --check (Recommended)
**Notes:** Goes slightly beyond CI-01 spec but user confirmed this is the right call for a portfolio project.

---

## .gitignore Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Standard Python .gitignore | Includes .claude/, __pycache__, .venv/, dist/, *.egg-info/, .mypy_cache/, .ruff_cache/, .pytest_cache/ | ✓ |
| Minimal (.claude/ only) | Exactly what REPO-01 specifies. Can extend later. | |

**User's choice:** Standard Python .gitignore (Recommended)
**Notes:** No .gitignore exists at all — good time to create a complete one. REPO-01 satisfied as a subset.

---

## Claude's Discretion

- CI job name and step names — standard conventions
- `uv sync` vs `uv sync --dev` — use `uv sync` (dev deps included by default from dependency-groups)
- CI timeout values — standard GitHub Actions defaults

## Deferred Ideas

None — discussion stayed within phase scope.
