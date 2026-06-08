---
phase: 07-jd-keyword-match-summary
plan: 02
subsystem: cli-integration
tags: [python, cli, keyword-matching, integration-test, unittest]

# Dependency graph
requires:
  - phase: 07-jd-keyword-match-summary
    plan: 01
    provides: show_keyword_match public entry point in keyword_matcher.py
provides:
  - cli.py wired with show_keyword_match import and call site after show_diff
  - Integration test asserting show_keyword_match called with correct args when analysis is not None
  - Safety @patch on existing test that uses non-None analysis return
affects: [cli-entrypoint, test-coverage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import alphabetical ordering: from keyword_matcher inserted between jd_analyzer and llm_client"
    - "if analysis is not None: guard in cli.py main() before calling show_keyword_match"
    - "Safety @patch(cli.show_keyword_match) added to any test mocking non-None analysis"

key-files:
  created: []
  modified:
    - src/cli.py
    - src/cli_test.py

key-decisions:
  - "show_keyword_match call placed after show_diff and before final print per D-02 (position decision)"
  - "if analysis is not None: guard in caller (cli.py) not inside module — T-07-05 mitigation"
  - "Safety @patch(cli.show_keyword_match) added to test_generate_called_with_analysis_dict_when_analysis_succeeds to prevent side effects when builtins.print is captured"

# Metrics
duration: ~2min
completed: 2026-06-08
---

# Phase 07 Plan 02: JD Keyword Match Summary — CLI Integration

**Three-line addition to cli.py that wires show_keyword_match into main() after show_diff, guarded by if analysis is not None, plus a new integration test asserting the call**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-08T18:14:12Z
- **Completed:** 2026-06-08T18:15:50Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `from keyword_matcher import show_keyword_match` to cli.py import block (alphabetical order between jd_analyzer and llm_client imports)
- Added `if analysis is not None:` guard followed by `show_keyword_match(analysis, result.content)` call after `show_diff` in main() try block
- Added new test function `test_show_keyword_match_called_when_analysis_not_none` asserting mock_show_keyword_match.assert_called_once_with(analysis_dict, tailored_content)
- Added `@patch("cli.show_keyword_match")` safety patch to `test_generate_called_with_analysis_dict_when_analysis_succeeds`
- Full suite: 104 tests passing, 3 skipped (Ollama not available — expected in CI), 0 failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire show_keyword_match into cli.py** - `fff96c9` (feat)
2. **Task 2: Add show_keyword_match integration test to cli_test.py** - `d6cf20d` (feat)

## Files Created/Modified

- `src/cli.py` — import added + 2-line call site wired (3 lines total added)
- `src/cli_test.py` — 1 new test function (27 lines) + safety decorator + parameter on existing test

## Decisions Made

- Call site placed after `show_diff(resume_text, result.content)` and before `print(f"Tailored resume written to: ...")` per D-02
- `if analysis is not None:` guard in cli.py (the caller) keeps keyword_matcher.py module clean per D-07
- T-07-05 mitigation: None guard explicitly prevents AttributeError if pass-1 fails
- Safety `@patch("cli.show_keyword_match")` on `test_generate_called_with_analysis_dict_when_analysis_succeeds` prevents unexpected side effects when `builtins.print` is captured via side_effect

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Known Stubs

None — all call sites are fully wired. show_keyword_match is TTY-gated in keyword_matcher.py so it silently returns in non-TTY test environments.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes. The `if analysis is not None:` guard implements T-07-05 (Tampering — None guard for analysis) as specified in the plan's threat model.

## Self-Check

- [x] src/cli.py contains `from keyword_matcher import show_keyword_match` (grep returns 1)
- [x] src/cli.py contains `if analysis is not None:` (grep returns 1)
- [x] src/cli.py contains `show_keyword_match` 2 times (import + call site)
- [x] src/cli_test.py contains `show_keyword_match` 5 times (new test 2 + existing test decorator + param + patch)
- [x] test function `test_show_keyword_match_called_when_analysis_not_none` exists in cli_test.py line 273
- [x] /workspace/.venv/bin/pytest -x -q exits 0 (104 passed, 3 skipped)
- [x] /workspace/.venv/bin/pytest src/cli_test.py -x -q exits 0 (12 passed)
- [x] /workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q exits 0 (13 passed)
- [x] Commits fff96c9 and d6cf20d verified in git log

## Self-Check: PASSED
