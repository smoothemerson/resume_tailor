---
phase: 05-diff-view
plan: "02"
subsystem: ui
tags: [difflib, ansi, tty, cli-integration, unittest-mock]

requires:
  - phase: 05-diff-view-plan-01
    provides: src/diff_view.py with show_diff() public entry point, TTY-gated and never-raises

provides:
  - src/cli.py — integrated show_diff() call outside try/except, between write_resume() and final print
  - src/cli_test.py — updated test suite with show_diff patched on all success paths and new call-site assertion test

affects:
  - Any future plan modifying cli.py main() flow

tech-stack:
  added: []
  patterns:
    - Patch call-site module namespace (cli.show_diff not diff_view.show_diff) to intercept in-module name lookup
    - Bottom-up decorator-to-param mapping: innermost @patch maps to first positional param after self

key-files:
  created: []
  modified:
    - src/cli.py
    - src/cli_test.py

key-decisions:
  - "show_diff() placed outside try/except block — non-fatal display call cannot suppress confirmation print (D-01, T-05-03)"
  - "Patch target is cli.show_diff not diff_view.show_diff — function looked up from cli module namespace at call time"
  - "mock_show_diff is first positional param (outermost remaining decorator) after mock_guards/mock_input/mock_read/mock_generate/mock_write"

patterns-established:
  - "cli.show_diff patch pattern: add @patch('cli.show_diff') at top of decorator stack (outermost) so mock_show_diff is last positional param"

requirements-completed: [DIFF-01, DIFF-02, DIFF-03]

duration: 3min
completed: 2026-06-04
---

# Phase 05 Plan 02: CLI Integration — Diff View Wiring Summary

**show_diff() integrated into cli.py main() flow outside try/except, with 8 cli tests green including new call-site assertion verifying correct arguments**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-04T18:30:00Z
- **Completed:** 2026-06-04T18:33:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `src/cli.py` wired with `from diff_view import show_diff` import in alphabetical order (after `config`, before `guards`) and `show_diff(resume_text, result.content)` call at the correct position: after try/except closes, before final print
- `src/cli_test.py` updated to patch `cli.show_diff` in all 4 success-path tests, preventing real TTY checks during testing
- New test `test_show_diff_called_with_resume_and_tailored` added, asserting show_diff is called once with the exact original and tailored content strings
- Full test suite: 48 tests, all passing

## Task Commits

1. **Task 1: Wire show_diff into cli.py** - `e7b74e9` (feat)
2. **Task 2: Update cli_test.py to patch show_diff and add call-site test** - `55ea383` (test)

## Files Created/Modified

- `src/cli.py` - Added `from diff_view import show_diff` import and `show_diff(resume_text, result.content)` call outside try/except block
- `src/cli_test.py` - Added `@patch("cli.show_diff")` and `mock_show_diff` param to 4 existing success-path tests; added `test_show_diff_called_with_resume_and_tailored`

## Decisions Made

- `show_diff()` call placed outside the try/except block per D-01 and T-05-03 — a display concern must never prevent the confirmation print or the written file from being reported
- Patch target is `cli.show_diff` (not `diff_view.show_diff`) because Python looks up the name from the importing module's namespace at call time
- Error-path tests (test_empty_jd_exits_1, test_runtime_error_from_llm_exits_1, test_value_error_from_llm_exits_1) do not need the patch because they exit before reaching the show_diff call site

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All 48 suite tests passed on first run after both tasks. A pre-existing `SyntaxWarning` in `src/llm_client.py` (invalid `\d` escape) was noted as out of scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DIFF-01, DIFF-02, DIFF-03 all satisfied: diff_view.py module built (Plan 01), wired into CLI (Plan 02)
- Phase 05 complete — diff feature fully integrated and tested
- No blockers for subsequent phases

---
*Phase: 05-diff-view*
*Completed: 2026-06-04*
