---
phase: 06-two-pass-pipeline
plan: 01
subsystem: testing
tags: [pytest, unit-tests, tdd, jd_analyzer, llm_client, mocking]

# Dependency graph
requires: []
provides:
  - "RED unit tests for analyze_job_description (6 tests covering success, fallback, truncation, fence-stripping)"
  - "RED unit tests for _build_messages analysis injection (2 tests covering with/without analysis dict)"
affects:
  - 06-two-pass-pipeline (Wave 2 plans implement against these tests)
  - 06-03 (jd_analyzer.py implementation must make test_jd_analyzer.py green)
  - 06-04 (llm_client.py _build_messages extension must make new test_llm_client.py tests green)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RED-first TDD: test files authored before implementation modules exist"
    - "jd_analyzer.requests.post patch target pattern (no health check to patch)"
    - "MagicMock response construction for Ollama /api/chat response shape"

key-files:
  created:
    - tests/unit/test_jd_analyzer.py
  modified:
    - tests/unit/test_llm_client.py

key-decisions:
  - "Fence-wrapped JSON test asserts result is dict (not None) — implementation must strip fences before json.loads"
  - "Connection error test asserts result is None without pytest.raises — fallback path, not raise path"
  - "Truncation test asserts pytest.raises(RuntimeError, match='truncated') — the one non-fallback failure mode"
  - "New _build_messages tests call with 2-arg form to prove backward compatibility (analysis defaults to None)"

patterns-established:
  - "Pattern: @patch('jd_analyzer.requests.post') — no _check_ollama_health to patch for analysis function"
  - "Pattern: mock_response.json.return_value sets full Ollama API envelope {done_reason, message: {content}}"

requirements-completed:
  - PIPE-01
  - PIPE-02
  - PIPE-03
  - PIPE-04

# Metrics
duration: 2min
completed: 2026-06-07
---

# Phase 06 Plan 01: Two-Pass Pipeline Test Scaffold Summary

**RED test suite for analyze_job_description and _build_messages analysis injection — 8 tests total, all start failing until Wave 2 implementation**

## Performance

- **Duration:** 2min
- **Started:** 2026-06-07T17:20:26Z
- **Completed:** 2026-06-07T17:22:02Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created tests/unit/test_jd_analyzer.py with 6 unit tests covering all behavior contracts: success dict return, JSON parse failure returns None, missing keys returns None, connection error returns None, done_reason=length raises RuntimeError with "truncated", fence-wrapped JSON is stripped and returns dict
- Appended 2 new unit tests to tests/unit/test_llm_client.py covering _build_messages with analysis dict (asserts jd_analysis XML tags present) and without analysis (asserts jd_analysis tags absent, proves backward compatibility)
- All tests syntactically valid; all tests start RED (jd_analyzer.py does not exist, _build_messages takes 2 args today)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tests/unit/test_jd_analyzer.py** - `a0984fa` (test)
2. **Task 2: Add _build_messages analysis injection tests** - `54c9d76` (test)

## Files Created/Modified
- `tests/unit/test_jd_analyzer.py` - 6 RED unit tests for analyze_job_description; patch target jd_analyzer.requests.post
- `tests/unit/test_llm_client.py` - 2 new RED tests appended: with/without analysis dict in _build_messages call

## Decisions Made
- Used `test_analyze_job_description_returns_none_on_fence_wrapped_valid_json` as the fence-stripping test name to clearly signal the expected behavior (returns dict, not None) — asserts implementation must strip fences
- Kept test for fence-wrapped JSON as a positive assertion (result is not None, result is dict) rather than just checking for None, making the success contract explicit

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave 1 test scaffold complete; Wave 2 plans (03, 04) can implement against these contracts
- 06-03 must create src/jd_analyzer.py to make test_jd_analyzer.py green
- 06-04 must extend _build_messages signature to make new test_llm_client.py tests green
- No blockers

## Self-Check: PASSED

- tests/unit/test_jd_analyzer.py: EXISTS, syntax OK, 6 test functions
- tests/unit/test_llm_client.py: EXISTS, syntax OK, both new test names present
- Commit a0984fa: EXISTS (Task 1)
- Commit 54c9d76: EXISTS (Task 2)

---
*Phase: 06-two-pass-pipeline*
*Completed: 2026-06-07*
