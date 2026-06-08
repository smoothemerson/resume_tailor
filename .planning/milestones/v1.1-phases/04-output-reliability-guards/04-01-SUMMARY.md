---
phase: 04-output-reliability-guards
plan: 01
subsystem: testing
tags: [guards, namedtuple, regex, latex, warnings, stderr]

# Dependency graph
requires:
  - phase: 03-cli-wiring
    provides: llm_client.py with generate_tailored_resume() and _strip_fences()
provides:
  - TailorResult(content, fences_stripped) NamedTuple in llm_client.py
  - src/guards.py with run_guards(), _check_missing_sections(), _check_format_violations(), _check_hallucinated_employers()
  - 13 new unit tests in src/guards_test.py covering GUARD-01 through GUARD-04
  - 4 new unit tests in src/llm_client_test.py covering TailorResult return type
affects: [04-output-reliability-guards, 04-02-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TailorResult NamedTuple return type carries metadata alongside primary value
    - Non-fatal guard functions: _check_* functions never raise; wrap body in try/except Exception
    - Warning output via logger.warning() from log_manager (not direct print)

key-files:
  created:
    - src/guards.py
    - src/guards_test.py
  modified:
    - src/llm_client.py
    - src/llm_client_test.py

key-decisions:
  - "TailorResult NamedTuple chosen over returning plain str to carry fences_stripped metadata to cli.py without requiring global state"
  - "Each _check_* function internally exception-safe (try/except Exception) so run_guards() never raises under any input (GUARD-04)"
  - "_EMPLOYER_PATTERN compiled at module level as re.compile() for reuse efficiency"

patterns-established:
  - "Non-fatal guard pattern: private _check_* functions returning None, all wrapped in try/except, called by public run_guards()"
  - "Warning output: always via logger.warning() from log_manager, never via direct print to stderr"
  - "Fences detection: compute raw.strip() != _strip_fences(raw) before stripping, not after"

requirements-completed: [GUARD-01, GUARD-02, GUARD-03, GUARD-04]

# Metrics
duration: 2min
completed: 2026-06-02
---

# Phase 4 Plan 01: Output Reliability Guards — Building Blocks Summary

**TailorResult NamedTuple in llm_client.py and guards.py with run_guards() plus three _check_* functions for dropped-section, format-violation, and employer-hallucination detection**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-02T18:45:45Z
- **Completed:** 2026-06-02T18:47:43Z
- **Tasks:** 2
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments

- Refactored `generate_tailored_resume()` to return `TailorResult(content, fences_stripped)` NamedTuple instead of plain `str`, enabling GUARD-02's fences-detection sub-check without global state
- Created `src/guards.py` with `run_guards()` public entry point and three private `_check_*` functions covering GUARD-01 (missing sections), GUARD-02 (format violations), and GUARD-03 (employer hallucination)
- Added 17 new unit tests (4 in `llm_client_test.py`, 13 in `guards_test.py`) — all 35 tests pass

## Task Commits

Each task was committed atomically with TDD RED/GREEN commits:

1. **Task 1 RED: TailorResult failing tests** - `cf0049f` (test)
2. **Task 1 GREEN: TailorResult implementation** - `4a2df17` (feat)
3. **Task 2 RED: guards.py failing tests** - `c3d9754` (test)
4. **Task 2 GREEN: guards.py implementation** - `b12009c` (feat)

_TDD tasks have RED (test) + GREEN (feat) commits per TDD execution flow_

## Files Created/Modified

- `/workspace/src/llm_client.py` - Added `TailorResult` NamedTuple, changed `generate_tailored_resume()` return type from `str` to `TailorResult`, replaced final return block with fences_stripped detection
- `/workspace/src/llm_client_test.py` - Added `TailorResult` import and 4 new tests for return type/fences behavior
- `/workspace/src/guards.py` - New module with `run_guards()`, `_check_missing_sections()`, `_check_format_violations()`, `_check_hallucinated_employers()`, `_EMPLOYER_PATTERN` compiled regex
- `/workspace/src/guards_test.py` - New test module with 13 tests covering all four guard requirements

## Decisions Made

- `TailorResult` NamedTuple is the cleanest way to thread `fences_stripped` metadata from `llm_client.py` to `cli.py` without global state or function signature changes to callers
- Each `_check_*` function wraps its entire body in `try/except Exception` and logs a warning on internal failure — this ensures `run_guards()` can never raise (GUARD-04)
- `_EMPLOYER_PATTERN` compiled at module level (not inside the function) for minor efficiency improvement — no functional change

## Deviations from Plan

None - plan executed exactly as written. Both tasks followed TDD RED/GREEN cycle as specified.

## Issues Encountered

None — pre-existing `SyntaxWarning` in llm_client.py system prompt string (invalid `\d` escape) was already present before this plan and is out of scope per deviation boundary rules.

## Next Phase Readiness

- `TailorResult` and `guards.py` are ready for wiring into `cli.py` in Plan 02
- Plan 02 will: import `run_guards` and `TailorResult` in `cli.py`, change `content = generate_tailored_resume(...)` to `result = ...`, call `run_guards(resume_text, result.content, result.fences_stripped)`, pass `result.content` to `write_resume()`
- Plan 02 will also need to update `cli_test.py` mock return values from plain `str` to `TailorResult` (5 tests affected — pitfall documented in RESEARCH.md)

---
*Phase: 04-output-reliability-guards*
*Completed: 2026-06-02*
