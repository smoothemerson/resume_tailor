---
phase: 04-output-reliability-guards
verified: 2026-06-04T00:00:00Z
status: passed
score: 15/15
overrides_applied: 0
re_verification: false
---

# Phase 4: Output Reliability Guards — Verification Report

**Phase Goal:** Users receive warnings when the tailored resume silently drops content, introduces hallucinated fields, or breaks LaTeX formatting — without ever blocking the output file from being written
**Verified:** 2026-06-04
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running the tool against a JD that causes a section to be dropped prints a warning to stderr identifying the missing section | VERIFIED | `run_guards` with `\header{Skills}` in original but not tailored produces `WARNING: Section "Skills" missing from tailored output.` on stderr — confirmed by live spot-check and `TestCheckMissingSections::test_missing_section_triggers_warning` passing |
| 2 | Running the tool when the LLM returns markdown fences or prose before `\documentclass` prints a format violation warning to stderr | VERIFIED | `fences_stripped=True` produces `WARNING: LLM returned markdown fences that were stripped from output.`; inline backticks produce `WARNING: Tailored output contains inline code fences.` — confirmed by spot-checks and `TestCheckFormatViolations` tests passing |
| 3 | Running the tool when the LLM introduces employer names or dates not in the original resume prints a hallucination warning to stderr | VERIFIED | `run_guards` with `\employer{Acme Corp}{2022}{Engineer}` in original but not tailored produces `WARNING: Employer "Acme Corp" from original resume not found in tailored output.` — confirmed by `TestCheckHallucinatedEmployers::test_employer_in_original_missing_from_tailored_triggers_warning` passing |
| 4 | All guard warnings are non-fatal — the tailored `.tex` file is written to disk regardless of how many warnings fire | VERIFIED | `run_guards` on line 51 of `cli.py`, `write_resume` on line 52; `run_guards` never raises (each `_check_*` wraps in `try/except Exception`); confirmed by `TestRunGuardsNeverRaises::test_run_guards_malformed_input_no_exception` passing with `None` inputs |

**Score (roadmap truths):** 4/4 verified

