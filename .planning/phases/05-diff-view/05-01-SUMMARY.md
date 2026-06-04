---
phase: 05-diff-view
plan: "01"
subsystem: ui
tags: [difflib, ansi, tty, unified-diff, normalization]

requires:
  - phase: 04-output-reliability-guards
    provides: guards.py single-concern module pattern and never-raises contract used as template

provides:
  - src/diff_view.py — show_diff(original, tailored) with TTY guard, normalization, ANSI colorization
  - src/diff_view_test.py — 11 unit tests covering TTY gate, normalization, colors, never-raises contract

affects:
  - 05-02 (CLI wiring will import and call show_diff)

tech-stack:
  added: []
  patterns:
    - Single-concern module with one public entry point and private _ helpers (guards.py analog)
    - TTY gate via sys.stdout.isatty() early return
    - ANSI colorization with +++ / --- header guard to prevent header line coloring
    - Blank-line cap normalization (2 max) and trailing-whitespace stripping before diffing

key-files:
  created:
    - src/diff_view.py
    - src/diff_view_test.py
  modified:
    - pyproject.toml

key-decisions:
  - "difflib.unified_diff with lineterm='' prevents double-newline output when iterating diff lines"
  - "header line guard in _colorize(): check startswith('+++') / startswith('---') before startswith('+') / startswith('-')"
  - "_normalize() and _colorize() are pure transforms — no try/except needed; never-raises contract satisfied at show_diff() boundary"
  - "No sys.path.insert in test file — pytest pythonpath=['src'] in pyproject.toml handles import resolution"

patterns-established:
  - "Pure transform helpers in diff_view.py need no try/except; show_diff() is called outside CLI try/except block"
  - "patch('sys.stdout') + mock_stdout.isatty.return_value controls TTY detection in tests"
  - "Captured-print pattern: patch('builtins.print', side_effect=lambda *a: printed.append(a[0] if a else '')) for output assertions"

requirements-completed: [DIFF-01, DIFF-02, DIFF-03]

duration: 2min
completed: 2026-06-04
---

# Phase 05 Plan 01: Diff View Core Module Summary

**TTY-gated normalized unified diff module with ANSI colorization using stdlib difflib — all three DIFF requirements implemented and covered by 11 unit tests**

## Performance

- **Duration:** 79 seconds (~2 min)
- **Started:** 2026-06-04T18:25:10Z
- **Completed:** 2026-06-04T18:26:29Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `src/diff_view.py` implements `show_diff(original, tailored)` with TTY guard (DIFF-02), trailing-whitespace and blank-line normalization (DIFF-03), and unified diff output with ANSI color (DIFF-01)
- `src/diff_view_test.py` provides 11 unit tests across 4 TestCase classes covering all behavioral contracts
- `pyproject.toml` updated with `src/diff_view.py` in alphabetical order in the wheel include list

## Task Commits

1. **Task 1: Create src/diff_view.py** - `01f1962` (feat)
2. **Task 2: Create src/diff_view_test.py and update pyproject.toml** - `36d2f4f` (test)

## Files Created/Modified

- `src/diff_view.py` - Single public function show_diff() with private _normalize() and _colorize() helpers; no external deps (stdlib difflib + sys only)
- `src/diff_view_test.py` - 11 tests in TestShowDiffTTYGate, TestShowDiffNormalization, TestShowDiffColors, TestShowDiffNeverRaises
- `pyproject.toml` - src/diff_view.py added to [tool.hatch.build.targets.wheel] include list

## Decisions Made

- Used `lineterm=""` in `unified_diff()` to prevent double-newline when printing — each line ends without `\n` so `print()` adds exactly one newline
- `_colorize()` checks `startswith("+++")` / `startswith("---")` before `startswith("+")` / `startswith("-")` — mandatory to prevent header lines from being colored
- Pure transform helpers `_normalize()` and `_colorize()` have no try/except — they operate on string inputs that cannot raise; never-raises contract is upheld at the `show_diff()` call site which sits outside the CLI try/except block
- Test file omits `sys.path.insert` — pytest `pythonpath = ["src"]` in pyproject.toml handles module resolution cleanly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All 11 diff_view tests and 47 total suite tests passed on first run. A pre-existing `SyntaxWarning` in `src/llm_client.py` (invalid `\d` escape sequence) was noted but left untouched as it is out of scope for this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `show_diff()` is ready to import and call from `src/cli.py` in Plan 05-02 (Wave 2)
- Integration point: after `run_guards()` and before the final `print(f"Tailored resume written to: ...")` in `cli.py`
- No blockers

---
*Phase: 05-diff-view*
*Completed: 2026-06-04*
