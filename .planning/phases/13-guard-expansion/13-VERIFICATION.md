---
phase: 13-guard-expansion
verified: 2026-06-12T18:16:25Z
status: gaps_found
score: 9/10 must-haves verified
overrides_applied: 0
gaps:
  - truth: "_check_protected_sections warns when the contact block differs between original and tailored"
    status: failed
    reason: >
      The implementation uses `if original_contact_m is not None and tailored_contact_m is not None`
      on guards.py:82. When the LLM removes the contact block entirely from the tailored output,
      tailored_contact_m is None, the condition is False, and no warning fires.
      Complete removal of the contact block is the worst-case mutation (candidate name, email, and
      phone all silently disappear) and produces zero user-facing signal. Confirmed by running
      _check_protected_sections(original_with_contact, tailored_without_contact) — 0 warnings.
      GARD-06 requires warning "when any of the following differ between original and tailored:
      contact block" — removal is the extreme case of differing. Roadmap SC #3 likewise requires
      warnings "for each protected element type."
    artifacts:
      - path: "src/guards.py"
        issue: "Line 82: both-not-None guard short-circuits when tailored contact block is absent"
    missing:
      - "Replace the `and` short-circuit with separate presence checks: if original_contact_m is not None, then check whether tailored_contact_m is None (warn: removed) or content differs (warn: modified)"
      - "Add a test: test_protected_sections_warns_when_contact_block_absent_from_tailored — passes a tailored string with no \\begin{center} block; asserts a warning is emitted"
---

# Phase 13: Guard Expansion Verification Report

**Phase Goal:** Add two new guards that catch technology substitution and protected-section mutations, and ship unit tests for both.
**Verified:** 2026-06-12T18:16:25Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

The truths below are merged from all three plan frontmatter `must_haves` sections and the ROADMAP.md success criteria.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `_check_technology_substitution` warns when technologies are substituted (removed AND added) | VERIFIED | `test_technology_substitution_warns_on_substitution` PASSES; implementation emits `f"Technology substitution in Skills: removed {sorted(removed)}, added {sorted(added)}"` |
| 2 | `_check_technology_substitution` warns when technologies are only removed | VERIFIED | `test_technology_substitution_warns_on_removal_only` PASSES; implementation hits `elif removed` branch |
| 3 | `_check_technology_substitution` warns when technologies are only added | VERIFIED | `test_technology_substitution_warns_on_addition_only` PASSES; implementation hits `elif added` branch |
| 4 | `_check_technology_substitution` is silent when Skills section is identical | VERIFIED | `test_technology_substitution_silent_for_identical` PASSES |
| 5 | `_check_technology_substitution` is silent when no Skills section exists in either text | VERIFIED | `test_technology_substitution_silent_for_no_skills_section` PASSES; early return when either section is None |
| 6 | `_check_technology_substitution` never raises on malformed (None) input | VERIFIED | `test_technology_substitution_malformed_input_no_raise` PASSES; `try/except Exception` wrapper on guards.py:58 |
| 7 | `_check_protected_sections` warns when the contact block **differs** between original and tailored | FAILED | Implementation (guards.py:82) uses `if original_contact_m is not None and tailored_contact_m is not None` — when LLM removes the contact block entirely, tailored_contact_m is None, condition is False, zero warnings emitted. Verified: `_check_protected_sections(original_with_contact, tailored_without_contact)` produces 0 warning calls. Content-modification case (both present, content differs) is correctly detected by the existing tests. |
| 8 | `_check_protected_sections` warns correctly for Education, Languages, employer headers, and project anchors | VERIFIED | Four tests (`*_education_diff`, `*_languages_diff`, `*_employer_header_change`, `*_silent_when_unchanged`) all PASS; implementation checks all four element types |
| 9 | `_check_protected_sections` never raises on empty string input | VERIFIED | `test_protected_sections_empty_strings_no_raise` PASSES |
| 10 | `run_guards()` calls both new guards; neither raises via run_guards() | VERIFIED | guards.py lines 112–113 contain both call sites; `test_run_guards_calls_technology_substitution` and `test_run_guards_new_guards_never_raise` both PASS; 14/14 unit tests pass |

**Score:** 9/10 truths verified (1 FAILED — BLOCKER)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/guards.py` | `def _check_technology_substitution` | VERIFIED | Line 57; substantive implementation with try/except wrapper |
| `src/guards.py` | `def _check_protected_sections` | VERIFIED | Line 77; substantive implementation; gap is in contact-block absent case only |
| `src/guards.py` | `def _extract_section` | VERIFIED | Line 46; module-private helper; reused by both new guards |
| `src/guards.py` | `run_guards()` calls both new guards | VERIFIED | Lines 112–113; correct argument order `(original_text, tailored_text)` |
| `tests/unit/test_guards.py` | 14 `@pytest.mark.unit` test functions | VERIFIED | All 14 exist and all 14 pass |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/unit/test_guards.py` | `src/guards.py` | `from guards import _check_technology_substitution, _check_protected_sections, run_guards` | VERIFIED | test_guards.py line 4 |
| `_check_technology_substitution` | `guards.logger` | `logger.warning()` | VERIFIED | guards.py lines 68, 70, 72 |
| `_check_protected_sections` | `guards.logger` | `logger.warning()` | VERIFIED | guards.py lines 84, 89, 93, 98, 103 |
| `_check_protected_sections` | `_extract_section` | module-private helper call | VERIFIED | guards.py lines 85–86, 90–91 |
| `_check_protected_sections` | `_EMPLOYER_PATTERN` | `_EMPLOYER_PATTERN.findall(original)` | VERIFIED | guards.py lines 95–96 |
| `run_guards()` | `_check_technology_substitution` | direct call | VERIFIED | guards.py line 112 |
| `run_guards()` | `_check_protected_sections` | direct call | VERIFIED | guards.py line 113 |

