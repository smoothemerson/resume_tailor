---
phase: 12-prompt-precision
plan: 02
subsystem: llm
tags: [prompt-engineering, ollama, guards, fabrication, temperature]

requires:
  - phase: 12-01
    provides: "ALLOWED/CONSTRAINTS system prompt with TECHNOLOGY FIDELITY rule and six rewritable elements"

provides:
  - "options.temperature=0.2 in tailoring payload for deterministic-leaning sampling"
  - "JD ANALYSIS USAGE rule in CONSTRAINTS block framing jd_analysis as relevance-ranking signals only"
  - "Inline fidelity reminders on the four fabrication-prone ALLOWED bullets"
  - "_check_fabricated_technologies() guard with token-boundary, case-insensitive, re.escape-safe matching"
  - "run_guards() extended with jd_technologies keyword parameter"
  - "cli.py wiring analysis.technologies into run_guards"

affects: []

tech-stack:
  added: []
  patterns:
    - "Guard pipeline: private function + try/except + logger.warning + never raises"
    - "Dict-unpacking kwarg passing (**{k: v} if cond else {}) to add optional kwargs without breaking existing positional call assertions"

key-files:
  created: []
  modified:
    - src/llm_client.py
    - src/guards.py
    - src/cli.py
    - src/guards_test.py
    - tests/unit/test_llm_client.py

key-decisions:
  - "Used **{'jd_technologies': ...} if analysis else {} dict-unpacking in cli.py to conditionally pass jd_technologies only when analysis is not None, preserving existing test assertions that check run_guards is called with exactly 3 positional args when analysis=None"
  - "Chose temperature=0.2 over 0 (greedy) to avoid degenerate repetition risk on full-document LaTeX rewrite with a 14B local model; 0.2 collapses most sampling variance while staying above pure greedy"
  - "Placed JD ANALYSIS USAGE rule immediately after TECHNOLOGY FIDELITY paragraph inside CONSTRAINTS block so both rules are co-located and the system never sees jd_analysis as a list of desired technologies"
  - "Single-character technology names (len < 2) are skipped in the fabrication guard to avoid false positives on 'C' and 'R'"

requirements-completed:
  - PRMP-03

duration: 25min
completed: 2026-06-13
---

# Phase 12 Plan 02: Prompt Precision (Gap Closure) Summary

**Three-layer anti-fabrication defense: temperature=0.2 in payload, JD ANALYSIS USAGE rule in system prompt with inline fidelity reminders on four ALLOWED bullets, and a deterministic _check_fabricated_technologies guard wired from cli.py**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-06-13T00:00:00Z
- **Completed:** 2026-06-13T00:25:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Payload now sends `{"num_ctx": 8192, "temperature": 0.2}` on every tailoring request, reducing sampling variance that caused non-deterministic fabrication failures
- System prompt CONSTRAINTS block includes a "JD ANALYSIS USAGE:" rule with the phrases "relevance-ranking signals" and "must never appear in the output" to defuse the jd_analysis priming effect
- The four fabrication-prone ALLOWED bullets (employer taglines, employer bullets, project subtitle, project bullets) each carry the inline reminder "(mention only technologies already present in the original resume)"
- `_check_fabricated_technologies()` in guards.py uses `re.compile` with `re.escape` and word-boundary lookarounds for case-insensitive token-bounded matching, wrapped in try/except per the existing guard pattern
- `run_guards()` extended with `jd_technologies: list | None = None` as the fourth parameter; default None preserves backward compatibility
- `cli.py` passes `analysis["technologies"]` into run_guards when analysis is not None, omitting the kwarg entirely when analysis is None

## Task Commits

Each task was committed atomically (TDD: test then feat):

1. **Task 1: Temperature and prompt edits (RED)** - `de946a1` (test)
2. **Task 1: Temperature and prompt edits (GREEN)** - `9df86fc` (feat)
3. **Task 2: Technology-fidelity guard (RED)** - `e1d1b3b` (test)
4. **Task 2: Technology-fidelity guard (GREEN)** - `2e7e05c` (feat)

## Files Created/Modified
- `src/llm_client.py` - Added temperature 0.2 to options, JD ANALYSIS USAGE rule in CONSTRAINTS, inline fidelity reminders on 4 ALLOWED bullets
- `src/guards.py` - Added `_check_fabricated_technologies()` private function and extended `run_guards()` signature
- `src/cli.py` - Wired `jd_technologies` from analysis into run_guards via conditional dict-unpacking
- `src/guards_test.py` - Added `TestCheckFabricatedTechnologies` class (8 test cases) and extended `TestRunGuardsNeverRaises`
- `tests/unit/test_llm_client.py` - Added 4 new tests: payload options assertion, JD ANALYSIS USAGE label, relevance-ranking phrases, and inline fidelity reminder count

