---
phase: 12-prompt-precision
verified: 2026-06-11T00:00:00Z
status: human_needed
score: 4/4 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run the CLI end-to-end against a real job description with Ollama running; diff the tailored output against the original resume"
    expected: "Contact block, Education, Languages, employer header lines, project anchors, and section headers are byte-identical; only the six ALLOWED elements differ; no technologies added that are absent from the original"
    why_human: "Requires a live Ollama LLM call; whether the model obeys the prompt cannot be verified by static inspection"
  - test: "During the same run, observe whether the model rewrites the title line and project subtitles/bullets despite the prompt's internal contradictions (REVIEW CR-01: ALLOWED title line vs 'entire' contact-block protection; CR-02: stale OUTPUT_FORMAT scope list naming 'professional summary, skills, and experience bullets only')"
    expected: "Model rewrites the title line and project content per <ALLOWED> and does not invent a 'professional summary' section or edit name/email/phone/links"
    why_human: "Which of two contradictory scope instructions an LLM obeys is a behavioral judgment, not a grep-verifiable property"
---

# Phase 12: Prompt Precision Verification Report

**Phase Goal:** Replace INSTRUCTIONS + CONSTRAINTS in `_build_messages()` with explicit ALLOWED/PROTECTED rules matching actual resume LaTeX patterns.
**Verified:** 2026-06-11
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | System prompt contains an `<ALLOWED>` section listing title line, employer taglines, employer bullets, project subtitle, project bullets, and skills content as the only rewritable elements | ✓ VERIFIED | Runtime probe of rendered prompt: all six elements present inside `<ALLOWED>...</ALLOWED>` (src/llm_client.py:52-65); section opens with "You may ONLY rewrite" and closes with "Everything not listed above must remain byte-for-byte identical." |
| 2   | System prompt contains a `<CONSTRAINTS>` section with a MUST NOT CHANGE list referencing concrete LaTeX inline patterns from the actual resume | ✓ VERIFIED | Runtime probe: all nine protected items present inside `<CONSTRAINTS>` (src/llm_client.py:67-88) with literal inline patterns `{\Huge \scshape {Name}}\\`, `\textbf{EMPLOYER}\textbf{ | ROLE} \hfill ...`, `\href{url}{\textbf{ProjectName}}`, `\header{Education}`, `\header{Languages}`; forbidden `\employer{` macro signature absent (grep count 0) |
| 3   | System prompt contains a prominently labeled TECHNOLOGY FIDELITY rule inside `<CONSTRAINTS>` stating that absent technologies must not appear and present technologies must not be removed | ✓ VERIFIED | Runtime probe: "TECHNOLOGY FIDELITY" label index falls between `<CONSTRAINTS>` and `</CONSTRAINTS>` indices; both directional rules present plus the Azure/AWS example (src/llm_client.py:82-87) |
| 4   | All existing tests pass without modification | ✓ VERIFIED | `PYTHONPATH=... python3 -m pytest -q` — 104 passed, 3 skipped in 0.27s (skips are pre-existing Ollama-dependent integration/e2e tests); test files untouched by commit f6a4e13 (diff stat: src/llm_client.py only) |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/llm_client.py` | `_build_messages()` with rewritten system_prompt containing `<ALLOWED>` | ✓ VERIFIED | Exists; substantive (75-line prompt rewrite, no stub patterns, no debt markers); wired — `_build_messages` called by `generate_tailored_resume` (src/llm_client.py:157) and exercised by 26 unit tests |
| `src/llm_client.py` | system_prompt containing "TECHNOLOGY FIDELITY" | ✓ VERIFIED | grep count 1; runtime probe confirms it renders in the message content sent to Ollama |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `src/llm_client.py _build_messages()` | `tests/unit/test_llm_client.py::test_build_messages_system_contains_constraints_tag` | `<CONSTRAINTS>`/`</CONSTRAINTS>` tag literals | ✓ WIRED | Test (tests/unit/test_llm_client.py:35-38) asserts both literals in `result[0]["content"]`; test passes |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `src/llm_client.py` | `system_prompt` → `messages[0]["content"]` | Raw string literal, `.strip()` applied | Yes — runtime import of `_build_messages()` returned the full rendered prompt with literal backslash sequences (`\usepackage`, `\textit{\small`, `{\Huge \scshape {Name}}\\`) intact; no escape corruption (no tab/backspace/vtab control chars) | ✓ FLOWING |
| `src/llm_client.py` | `messages` → Ollama payload | `generate_tailored_resume()` posts `messages` to `/api/chat` (src/llm_client.py:157-170) | Yes — payload assembly unchanged, covered by passing mock-based tests | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Section order PERSONA→TASK→CONTEXT→ALLOWED→CONSTRAINTS→OUTPUT_FORMAT (D-06) | python3 runtime probe on `_build_messages()` | order indices strictly increasing | ✓ PASS |
| TECHNOLOGY FIDELITY positioned inside `<CONSTRAINTS>` block | python3 runtime probe | index between open/close tags | ✓ PASS |
| Old `<INSTRUCTIONS>` tag removed; `\employer{` macro signature absent | grep counts | both 0 | ✓ PASS |
| Full test suite | `python3 -m pytest -q` | 104 passed, 3 skipped | ✓ PASS |
| Live tailoring run | — | Ollama not available in this environment | ? SKIP → routed to human verification |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist in the repository and none are declared in PLAN or SUMMARY. Not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| PRMP-01 | 12-01 | Explicit ALLOWED list: title line, employer taglines, employer bullets, project subtitle and bullets, skills reordering/reweighting | ✓ SATISFIED | All six elements verified in `<ALLOWED>` section (src/llm_client.py:52-65) |
| PRMP-02 | 12-01 | Explicit MUST-NOT-CHANGE list: candidate name, contact block, education, languages, employer header lines, project name/URL/date, all LaTeX structural commands | ✓ SATISFIED | All required items (plus section headers and bullet count) verified in MUST NOT CHANGE list (src/llm_client.py:68-80); project name/URL/date covered by "Project anchors: the \href{url}{\textbf{ProjectName}} and \hfill date" |
| PRMP-03 | 12-01 | Anti-fabrication rule: no technology substitution; Azure-present-must-remain / AWS-absent-must-not-appear | ✓ SATISFIED | TECHNOLOGY FIDELITY rule with both directional clauses and the exact Azure/AWS example (src/llm_client.py:82-87) |

No orphaned requirements: REQUIREMENTS.md maps exactly PRMP-01/02/03 to Phase 12, and the single plan claims all three.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| src/llm_client.py | 54 vs 70-71 | Internal prompt contradiction (REVIEW CR-01): ALLOWED grants title-line rewrite; CONSTRAINTS protects the "entire" contact block that contains it | ⚠️ Warning | Both instructions were mandated verbatim by the plan action text (and the contradiction is inherited from PRMP-01/PRMP-02 wording); roadmap success criteria are still met literally, but model behavior at this conflict is unverifiable statically — routed to human verification |
| src/llm_client.py | 93 | Internal prompt contradiction (REVIEW CR-02): OUTPUT_FORMAT retains stale scope list "professional summary, skills, and experience bullets only", conflicting with the six-element ALLOWED list | ⚠️ Warning | Plan explicitly instructed copying OUTPUT_FORMAT verbatim, so the executor followed the plan; the defect lives in the shipped prompt and undermines the phase's precision intent — recommend a follow-up fix per REVIEW.md CR-02 |
| src/llm_client.py | — | Debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER) | ℹ️ None found | grep clean |

### Human Verification Required

### 1. End-to-end tailoring run preserves protected sections

**Test:** With Ollama running, execute the CLI against a real job description and diff the tailored `.tex` against the original resume.
**Expected:** Contact block, Education, Languages, employer header lines, project anchors, and section headers are byte-identical; only the six ALLOWED elements differ; no technologies appear that are absent from the original resume.
**Why human:** Requires a live LLM call; prompt compliance is model behavior, not a static property.

### 2. Prompt contradictions do not derail model scope

**Test:** In the same run, check whether the model rewrites the title line and project subtitles/bullets (per ALLOWED) despite CR-01 ("entire" contact-block protection) and CR-02 (stale OUTPUT_FORMAT "only" list).
**Expected:** Title line and project content are rewritten; no "professional summary" section is invented; name/email/phone/links untouched.
**Why human:** Which of two contradictory instructions an LLM follows is a behavioral judgment.

### Gaps Summary

No gaps against the roadmap contract. All four roadmap success criteria and all four PLAN must-have truths are verified in the codebase: the `<INSTRUCTIONS>` block is gone, the `<ALLOWED>` whitelist names the six rewritable elements with concrete LaTeX patterns, the `<CONSTRAINTS>` block carries the nine-item MUST NOT CHANGE list using the resume's actual inline patterns, the TECHNOLOGY FIDELITY rule with the Azure/AWS example sits inside `<CONSTRAINTS>`, and the full test suite passes (104 passed, 3 pre-existing Ollama-dependent skips) with no test modifications. The raw-string conversion deviation (SUMMARY auto-fix 1) was confirmed correct at runtime — backslash sequences render literally with no escape corruption.

Two advisory code-review findings (CR-01, CR-02 in 12-REVIEW.md) are real internal contradictions in the shipped prompt but were mandated by the plan text itself (and CR-01 traces back to the PRMP-01/PRMP-02 requirement wording). They do not falsify any success criterion; their behavioral impact is the subject of the human verification items above and should be addressed as follow-up prompt fixes.

---

_Verified: 2026-06-11_
_Verifier: Claude (gsd-verifier)_
