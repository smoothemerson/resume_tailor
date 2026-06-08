---
phase: 04-output-reliability-guards
plan: 02
subsystem: guards
tags: [guards, cli, namedtuple, latex, warnings, stderr, unittest, patch]

# Dependency graph
requires:
  - phase: 04-output-reliability-guards/04-01
    provides: TailorResult NamedTuple in llm_client.py and guards.py with run_guards()
provides:
  - cli.py wired with run_guards(resume_text, result.content, result.fences_stripped) before write_resume()
  - cli.py imports TailorResult and run_guards
  - guards_test.py with 14 tests covering GUARD-01 through GUARD-04 (including test_multiple_missing_sections)
affects: [04-output-reliability-guards, 04-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Guard pipeline wired between generate_tailored_resume() and write_resume() in cli.py
    - TailorResult.content and TailorResult.fences_stripped consumed at cli boundary

key-files:
  created: []
  modified:
    - src/cli.py
    - src/guards_test.py

key-decisions:
  - "Guards are called before write_resume() so warnings always fire before output is saved — preserving D-03 ordering rule"
  - "TailorResult import added to cli.py for Plan 03 cli_test.py mock compatibility"
  - "test_multiple_missing_sections added to guards_test.py to satisfy Plan 02 behavioral spec (two dropped sections -> two warnings)"

patterns-established:
  - "Guard wiring in cli.py: result = generate_tailored_resume(...) -> run_guards(...) -> write_resume(result.content, ...)"
  - "Existing Plan 01 guards_test.py satisfied Plan 02 done criteria — only test_multiple_missing_sections was missing"

requirements-completed: [GUARD-01, GUARD-02, GUARD-03, GUARD-04]

# Metrics
duration: 2min
completed: 2026-06-02
---

# Phase 4 Plan 02: Wire Guards into CLI and Complete Test Suite Summary

**Guard pipeline wired into cli.py calling run_guards(resume_text, result.content, result.fences_stripped) before write_resume(), with 14-test guards_test.py covering all four guard requirements**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-02T18:50:48Z
- **Completed:** 2026-06-02T18:52:16Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Updated `cli.py` to import `run_guards` from guards and `TailorResult` from llm_client, replacing `content = generate_tailored_resume(...)` with `result = ...` and calling `run_guards(resume_text, result.content, result.fences_stripped)` before `write_resume(result.content, output_dir)` — guards now fire on every real run
- Added `test_multiple_missing_sections` to `guards_test.py` (the one behavioral test from Plan 02's spec that was not already present from Plan 01), bringing the test count from 13 to 14
- All 14 guards_test.py tests pass; cli_test.py failures are expected (mocks return plain str — fixed in Plan 03)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire run_guards into cli.py** - `e3c7675` (feat)
2. **Task 2: Add test_multiple_missing_sections to guards_test.py** - `1aa842b` (feat)

## Files Created/Modified

- `/workspace/src/cli.py` - Added `from guards import run_guards`, changed `from llm_client import TailorResult, generate_tailored_resume`, changed try block to use `result = generate_tailored_resume(...)` and call `run_guards()` before `write_resume(result.content, ...)`
- `/workspace/src/guards_test.py` - Added `test_multiple_missing_sections` test asserting that two dropped sections produce exactly two warning calls

## Decisions Made

- `TailorResult` imported in cli.py even though cli.py itself doesn't instantiate it — this is forward-looking for Plan 03's cli_test.py mock update, which will need `TailorResult` importable from the tested module namespace
- `test_multiple_missing_sections` added using `mock_logger.warning.call_count == 2` assertion (not `assert_called_once_with`) since two different section names are warned independently

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] guards_test.py already existed from Plan 01 — added missing test**
- **Found during:** Task 2 (guards_test.py creation)
- **Issue:** Plan 01 already created `guards_test.py` with 13 tests. Plan 02 specified `test_multiple_missing_sections` was not in the existing file.
- **Fix:** Added the single missing test to the existing file rather than recreating it. All 14 tests pass.
- **Files modified:** src/guards_test.py
- **Verification:** `.venv/bin/python -m pytest src/guards_test.py -v` exits 0, 14 passed
- **Committed in:** 1aa842b (Task 2 commit)

---

**Total deviations:** 1 auto-handled (existing file from prior plan — added missing test only)
**Impact on plan:** No scope change; all Plan 02 done criteria satisfied.

## Issues Encountered

None — the only noteworthy observation is that Plan 01 had already created `guards_test.py` with 13 tests, so Task 2 required adding only the one missing behavioral test rather than creating the file from scratch.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `cli.py` guard wiring complete — guards fire warnings on every real run before output is written
- `cli_test.py` will fail (4 tests) until Plan 03 updates mocks from plain `str` to `TailorResult`
- Plan 03 must: patch `cli.run_guards` in each affected test, update 5 `mock_generate.return_value` calls from plain `str` to `TailorResult(content=..., fences_stripped=False)`

---
*Phase: 04-output-reliability-guards*
*Completed: 2026-06-02*
