---
phase: 08-test-infrastructure
plan: "02"
subsystem: testing
tags: [pytest, conftest, fixtures, sys-path-cleanup, ollama-skip-fixture]

# Dependency graph
requires:
  - phase: 08-01
    provides: "pythonpath = [src] in pyproject.toml makes sys.path.insert hacks redundant"
provides:
  - tests/unit/, tests/integration/, tests/e2e/ directories exist (no __init__.py)
  - tests/conftest.py with ollama_available (session-scoped) and require_ollama (function-scoped) fixtures
  - sys.path.insert hacks removed from src/cli_test.py and src/llm_client_test.py
  - ruff-clean test files; all 35 tests pass
affects:
  - 09-unit-tests
  - 10-integration-tests
  - 11-e2e-tests

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "session-scoped ollama_available fixture performs single HTTP GET to /api/tags with timeout=3"
    - "function-scoped require_ollama opts tests into Ollama dependency without autouse"
    - ".gitkeep files track empty test directories in git"

key-files:
  created:
    - tests/conftest.py
    - tests/unit/.gitkeep
    - tests/integration/.gitkeep
    - tests/e2e/.gitkeep
  modified:
    - src/cli_test.py
    - src/llm_client_test.py

key-decisions:
  - "import sys was unused in cli_test.py (@patch uses string targets not module references) — removed per Rule 1 (ruff F401)"
  - ".gitkeep files added to empty test directories so git tracks them (empty dirs are not tracked by git)"
  - "require_ollama has no autouse=True — tests must opt-in by declaring the fixture parameter"

patterns-established:
  - "Ollama skip pattern: session-scoped probe + function-scoped skip guard; integration tests declare require_ollama parameter to opt in"

requirements-completed:
  - TEST-02
  - TEST-03

# Metrics
duration: 2min
completed: 2026-06-02
---

# Phase 8 Plan 02: Test Infrastructure — Scaffold and conftest.py Summary

**tests/ hierarchy scaffolded with three empty subdirectories; tests/conftest.py provides session-scoped Ollama availability probe and function-scoped skip fixture; sys.path hacks removed from both test files**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-02T18:52:10Z
- **Completed:** 2026-06-02T18:54:16Z
- **Tasks:** 2
- **Files modified:** 4 (tests/conftest.py created; tests/unit/, tests/integration/, tests/e2e/ with .gitkeep; src/cli_test.py and src/llm_client_test.py modified)

## Accomplishments
- Created tests/unit/, tests/integration/, tests/e2e/ bare directories (no __init__.py) with .gitkeep tracking files
- Created tests/conftest.py with ollama_available (scope="session", imports OLLAMA_BASE_URL from config, probes /api/tags with timeout=3) and require_ollama (function-scoped, calls pytest.skip when Ollama is unavailable)
- Removed sys.path.insert hacks from src/cli_test.py (1 line) and src/llm_client_test.py (3 lines including unused imports)
- All 35 tests pass; ruff clean on all three modified files

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tests/ scaffold and conftest.py fixtures** - `6ae8746` (feat)
2. **Task 2: Remove sys.path.insert hacks from src/*_test.py** - `e3d8217` (chore)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified
- `tests/conftest.py` - ollama_available and require_ollama pytest fixtures; imports OLLAMA_BASE_URL from config
- `tests/unit/.gitkeep` - tracks empty unit test directory
- `tests/integration/.gitkeep` - tracks empty integration test directory
- `tests/e2e/.gitkeep` - tracks empty e2e test directory
- `src/cli_test.py` - removed sys.path.insert line (line 6) and unused import sys (line 1)
- `src/llm_client_test.py` - removed import sys (line 1), from pathlib import Path (line 3), and sys.path.insert (line 6)

## Decisions Made
- Used .gitkeep files to track empty test directories — empty directories are not tracked by git, .gitkeep is the standard convention
- Removed import sys from cli_test.py in addition to the sys.path.insert line — ruff identified it as unused (F401); @patch("sys.argv") uses a string target and does not require the sys module to be imported

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused import sys from cli_test.py**
- **Found during:** Task 2 (Remove sys.path.insert hacks from src/*_test.py)
- **Issue:** Plan stated "KEEP: import sys (line 1, used by @patch('sys.argv'))" but @patch uses a string path to the target, not an actual module reference. `import sys` was therefore unused and ruff reported F401.
- **Fix:** Removed `import sys` from the top of src/cli_test.py; only `from pathlib import Path` was retained (used for Path("/tmp/...") mock return values in test methods)
- **Files modified:** src/cli_test.py
- **Verification:** uv run ruff check src/cli_test.py exits 0; all 35 tests still pass
- **Committed in:** e3d8217 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan's import retention guidance)
**Impact on plan:** Required for ruff compliance. No scope creep — correct per acceptance criteria "uv run ruff check src/cli_test.py exits 0 with no warnings."

## Issues Encountered
- Plan stated import sys should be kept in cli_test.py but it was actually unused. Ruff correctly flagged it; removal was necessary to satisfy the ruff acceptance criterion. See deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 8 test infrastructure is complete: pytest configured (plan 01), test directories created, conftest.py fixtures present (plan 02)
- Phases 9-11 can add tests to tests/unit/, tests/integration/, and tests/e2e/ without any additional setup
- Integration and e2e tests that need Ollama declare require_ollama as a fixture parameter; they are skipped automatically when Ollama is not running

---
*Phase: 08-test-infrastructure*
*Completed: 2026-06-02*
