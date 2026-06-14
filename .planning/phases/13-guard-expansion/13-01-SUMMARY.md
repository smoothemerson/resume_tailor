---
phase: 13-guard-expansion
plan: "01"
subsystem: guards
tags: [guards, tdd, unit-tests, latex-parsing, technology-substitution]
dependency_graph:
  requires: []
  provides: [_check_technology_substitution, _extract_section, _extract_technologies]
  affects: [src/guards.py, tests/unit/test_guards.py]
tech_stack:
  added: []
  patterns:
    - _extract_section() with re.DOTALL and \header{} lookahead boundary
    - _extract_technologies() stripping LaTeX macros then comma-splitting
    - three-way warning logic (removed+added, removed-only, added-only)
    - never-raise try/except Exception wrapper per D-13
key_files:
  created:
    - tests/unit/test_guards.py
  modified:
    - src/guards.py
decisions:
  - Removed pre-existing unused `import sys` from guards.py (ruff F401, Rule 2 cleanup)
  - Extracted _extract_section() as module-private helper to enable reuse by Plan 02 (_check_protected_sections)
  - Extracted _extract_technologies() as module-private helper for clarity
metrics:
  duration: "3m"
  completed: "2026-06-11T19:21:31Z"
  tasks_completed: 2
  files_changed: 2
---

# Phase 13 Plan 01: Technology Substitution Guard Summary

TDD implementation of `_check_technology_substitution(original, tailored)` in `src/guards.py` (GARD-05) with six `@pytest.mark.unit` tests in `tests/unit/test_guards.py` (TEST-12). The guard detects when the LLM swaps named technologies in the Skills section, emitting three distinct warning variants.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Write failing tests for _check_technology_substitution | 04cb15f | tests/unit/test_guards.py (created) |
| 2 (GREEN) | Implement _check_technology_substitution in guards.py | c8a5e30 | src/guards.py (modified) |

## Verification Results

- `pytest -m unit tests/unit/test_guards.py -x` — 6 passed
- `pytest src/guards_test.py` — 14 passed (existing tests unaffected)
- `ruff check src/guards.py` — All checks passed
- `grep -c "def _check_technology_substitution" src/guards.py` — 1

## TDD Gate Compliance

- RED gate commit: `04cb15f` — `test(13-01): add failing tests for _check_technology_substitution (RED)` — ImportError at collection time confirmed
- GREEN gate commit: `c8a5e30` — `feat(13-01): implement _check_technology_substitution in guards.py (GREEN)` — all 6 tests pass

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Cleanup] Removed unused `import sys` from guards.py**
- **Found during:** Task 2 (ruff check as plan verification step)
- **Issue:** Pre-existing `import sys` in guards.py was unused, causing ruff F401. Plan verification requires `ruff check src/guards.py` exits 0.
- **Fix:** Removed `import sys` line from guards.py
- **Files modified:** src/guards.py
- **Commit:** c8a5e30 (included in Task 2 commit)

## Implementation Notes

- `_extract_section(text, section_name)` uses `rf'\\header\{{{re.escape(section_name)}\}}(.*?)(?=\\header\{{|$)'` with `re.DOTALL` — reusable by Plan 02's `_check_protected_sections`
- `_extract_technologies(section_text)` strips `\textbf{...}` and other LaTeX macros via `re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', ...)` then comma-splits
- `_check_technology_substitution` returns silently if either text lacks `\header{Skills}` (D-04)
- Never-raise wrapper: `try/except Exception as exc: logger.warning(f"Technology substitution check failed: {exc}")` per D-13
- `run_guards()` NOT modified in this plan — GARD-07 wiring is handled in Plan 03

## Known Stubs

None. The function is fully implemented and wired through its test path. `run_guards()` is not yet updated (per plan spec — Plan 03 handles GARD-07 wiring).

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. The guard processes in-memory strings from an existing pipeline and emits `logger.warning()` only.

## Self-Check: PASSED

- `src/guards.py` — FOUND (verified, contains `def _check_technology_substitution` and `def _extract_section`)
- `tests/unit/test_guards.py` — FOUND (verified, contains 6 `@pytest.mark.unit` tests)
- Commit `04cb15f` — FOUND (`test(13-01): add failing tests for _check_technology_substitution (RED)`)
- Commit `c8a5e30` — FOUND (`feat(13-01): implement _check_technology_substitution in guards.py (GREEN)`)
