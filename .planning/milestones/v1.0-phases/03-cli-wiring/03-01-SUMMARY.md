---
phase: "03"
plan: "01"
subsystem: cli
tags: [cli, orchestration, tdd, input-loop, error-handling]
dependency_graph:
  requires: [src/config.py, src/resume_reader.py, src/llm_client.py, src/resume_writer.py]
  provides: [src/cli.py, src/cli_test.py]
  affects: []
tech_stack:
  added: [pytest>=9.0.3 (dev)]
  patterns: [TDD RED/GREEN, argparse --help only, multiline input loop with END sentinel, try/except at CLI boundary]
key_files:
  created: [src/cli_test.py]
  modified: [src/cli.py, pyproject.toml]
decisions:
  - "sys.argv patched in all tests to prevent argparse from consuming pytest CLI arguments"
  - "pytest added as dev dependency via uv add --dev to enable test execution"
metrics:
  duration: "2 minutes"
  completed: "2026-05-29"
  tasks_completed: 2
  files_changed: 3
---

# Phase 3 Plan 1: CLI Wiring — cli.py Orchestration Summary

**One-liner:** Full main() orchestration in cli.py with banner, END-sentinel input loop, progress flush, try/except error boundary, and absolute-path success message, verified by 5 unit tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED (TDD) | Failing tests for cli.py main() | aba9cff | src/cli_test.py (created) |
| 1 GREEN | Implement cli.py:main() (D-01 through D-08) | 3c63fef | src/cli.py, src/cli_test.py |
| 2 | Add pytest dev dependency | 739f373 | pyproject.toml |

## What Was Built

`src/cli.py:main()` implements the complete end-to-end orchestration:

1. Argparse with prog="resume-tailor" for --help
2. Banner: four print() calls to stdout (D-04, D-06)
3. Input loop: `while True` with `input()`, breaks on EOFError or "END" sentinel, accumulates lines (D-05)
4. Empty JD guard: prints to stderr, exits 1 (T-03-03 mitigation)
5. Progress message: `print(..., flush=True)` before LLM call (D-08, CORE-03)
6. try/except (RuntimeError, ValueError): catches llm_client errors, prints to stderr, exits 1 (D-02, D-03)
7. Success: prints absolute path via `output_path.resolve()` (CORE-06)

`src/cli_test.py` covers 5 behavioral paths across 3 test classes:
- TestInputLoop (3): END sentinel, EOF submission, empty JD guard
- TestErrorHandling (1): RuntimeError from LLM exits 1
- TestSuccessPath (1): success prints "Tailored resume written to:"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed argparse consuming pytest CLI arguments in tests**
- **Found during:** Task 1 GREEN phase (first test run)
- **Issue:** `parser.parse_args()` with no args reads from `sys.argv` by default; when running under pytest, sys.argv contains pytest's own arguments (e.g., `src/cli_test.py -v --tb=short`), causing argparse to fail with exit code 2 instead of proceeding to the test behavior
- **Fix:** Added `@patch("sys.argv", ["resume-tailor"])` decorator to all 5 test methods so argparse sees a clean argv during test execution
- **Files modified:** src/cli_test.py
- **Commit:** 3c63fef

**2. [Rule 3 - Blocking] Added pytest dev dependency**
- **Found during:** Task 1 RED phase setup
- **Issue:** pytest not installed in the project virtual environment; `python -m pytest` returned "No module named pytest"
- **Fix:** `uv add --dev pytest` added pytest>=9.0.3 to `[dependency-groups]` in pyproject.toml
- **Files modified:** pyproject.toml
- **Commit:** 739f373

## Verification Results

All 5 plan verification checks pass:
1. `python src/cli.py --help` exits 0 with "Tailor a LaTeX resume to a job description using a local Ollama LLM."
2. `echo -e "Senior ML Engineer role\nEND" | python src/cli.py` exits 1 with stderr message (no traceback)
3. `pytest src/cli_test.py -v` exits 0 with 5 tests passing
4. `grep -c "log_manager" src/cli.py` returns 0
5. `grep -c "flush=True" src/cli.py` returns 1

## TDD Gate Compliance

- RED gate: `test(03-01)` commit aba9cff — 5 failing tests committed before implementation
- GREEN gate: `feat(03-01)` commit 3c63fef — implementation passes all 5 tests
- REFACTOR: No refactor needed; implementation was clean on first pass

## Self-Check: PASSED
