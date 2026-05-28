---
phase: 02-llm-integration
plan: 01
subsystem: llm
tags: [ollama, requests, llm-integration, latex, python]

requires:
  - phase: 01-foundation
    provides: config.py with OLLAMA_BASE_URL/OLLAMA_MODEL/TIMEOUT constants; resume_reader.py/resume_writer.py for file I/O
provides:
  - generate_tailored_resume(resume_text, job_description) -> str: complete LLM integration with safety guards
  - _check_ollama_health: GET /api/tags fast-fail before prompt construction
  - _build_messages: role-separated prompt with D-01/D-02/D-03/D-04 constraints
  - _strip_fences: unconditional markdown fence removal
  - _validate_latex: documentclass + end{document} boundary validation
  - llm_client_test.py: 11 unit tests covering all behavioral contracts
affects: [03-main-integration]

tech-stack:
  added: []
  patterns:
    - raise-not-exit: llm_client.py raises RuntimeError/ValueError; main.py owns sys.exit boundary
    - unconditional-strip: fence stripping always runs regardless of fence presence (QUAL-01)
    - fail-fast-health-check: GET /api/tags before any prompt construction (ERR-03)
    - done_reason-first: truncation check precedes fence strip and LaTeX validation (QUAL-03)

key-files:
  created:
    - src/llm_client.py
    - src/log_manager.py
    - src/llm_client_test.py
  modified: []

key-decisions:
  - "RuntimeError for operational failures (connection, truncation, HTTP error); ValueError for validation failures (malformed LLM output) — enables Phase 3 to catch them separately"
  - "TIMEOUT[0] (connect-only, 10s) used for health check; full TIMEOUT tuple for /api/chat call — avoids 300s read wait on instant /api/tags response"
  - "log_manager.py created in worktree as blocking dependency (was untracked in main workspace)"
  - "TDD: tests written before implementation; all 11 tests confirmed failing then passing"

patterns-established:
  - "Pattern: raise-not-exit — all LLM errors raise, never call sys.exit inside module"
  - "Pattern: test isolation via unittest.mock.patch on requests.get and requests.post"
  - "Pattern: XML-wrapped job description in user message (<job_description>...</job_description>)"

requirements-completed: [CORE-04, QUAL-01, QUAL-02, QUAL-03, QUAL-04, ERR-02, ERR-03]

duration: 2min
completed: 2026-05-28
---

# Phase 2 Plan 01: LLM Client Summary

**Ollama /api/chat integration with unconditional fence stripping, done_reason truncation guard, and documentclass/end{document} LaTeX validation — all five safety guards built in from the start**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-28T22:51:37Z
- **Completed:** 2026-05-28T22:54:24Z
- **Tasks:** 2
- **Files modified:** 3 created

## Accomplishments

- Implemented generate_tailored_resume() with the full 7-step execution order: health check, prompt build, /api/chat POST with stream=False and num_ctx=8192, done_reason check, fence strip, LaTeX validation, return validated string
- Created log_manager.py (was untracked in main workspace; needed for D-08 import pattern)
- 11 unit tests cover all behavioral contracts: fence stripping variants, LaTeX boundary validation, RuntimeError on ConnectionError, RuntimeError on done_reason=length, ValueError propagation for invalid LLM output

## Task Commits

1. **Task 1: Implement llm_client.py** - `0930925` (feat)
2. **Task 2: Validate behavioral contracts with unit tests** - `6934845` (test)

## Files Created/Modified

- `src/llm_client.py` - LLM integration module: generate_tailored_resume() + four private helpers
- `src/log_manager.py` - CustomLogger class and module-level logger instance (D-08 dependency)
- `src/llm_client_test.py` - 11 unittest cases covering all safety guard behavioral contracts

## Decisions Made

- RuntimeError for operational failures; ValueError for validation failures — enables Phase 3 to catch them separately if needed
- TIMEOUT[0] (10s) for health check; full TIMEOUT tuple (10, 300) for /api/chat — avoids hanging 300s read on /api/tags instant response
- uv installed during execution to resolve `requests` module (not available in shell PATH); all tests run via `uv run python3`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created log_manager.py in worktree**
- **Found during:** Task 1 (reading dependencies before implementation)
- **Issue:** log_manager.py was untracked in main workspace (not committed to git), so it was missing from the worktree. llm_client.py imports `from log_manager import logger` (D-08); without it, the module cannot be imported.
- **Fix:** Created src/log_manager.py in the worktree, mirroring the main workspace version (CustomLogger class wrapping stdlib logging)
- **Files modified:** src/log_manager.py
- **Verification:** Tests import llm_client successfully; all 11 tests pass
- **Committed in:** 0930925 (Task 1 commit)

**2. [Rule 3 - Blocking] Installed uv to resolve requests dependency**
- **Found during:** Task 1 RED phase (running tests to confirm failure)
- **Issue:** `requests` module not available in shell PATH; no pip or uv installed
- **Fix:** Downloaded and installed uv from astral.sh, then ran `uv sync` to create .venv with requests>=2.32
- **Files modified:** None (dev environment setup only)
- **Verification:** `uv run python3` successfully imports requests and runs all 11 tests
- **Committed in:** Not committed (environment setup, no code change)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes required for the module to be importable and tests to run. No scope creep.

## Issues Encountered

- pyproject.toml include list missing log_manager.py and llm_client.py entries — noted but out of scope for this plan; Phase 3 (main.py integration) will need the full package include list updated

## Threat Surface Scan

No new network endpoints or auth paths introduced. All HTTP calls go to http://localhost:11434 (loopback only). No user data leaves the machine. T-02-01 through T-02-06 all handled per threat_model in the plan. No unplanned threat surface.

## Known Stubs

None — llm_client.py is fully wired. generate_tailored_resume() makes real HTTP calls to Ollama when invoked; no hardcoded mock data flows to callers.

## Next Phase Readiness

- generate_tailored_resume(resume_text, job_description) is ready for Phase 3 (main.py) to import and call
- Raises RuntimeError or ValueError on failure; Phase 3 needs to catch both and call sys.exit(1) with user-readable messages
- log_manager.py needs to be committed to main branch (currently only in worktree) before Phase 3 runs

## Self-Check: PASSED

- src/llm_client.py: FOUND
- src/log_manager.py: FOUND
- src/llm_client_test.py: FOUND
- 02-01-SUMMARY.md: FOUND
- Commit 0930925 (feat - llm_client.py): FOUND
- Commit 6934845 (test - llm_client_test.py): FOUND
- All 11 unit tests: PASSED

---
*Phase: 02-llm-integration*
*Completed: 2026-05-28*