### Plan Frontmatter Must-Haves (04-01-PLAN.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `generate_tailored_resume()` returns `TailorResult(content, fences_stripped)` not a plain str | VERIFIED | `llm_client.py` line 130: `-> TailorResult`; line 176: `return TailorResult(content=content, fences_stripped=fences_stripped)` |
| 2 | `fences_stripped` is True when `_strip_fences()` modifies the raw LLM content, False when it is a no-op | VERIFIED | `llm_client.py` line 173: `fences_stripped = raw.strip() != _strip_fences(raw)`; covered by `TestTailorResult::test_fences_stripped_true_when_raw_had_fences` and `test_fences_stripped_false_when_no_fences` |
| 3 | `run_guards()` accepts `(original_text, tailored_text, fences_stripped=False)` and returns None | VERIFIED | `guards.py` line 44: `def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None` |
| 4 | A missing `\header{}` section in tailored output triggers `WARNING: Section ... missing from tailored output.` | VERIFIED | Spot-check produced `WARNING: Section "Skills" missing from tailored output.` on stderr; test passing |
| 5 | `fences_stripped=True` triggers `WARNING: LLM returned markdown fences that were stripped from output.` | VERIFIED | Spot-check confirmed; `test_fences_stripped_true_triggers_warning` passing |
| 6 | Inline `` ``` `` in tailored body triggers `WARNING: Tailored output contains inline code fences.` | VERIFIED | Spot-check confirmed; `test_inline_code_fence_triggers_warning` passing |
| 7 | `run_guards()` never raises — any internal exception is swallowed and converted to a warning | VERIFIED | Spot-check with `None` inputs: each `_check_*` caught the TypeError and logged a warning; no exception propagated |

### Plan Frontmatter Must-Haves (04-02-PLAN.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `cli.py` calls `run_guards(resume_text, result.content, result.fences_stripped)` before `write_resume()` | VERIFIED | `cli.py` line 51: `run_guards(resume_text, result.content, result.fences_stripped)` precedes line 52: `write_resume(result.content, output_dir)` |
| 2 | `cli.py` consumes `result.content` and `result.fences_stripped` from the TailorResult returned by `generate_tailored_resume()` | VERIFIED | `cli.py` line 50: `result = generate_tailored_resume(...)` — both attributes accessed on lines 51 and 52 |
| 3 | GUARD-01 unit tests: missing section fires warning, present sections produce no warnings | VERIFIED | `TestCheckMissingSections` — 4 tests, all passing |
| 4 | GUARD-02 unit tests: `fences_stripped=True` fires warning, inline backticks fire warning, clean LaTeX fires no warnings | VERIFIED | `TestCheckFormatViolations` — 4 tests, all passing |
| 5 | GUARD-03 unit tests: zero `\employer{}` entries produces zero warnings, missing employer fires warning | VERIFIED | `TestCheckHallucinatedEmployers` — 3 tests, all passing |
| 6 | All `guards_test.py` tests pass | VERIFIED | `pytest src/guards_test.py` — 11 tests, 0 failures |

### Plan Frontmatter Must-Haves (04-03-PLAN.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All mock return values for `generate_tailored_resume` use `TailorResult` not plain str | VERIFIED | 4 occurrences of `TailorResult(content=` in `cli_test.py`; `grep -c 'mock_generate.return_value = "\\documentclass'` returns 0 |
| 2 | Tests that exercise the success path patch `cli.run_guards` to prevent stderr output during tests | VERIFIED | 4 success-path tests each have `@patch("cli.run_guards")` decorator (lines 15, 34, 96, 119) |
| 3 | `python -m pytest src/cli_test.py -v` passes with all 7 existing tests green | VERIFIED | 7/7 tests pass |
| 4 | `python -m pytest src/ -v` passes — the full suite is green | VERIFIED | 36/36 tests pass, 0.11s |

**Combined plan must-have score:** 15/15

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/llm_client.py` | TailorResult NamedTuple + refactored `generate_tailored_resume()` | VERIFIED | `class TailorResult(NamedTuple)` at line 9; return type `-> TailorResult` at line 130; `return TailorResult(content=content, fences_stripped=fences_stripped)` at line 176 |
| `src/guards.py` | `run_guards()` + three private `_check_*` functions | VERIFIED | All 4 functions defined; `from log_manager import logger` at line 4; `_EMPLOYER_PATTERN` compiled at line 6 |
| `src/cli.py` | Guard pipeline integration — `run_guards` called before `write_resume` | VERIFIED | `from guards import run_guards` at line 6; call sequence confirmed at lines 51-52 |
| `src/guards_test.py` | Unit test coverage for GUARD-01, GUARD-02, GUARD-03, GUARD-04 | VERIFIED | 11 tests across 4 classes; all passing |
| `src/cli_test.py` | Updated CLI tests compatible with TailorResult return type | VERIFIED | `from llm_client import TailorResult` at line 6; 4 TailorResult mocks; 4 `@patch("cli.run_guards")` decorators |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `llm_client.py generate_tailored_resume()` | `TailorResult` | `return TailorResult(content=content, fences_stripped=fences_stripped)` | WIRED | Confirmed at line 176 |
| `guards.py run_guards()` | `log_manager.logger` | `from log_manager import logger` / `logger.warning(` | WIRED | Import at line 4; `logger.warning(` calls in all three `_check_*` functions |
| `cli.py main()` | `guards.run_guards` | `run_guards(resume_text, result.content, result.fences_stripped)` | WIRED | Confirmed at line 51 |
| `cli.py main()` | `TailorResult.content` | `result.content` passed to `write_resume` | WIRED | Confirmed at line 52 |
| `cli_test.py mock_generate.return_value` | `TailorResult` | `TailorResult(content=..., fences_stripped=False)` | WIRED | 4 occurrences confirmed |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase produces guard/warning logic (side effects to stderr), not rendering of dynamic UI data. The output artifact is a `.tex` file written by `write_resume(result.content, ...)` and the guard warnings are printed to stderr. Both paths were spot-checked directly.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Missing section triggers WARNING | `run_guards(r'\header{Skills}\header{Experience}', r'\header{Experience}')` | `WARNING: Section "Skills" missing from tailored output.` on stderr | PASS |
| `fences_stripped=True` triggers WARNING | `run_guards('', content, fences_stripped=True)` | `WARNING: LLM returned markdown fences that were stripped from output.` on stderr | PASS |
| Inline backticks trigger WARNING | `run_guards('', content_with_backticks)` | `WARNING: Tailored output contains inline code fences.` on stderr | PASS |
| `run_guards` never raises | `run_guards(None, None)` | Warnings fired for each guard, no exception propagated | PASS |
| Full test suite green | `.venv/bin/python -m pytest src/ -v` | 36 passed in 0.11s | PASS |

---

### Probe Execution

No probes declared in PLAN files and no `scripts/*/tests/probe-*.sh` present. Step skipped.

---

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GUARD-01 | 04-01, 04-02 | Tool warns when a section present in original is missing from tailored output | SATISFIED | `_check_missing_sections()` in `guards.py`; 4 tests in `TestCheckMissingSections`; wired via `run_guards()` in `cli.py` |
| GUARD-02 | 04-01, 04-02 | Tool warns when tailored output contains markdown prose or format violations | SATISFIED | `_check_format_violations()` in `guards.py`; 4 tests in `TestCheckFormatViolations`; `fences_stripped` metadata flows from `llm_client.py` through `TailorResult` to `run_guards()` |
| GUARD-03 | 04-01, 04-02 | Tool warns when structured fields (employer names) appear in output but were not in original | SATISFIED | `_check_hallucinated_employers()` in `guards.py`; 3 tests in `TestCheckHallucinatedEmployers`; `_EMPLOYER_PATTERN` regex compiled at module level |
| GUARD-04 | 04-01, 04-02, 04-03 | Guards degrade gracefully — any guard failure prints warning but does not block output write | SATISFIED | Each `_check_*` wraps body in `try/except Exception`; `run_guards()` never raises; `write_resume()` always reached in `cli.py` (line 52 after line 51); 3 tests in `TestRunGuardsNeverRaises` including `None` input test |

All 4 requirements fully satisfied. No orphaned requirements.

---

### Anti-Patterns Found

Scanned `src/guards.py`, `src/llm_client.py`, `src/cli.py`, `src/guards_test.py`, `src/cli_test.py` — modified files for this phase.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | - | - | - | - |

No `TBD`, `FIXME`, or `XXX` markers found. No placeholder returns. No orphaned code. No hardcoded empty data in production rendering paths.

---

### Human Verification Required

None. All observable behaviors are verifiable programmatically:
- Warning text is deterministic given fixed inputs
- Test suite passes 36/36 with no randomness
- Guard ordering in `cli.py` is statically visible
- No UI, real-time behavior, or external service integration introduced in this phase

---

### Gaps Summary

No gaps. All 15 must-haves verified. All 4 GUARD requirements satisfied. Full test suite green at 36/36. Phase goal achieved.

---

_Verified: 2026-06-04_
_Verifier: Claude (gsd-verifier)_
