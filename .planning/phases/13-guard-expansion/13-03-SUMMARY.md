---
phase: 13-guard-expansion
plan: "03"
subsystem: guards
tags: [guards, integration, run_guards, GARD-07, unit-tests, wiring]
dependency_graph:
  requires: [13-01, 13-02]
  provides: [run_guards wired with _check_technology_substitution and _check_protected_sections]
  affects: [src/guards.py, tests/unit/test_guards.py]
tech_stack:
  added: []
  patterns:
    - run_guards() dispatch to new guards following existing call-site pattern
    - patch("guards.logger") + call_args_list + any() assertion for integration tests
    - never-raise end-to-end coverage via run_guards(None, None)
key_files:
  created: []
  modified:
    - src/guards.py
    - tests/unit/test_guards.py
decisions:
  - Both new guards appended after _check_hallucinated_employers in run_guards() per plan order
  - run_guards import added to test file to enable GARD-07 integration tests
  - No extra exception handling needed in run_guards() — try/except wrappers inside each guard satisfy D-13
metrics:
  duration: "2m"
  completed: "2026-06-11T21:20:00Z"
  tasks_completed: 2
  files_changed: 2
---

# Phase 13 Plan 03: run_guards() Wiring and GARD-07 Integration Tests Summary

Wired `_check_technology_substitution` and `_check_protected_sections` into `run_guards()` in `src/guards.py` (GARD-07), and added two `@pytest.mark.unit` integration tests to `tests/unit/test_guards.py` proving both guards fire through `run_guards()` and that `run_guards(None, None)` never raises.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Wire both new guards into run_guards() | 1bf5c70 | src/guards.py (+2 call lines) |
| 2 | Add GARD-07 integration tests to test_guards.py | 6e169e9 | tests/unit/test_guards.py (+2 tests, import updated) |

## Verification Results

- `pytest -m unit tests/unit/test_guards.py -v` — 14 passed (12 Plan-01+02 + 2 Plan-03)
- `pytest src/guards_test.py` — 14 passed (existing class-based tests unaffected)
- `ruff check src/guards.py` — All checks passed
- `ruff check tests/unit/test_guards.py` — All checks passed
- `grep -c "def _check_technology_substitution" src/guards.py` — 1
- `grep -c "def _check_protected_sections" src/guards.py` — 1
- One call site each in run_guards() — confirmed by grep -v "def" | grep -c pattern

## Deviations from Plan

None - plan executed exactly as written.

## Implementation Notes

- Task 1 added exactly two lines to run_guards(): `_check_technology_substitution(original_text, tailored_text)` and `_check_protected_sections(original_text, tailored_text)`, after the `_check_hallucinated_employers` call
- Task 2 updated the import line from `from guards import _check_technology_substitution, _check_protected_sections` to also include `run_guards`
- `test_run_guards_calls_technology_substitution` uses the Skills-section diff (Java→Go) with `patch("guards.logger")` and `call_args_list + any()` idiom per PATTERNS.md
- `test_run_guards_new_guards_never_raise` calls `run_guards(None, None)` — the try/except wrappers inside each guard catch the AttributeError from None input, satisfying D-13 end-to-end

## Known Stubs

None. Both guards are fully implemented (Plans 01 and 02) and wired into run_guards(). All GARD-07 requirements are met.

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. Two call-site additions to run_guards() only.

## Self-Check: PASSED

- `src/guards.py` — FOUND (contains both call sites in run_guards())
- `tests/unit/test_guards.py` — FOUND (contains 14 @pytest.mark.unit tests)
- Commit `1bf5c70` — FOUND (feat(13-03): wire _check_technology_substitution and _check_protected_sections into run_guards())
- Commit `6e169e9` — FOUND (test(13-03): add GARD-07 integration tests to test_guards.py)
