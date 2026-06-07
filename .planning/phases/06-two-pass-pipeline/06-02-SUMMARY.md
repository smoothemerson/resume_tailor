---
phase: 06-two-pass-pipeline
plan: "02"
subsystem: testing
tags: [unittest, mock, patch, two-pass-pipeline, cli, pytest]

requires:
  - phase: 06-two-pass-pipeline plan 01
    provides: jd_analyzer.py analyze_job_description function (tested in 06-01)

provides:
  - All 8 existing cli_test.py tests patched with @patch("cli.analyze_job_description", return_value=None)
  - 3 new tests covering two-pass behavior: progress message order, analysis=None forwarding, analysis dict forwarding
  - Full cli_test.py suite hardened against Wave 3 cli.py wiring of analyze_job_description

affects:
  - 06-03 (cli.py wiring — these tests will start passing after that plan)
  - 06-04 (llm_client.py modifications — analysis dict injection)

tech-stack:
  added: []
  patterns:
    - "Outermost @patch decorator maps to last function parameter (Python bottom-up decorator application)"
    - "printed_lines capture pattern for asserting print call order"
    - "mock_generate.call_args.kwargs for verifying keyword argument values"

key-files:
  created: []
  modified:
    - src/cli_test.py

key-decisions:
  - "All 8 existing tests patched with return_value=None (simulates fallback path — analysis failed silently)"
  - "New analyze patch placed as OUTERMOST decorator so mock_analyze is LAST parameter per Python decorator ordering"
  - "3 new tests use full standard decorator stack matching existing test structure"
  - "test_analyzing_progress_message_printed asserts message ORDER via index comparison, not just presence"

patterns-established:
  - "Patch outermost = last param: when adding a new @patch to existing tests, add it topmost and append param last"
  - "Two-pass progress assertion: capture printed_lines list, check index of analyzing < index of tailoring"
  - "Call args kwarg assertion: mock.call_args.kwargs['analysis'] to verify keyword argument injection"

requirements-completed:
  - PIPE-01
  - PIPE-03

duration: 8min
completed: 2026-06-07
---

# Phase 06 Plan 02: cli_test.py Two-Pass Pipeline Test Updates Summary

**All 8 cli_test.py tests patched with @patch("cli.analyze_job_description") + 3 new tests covering progress message order, analysis=None forwarding, and analysis dict forwarding**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-07T00:00:00Z
- **Completed:** 2026-06-07T00:08:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Patched all 8 existing test functions in src/cli_test.py with @patch("cli.analyze_job_description", return_value=None) as outermost decorator and mock_analyze as last parameter
- Added test_analyzing_progress_message_printed: verifies "Analyzing job description..." appears before "Tailoring resume" in print output
- Added test_generate_called_with_analysis_none_when_analysis_fails: verifies generate_tailored_resume receives analysis=None on fallback path
- Added test_generate_called_with_analysis_dict_when_analysis_succeeds: verifies generate_tailored_resume receives the analysis dict on success path

## Task Commits

Each task was committed atomically:

1. **Task 1: Patch all 8 existing cli_test.py tests** - `c328efb` (test)
2. **Task 2: Add 3 new two-pass behavior tests** - `c328efb` (test, combined with Task 1 in single commit)

## Files Created/Modified
- `src/cli_test.py` - All 8 existing tests patched + 3 new two-pass behavior tests added (8 -> 11 total)

## Decisions Made
- Tasks 1 and 2 committed together in a single atomic commit since both modify the same file and are logically inseparable (Task 2 appends to the file Task 1 modifies)
- Used return_value=None on all 8 existing test patches to simulate the fallback path without changing any assertion bodies
- New tests use the identical decorator stack as existing tests for consistency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- src/cli_test.py suite is hardened: all tests mock analyze_job_description so they won't break when cli.py is wired in Wave 3 (06-03)
- The 3 new tests will fail until cli.py gains the analyze_job_description() call and passes analysis= to generate_tailored_resume — this is expected TDD behavior
- No blockers

## Self-Check

- [x] src/cli_test.py exists and compiles: `python3 -m py_compile src/cli_test.py` exits 0
- [x] grep -c "cli.analyze_job_description" src/cli_test.py returns 11 (8 existing + 3 new)
- [x] grep -c "def test_" src/cli_test.py returns 11
- [x] Commit c328efb exists: all 8 existing tests patched + 3 new tests added

## Self-Check: PASSED

---
*Phase: 06-two-pass-pipeline*
*Completed: 2026-06-07*