---

### Data-Flow Trace (Level 4)

Not applicable — guards.py contains no UI rendering or dynamic data display. All functions are pure text analysis that emit `logger.warning()` calls; no rendering or data display to trace.

---

### Behavioral Spot-Checks

All spot-checks were executed against the actual codebase.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 14 unit tests pass | `pytest -m unit tests/unit/test_guards.py -v` | 14 passed in 0.05s | PASS |
| 14 existing guards_test.py tests pass | `pytest src/guards_test.py -v` | 14 passed in 0.04s | PASS |
| `run_guards()` has 5 guard call sites | `grep -n "check_" guards.py` | Lines 109–113, all 5 guards present | PASS |
| Contact block absent from tailored: no warning | `_check_protected_sections(original_with_contact, tailored_without_contact)` | 0 warnings emitted | FAIL — CR-01 confirmed |

---

### Probe Execution

No `scripts/*/tests/probe-*.sh` files declared or found for this phase. Step skipped.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GARD-05 | 13-01 | `_check_technology_substitution` extracts Skills section and warns for substitution, removal-only, addition-only | SATISFIED | Function defined at guards.py:57; all 6 TEST-12 tests pass |
| GARD-06 | 13-02 | `_check_protected_sections` warns when contact block, education, languages, employer headers, or project anchors differ | BLOCKED (partial) | Function defined at guards.py:77; modification of contact block is detected, but complete removal of contact block produces no warning — the contact block check uses `and` where it should use a presence check first |
| GARD-07 | 13-03 | Both new guards called from `run_guards()` and never raise | SATISFIED | Lines 112–113 in guards.py; `test_run_guards_new_guards_never_raise` passes |
| TEST-12 | 13-01 | Unit tests cover `_check_technology_substitution`: 6 cases | SATISFIED | 6 tests, all pass |
| TEST-13 | 13-02 | Unit tests cover `_check_protected_sections`: 6 cases | PARTIAL | 6 tests all pass, but no test covers the "contact block entirely absent from tailored" failure mode that CR-01 exposes |

**Orphaned requirements check:** No additional Phase 13 requirements found in REQUIREMENTS.md beyond GARD-05, GARD-06, GARD-07, TEST-12, TEST-13. All 5 are accounted for.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/guards.py` | 82 | `if original_contact_m is not None and tailored_contact_m is not None` — both-not-None guard | BLOCKER | Contact block silently removed from tailored output without any warning; the worst-case LLM mutation (candidate name/contact info disappears) goes undetected |

No `TBD`, `FIXME`, `XXX`, `HACK`, `PLACEHOLDER` markers found in either modified file. No stub patterns (empty returns, hardcoded empty data) found.

---

### Human Verification Required

None. All behaviors are programmatically verifiable through tests and grep. No visual, real-time, or external service dependencies in this phase.

---

## Gaps Summary

**1 BLOCKER gap** prevents the phase goal from being fully achieved.

**Root cause:** `_check_protected_sections` correctly detects contact block content modifications (both blocks present, content differs) but does not detect complete removal of the contact block from the tailored output. The guard on guards.py:82 requires both regex matches to be non-None before comparing content; when the LLM removes `\begin{center}...\end{center}` entirely, the `tailored_contact_m is None` branch is silently skipped.

**Scope:** This is the only gap. All other GARD-06 checks (Education, Languages, employer headers, project anchors) correctly fire for both modification and removal, because Education and Languages are caught by `_check_missing_sections` when their `\header{}` marker disappears, and employer headers and project anchors use set-difference logic that naturally catches absence. Only the contact block check, which uses `\begin{center}` as its marker rather than `\header{}`, is vulnerable to this short-circuit.

**Fix scope:** One code change (3 lines in guards.py), one new test case in test_guards.py.

**Note — CR-01 severity assessment:** The code review correctly classified this as Critical. The contact block is the single most important protected element in the resume (it contains the candidate's name, email, phone, and profile URL). A guard that fires only when the block is modified but not when it is deleted provides false assurance. The GARD-06 requirement text ("warns when any of the following differ") and the roadmap success criterion ("warns correctly for each protected element type") both require detection of absence, not only modification.

---

_Verified: 2026-06-12T18:16:25Z_
_Verifier: Claude (gsd-verifier)_