## Decisions Made
- Used `**{"jd_technologies": analysis["technologies"]} if analysis else {}` dict-unpacking pattern in cli.py. Passing `jd_technologies=None` explicitly would break the existing `assert_called_once_with("resume text", content, False)` test when analysis=None. The dict-unpacking approach omits the kwarg entirely when analysis is None, satisfying both the plan's wiring requirement and the "all existing tests pass without modification" constraint.
- Temperature 0.2 chosen over 0 (greedy decoding) to avoid repetition risk on a 14B model producing full-document LaTeX rewrites.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Conditional jd_technologies passing to avoid breaking existing cli_test.py assertion**
- **Found during:** Task 2 (GREEN phase implementation)
- **Issue:** The plan's action item `run_guards(..., jd_technologies=analysis.get("technologies") if analysis else None)` passes `jd_technologies=None` explicitly when analysis is None. The existing `test_end_sentinel_breaks_loop` test asserts `run_guards` is called with exactly 3 positional args when analysis=None. Adding a `jd_technologies=None` kwarg breaks `assert_called_once_with`.
- **Fix:** Used `**{"jd_technologies": analysis["technologies"]} if analysis else {}` to conditionally include the kwarg only when analysis is not None. This satisfies the plan's semantic requirement (wire technologies from analysis) and the must_haves constraint (no test modification).
- **Files modified:** src/cli.py
- **Verification:** `pytest src/cli_test.py -x -q` passes 12 tests; `pytest -x -q` passes 125 tests
- **Committed in:** 2e7e05c

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug: plan action vs existing test assertion conflict)
**Impact on plan:** Fix is strictly compatible with plan intent. jd_technologies flows through to run_guards whenever analysis is not None. No scope creep.

## Issues Encountered

None beyond the deviation documented above.

## Known Stubs

None — all guard logic is complete and wired; no placeholder values or TODO markers.

## Threat Flags

Per plan threat model T-12.02-01: `re.escape` is applied to every technology token before compilation. No LLM-controlled regex metacharacters reach `re.compile`. Lookaround boundaries are fixed literals. No new network endpoints, auth paths, file access patterns, or dependencies introduced.

## Verification Results

- `pytest tests/unit/test_llm_client.py -x -q` — 38 passed (26 pre-existing + 4 new, plus 8 previously-added phase-12 tests)
- `pytest src/llm_client_test.py -x -q` — 15 passed (all pre-existing)
- `pytest src/guards_test.py -x -q` — 23 passed (14 pre-existing + 9 new)
- `pytest src/cli_test.py -x -q` — 12 passed (all pre-existing)
- `pytest -x -q` — 125 passed, 3 skipped (Ollama-dependent, expected)
- Spot checks:
  - `grep -c '"temperature": 0.2' src/llm_client.py` = 1
  - `grep -c 'JD ANALYSIS USAGE' src/llm_client.py` = 1
  - fidelity reminder count = 4
  - `_check_fabricated_technologies` in guards.py = 2 (definition + call)
  - `jd_technologies` in cli.py = 1

## Next Phase Readiness
- UAT Test 1 re-run is the human verification step that closes the gap (deterministic layer guarantees named warnings on fabrication even if probabilistic layer fails)
- All three root-cause factors have been addressed: (1) temperature added, (2) jd_analysis framing corrected, (3) post-generation guard added
- No blockers for next phase

---
*Phase: 12-prompt-precision*
*Completed: 2026-06-13*

## Self-Check: PASSED

- src/llm_client.py: contains `"temperature": 0.2`, `JD ANALYSIS USAGE:`, inline fidelity reminder x4
- src/guards.py: contains `_check_fabricated_technologies` (definition + call in run_guards)
- src/cli.py: contains `jd_technologies`
- src/guards_test.py: contains `TestCheckFabricatedTechnologies`
- tests/unit/test_llm_client.py: contains `test_generate_tailored_resume_payload_includes_temperature`
- Commits de946a1, 9df86fc, e1d1b3b, 2e7e05c all exist
- Full test suite: 125 passed, 3 skipped
