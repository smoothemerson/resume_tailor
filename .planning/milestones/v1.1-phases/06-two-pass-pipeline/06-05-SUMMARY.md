---
phase: 06-two-pass-pipeline
plan: 05
subsystem: cli
tags: [cli, two-pass-pipeline, jd_analyzer, llm_client, integration]

# Dependency graph
requires:
  - phase: 06-03
    provides: "src/jd_analyzer.py with analyze_job_description(job_description, model=None) -> dict | None"
  - phase: 06-04
    provides: "generate_tailored_resume extended with optional analysis: dict | None = None parameter"
provides:
  - "src/cli.py with two-pass orchestration: analyze_job_description then generate_tailored_resume(analysis=analysis)"
  - "All 11 src/cli_test.py tests passing GREEN"
  - "PIPE-01, PIPE-02, PIPE-03, PIPE-04 fully wired end-to-end"
affects:
  - Phase 07 (integration verification against live Ollama; full pipeline smoke test)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-pass orchestration: analyze_job_description inside try block before generate_tailored_resume; analysis result forwarded via analysis= kwarg"
    - "Pass-1 progress message before analyze call; pass-2 progress message before tailoring call — each print immediately precedes its respective LLM call"

key-files:
  created: []
  modified:
    - src/cli.py

key-decisions:
  - "analyze_job_description placed inside the try block so RuntimeError from done_reason=length is caught by existing except (RuntimeError, ValueError, OSError) handler — clean error exit"
  - "analysis=None fallback is transparent: jd_analyzer returns None on any parse failure; generate_tailored_resume accepts None and produces single-pass output (PIPE-03 preserved)"

requirements-completed:
  - PIPE-01
  - PIPE-02
  - PIPE-03
  - PIPE-04

# Metrics
duration: 5min
completed: 2026-06-07
---

# Phase 06 Plan 05: CLI Two-Pass Pipeline Wiring Summary

**Two targeted edits to src/cli.py wire the complete two-pass pipeline: import analyze_job_description, insert pass-1 progress + analysis call inside try block, forward analysis result to generate_tailored_resume via analysis= keyword argument — all 11 cli_test.py tests green, full suite 89 passed**

## Performance

- **Duration:** 5min
- **Started:** 2026-06-07T17:45:00Z
- **Completed:** 2026-06-07T17:50:00Z
- **Tasks:** 1 (of 2; 1 auto completed, 1 checkpoint:human-verify pending)
- **Files modified:** 1

## Accomplishments

- Added `from jd_analyzer import analyze_job_description` import to src/cli.py
- Replaced single-pass block with two-pass block: `print("Analyzing job description...", flush=True)` before the try, `analyze_job_description(job_description, model=args.model)` first inside try, `print("Tailoring resume — this may take a minute...", flush=True)` before generate call
- Forwarded `analysis` result to `generate_tailored_resume(..., analysis=analysis, model=args.model)`
- All 11 src/cli_test.py tests GREEN (3 new: test_analyzing_progress_message_printed, test_generate_called_with_analysis_none_when_analysis_fails, test_generate_called_with_analysis_dict_when_analysis_succeeds)
- Full test suite: 89 passed, 2 skipped (Ollama integration tests, expected)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire two-pass pipeline into src/cli.py** - `9002c1a` (feat)

## Files Created/Modified

- `src/cli.py` — Two edits: (1) import added; (2) single-pass block replaced with two-pass block. analyze_job_description inside try block, result forwarded to generate_tailored_resume as analysis= kwarg.

## Decisions Made

- analyze_job_description placed inside the try block (per PLAN action block) so RuntimeError from done_reason=length is caught by existing error handler — exits cleanly per D-05
- "Analyzing job description..." print placed before the try block (before analyze call) so it appears as first visible output; "Tailoring resume..." placed inside try immediately before generate call
- No changes to any other module — cli.py wiring was the only remaining work after plans 06-03 and 06-04

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. The two-pass pipeline is fully wired. analyze_job_description -> analysis dict -> generate_tailored_resume(_build_messages jd_analysis XML block). No placeholder values.

## Threat Flags

No new threat surface introduced. Analysis dict forwarded from jd_analyzer to generate_tailored_resume as in-process function argument. No network boundary, no file write, no shell execution. Accepted per T-06-08, T-06-10.

## Issues Encountered

None.

## Checkpoint Pending

Task 2 (checkpoint:human-verify) is pending human verification:
- Run: `uv run pytest --tb=short -q` — should show 89 passed, 2 skipped
- Optional live smoke test requires Ollama running locally

## User Setup Required

None for unit tests. Live smoke test requires Ollama running at localhost:11434.

## Next Phase Readiness

- Phase 06 Plan 05 auto tasks complete
- Human verification checkpoint pending (see Checkpoint Pending section)
- After checkpoint approval, Phase 06 is fully complete
- No blockers for Phase 07 (integration testing)

## Self-Check: PASSED

- src/cli.py modified: EXISTS (9002c1a commit)
- Commit 9002c1a: EXISTS (confirmed via git rev-parse)
- `from jd_analyzer import analyze_job_description` in cli.py: CONFIRMED (grep match)
- `analysis=analysis` in cli.py: CONFIRMED (grep match)
- `Analyzing job description` in cli.py: CONFIRMED (grep match)
- All 11 cli_test.py tests: PASSING (uv run pytest src/cli_test.py -x -q: 11 passed)
- Full suite: PASSING (89 passed, 2 skipped)

---
*Phase: 06-two-pass-pipeline*
*Completed: 2026-06-07*
