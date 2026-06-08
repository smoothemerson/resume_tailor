# Phase 4: Output Reliability Guards - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 4-Output Reliability Guards
**Areas discussed:** Guard architecture, GUARD-02 vs existing validation, GUARD-03 field extraction scope, Warning message format

---

## Guard Architecture

### Q1: Where should guard logic live?

| Option | Description | Selected |
|--------|-------------|----------|
| New guards.py module | guards.py exports run_guards(); called from cli.py. Matches raise-not-exit pattern; easiest to test in isolation. | ✓ |
| Inside llm_client.py | Guard functions inside generate_tailored_resume(); prints to stderr internally. Fewer files but mixes HTTP logic with guard logic. | |
| You decide | Let the planner choose. | |

**User's choice:** New guards.py module

### Q2: When should run_guards() be called relative to write_resume()?

| Option | Description | Selected |
|--------|-------------|----------|
| Before write_resume() | Guards run on content first, then file is written regardless of warnings. Natural check-before-save UX. | ✓ |
| After write_resume() | File written first, then warnings printed. Slightly odd — file is on disk when warned about issues. | |
| You decide | Let the planner choose. | |

**User's choice:** Before write_resume()

---

## GUARD-02 vs Existing Validation

### Q1: How should GUARD-02 relate to existing _validate_latex?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep hard errors, GUARD-02 adds soft checks | _validate_latex stays as-is (blocking). GUARD-02 adds separate non-blocking checks. | ✓ |
| GUARD-02 replaces _validate_latex | Convert hard errors to warnings. Riskier: writing unusable .tex silently is worse than a clear error. | |
| GUARD-02 warns only when _strip_fences modified text | Simplest: fire only when fences were detected and stripped. | |

**User's choice:** Keep hard errors, GUARD-02 adds soft checks

### Q2: What should GUARD-02 check specifically?

| Option | Description | Selected |
|--------|-------------|----------|
| Stripped fences warning | Warn if _strip_fences() modified the text — model ignored LaTeX-only instruction. | ✓ |
| Inline markdown in body | Warn if tailored content contains ``` fences, ## headers, or **bold** markers inside the document. | ✓ |
| Prose before \documentclass | Warn when non-LaTeX text appears before \documentclass (already caught by _validate_latex as hard error). | |

**User's choice:** Both — stripped fences warning AND inline markdown in body

---

## GUARD-03 Field Extraction Scope

### Q1: How should GUARD-03 extract fields to compare?

| Option | Description | Selected |
|--------|-------------|----------|
| \employer{} regex only | Extract names and dates from \employer{name}{dates}{title} in original. Accurate for this template, easy to implement. | ✓ |
| Broad token-diff | Compare any new capitalized multi-word phrase in tailored vs original. Higher false-positive rate. | |
| You decide | Let the planner choose extraction strategy. | |

**User's choice:** \employer{} regex only

### Q2: Should GUARD-03 also check education entries?

| Option | Description | Selected |
|--------|-------------|----------|
| Employer only | Check \employer{} entries only. Education (fixed, well-known institutions) rarely hallucinated. | ✓ |
| Employer + education | Also check \schoolwithcourses{} and \school{} institution names. | |

**User's choice:** Employer only

---

## Warning Message Format

### Q1: How should guard warnings be formatted?

| Option | Description | Selected |
|--------|-------------|----------|
| Plain WARNING: prefix | e.g. 'WARNING: Section "Skills" missing from tailored output.' Consistent with existing Error: prefix. | ✓ |
| Guard ID prefix | e.g. '[GUARD-01] Missing section: Skills'. Traceable to requirements but technical. | |
| You decide | Let planner choose a format consistent with existing stderr style. | |

**User's choice:** Plain WARNING: prefix

### Q2: When multiple guards fire, how should warnings be grouped?

| Option | Description | Selected |
|--------|-------------|----------|
| Inline as each guard fires | Each guard prints immediately when it detects an issue. Simple, no buffering. | ✓ |
| Collect then print as a block | run_guards() collects all warnings, prints them as a block. Cleaner grouping but adds buffer. | |

**User's choice:** Inline as each guard fires

---

## Claude's Discretion

None — user made explicit choices in all areas.

## Deferred Ideas

None — discussion stayed within phase scope.
