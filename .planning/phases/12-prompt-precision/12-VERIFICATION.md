---
phase: 12-prompt-precision
verified: 2026-06-13T00:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 4/4
  gaps_closed:
    - "UAT Test 1 gap: fabricated technologies — temperature=0.2 added, JD ANALYSIS USAGE rule added, inline fidelity reminders added, _check_fabricated_technologies guard wired from cli.py"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Run the CLI end-to-end against a real job description with Ollama running — same test as UAT Test 1 but with the three-layer defense now in place"
    expected: "No fabricated technologies appear in the tailored output; only skills actually in the base resume are surfaced; protected sections remain byte-identical; if the model does slip through, run_guards logs a warning naming the specific technology and the phrase 'possible fabrication'"
    why_human: "Requires a live Ollama LLM call; whether temperature=0.2 + the new JD ANALYSIS USAGE rule + the inline reminders collectively suppress fabrication cannot be verified by static inspection — the prior UAT found this to be intermittent, so at least one clean run is needed to confirm the defence closes the gap in practice"
---

# Phase 12: Prompt Precision Verification Report (Re-verification)

**Phase Goal:** Close UAT gap — eliminate fabricated technologies in tailored resume output through three-layer defense: temperature, prompt rules, and a deterministic post-generation guard
**Verified:** 2026-06-13
**Status:** human_needed
**Re-verification:** Yes — after gap closure (12-02-PLAN added temperature=0.2, JD ANALYSIS USAGE rule, inline fidelity reminders, and _check_fabricated_technologies guard)

## Goal Achievement

### Observable Truths

Truths 1-4 come from the roadmap success criteria and 12-01-PLAN must_haves (verified in the prior verification).
Truths 5-9 come from the 12-02-PLAN must_haves covering the UAT gap closure.

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | System prompt contains an `<ALLOWED>` section listing title line, employer taglines, employer bullets, project subtitle, project bullets, and skills content as the only rewritable elements | ✓ VERIFIED | Runtime probe: all six elements present inside `<ALLOWED>...</ALLOWED>` (src/llm_client.py:52-69); section closes with "Everything not listed above must remain byte-for-byte identical." — confirmed by test `test_build_messages_allowed_section_names_six_rewritable_elements` (38 passed) |
| 2  | System prompt contains a `<CONSTRAINTS>` section with a MUST NOT CHANGE list referencing concrete LaTeX inline patterns from the actual resume | ✓ VERIFIED | Runtime probe: MUST NOT CHANGE list at src/llm_client.py:72-87 with literal patterns `{\Huge \scshape {Name}}\\`, `\textbf{EMPLOYER}\textbf{ | ROLE} \hfill ...`, `\href{url}{\textbf{ProjectName}}`, `\header{Education}`, `\header{Languages}`, `\documentclass`, `\item` entries — confirmed by test `test_build_messages_constraints_name_protected_elements_by_latex_pattern` |
| 3  | System prompt contains a prominently labeled TECHNOLOGY FIDELITY rule inside `<CONSTRAINTS>` stating absent technologies must not appear and present technologies must not be removed | ✓ VERIFIED | "TECHNOLOGY FIDELITY:" label at src/llm_client.py:89; both directional rules plus Azure/AWS example confirmed by `test_build_messages_technology_fidelity_includes_azure_aws_example` |
| 4  | All pre-existing tests pass without modification | ✓ VERIFIED | Full suite: 125 passed, 3 skipped (Ollama-dependent integration/e2e, pre-existing) — `PYTHONPATH=... python3 -m pytest -x -q` |
| 5  | The tailoring request payload sets options.temperature to 0.2 | ✓ VERIFIED | src/llm_client.py:176: `"options": {"num_ctx": 8192, "temperature": 0.2}`; runtime mock probe returns `{'num_ctx': 8192, 'temperature': 0.2}`; confirmed by `test_generate_tailored_resume_payload_includes_temperature` |
| 6  | The system prompt explains the `<jd_analysis>` block as relevance-ranking signals only; absent technologies must never appear in output | ✓ VERIFIED | "JD ANALYSIS USAGE:" label at src/llm_client.py:96; phrases "relevance-ranking signals" (line 97) and "must never appear in the output" (line 101) both present inside `<CONSTRAINTS>` block; confirmed by `test_build_messages_constraints_contain_jd_analysis_usage_label` and `test_build_messages_constraints_jd_analysis_uses_relevance_ranking_signals` |
| 7  | Each rewritable ALLOWED element where fabrication occurred (taglines, employer bullets, project subtitle, project bullets) carries an inline technology-fidelity reminder | ✓ VERIFIED | Runtime probe: "(mention only technologies already present in the original resume)" appears exactly 4 times inside `<ALLOWED>...</ALLOWED>` block; confirmed by `test_build_messages_allowed_inline_fidelity_reminder_appears_at_least_four_times` |
| 8  | run_guards logs a warning naming any JD-analysis technology that appears in the tailored output but not in the base resume | ✓ VERIFIED | `_check_fabricated_technologies()` at src/guards.py:47-63 uses token-boundary case-insensitive regex with `re.escape`; behavioral spot-check: Kubernetes absent from original but in tailored fires warning containing "Kubernetes" and "possible fabrication"; case-insensitive ("kubernetes" matches "Kubernetes" in jd list); token-bounded ("Java" in jd list does NOT warn when only "JavaScript" appears in tailored); single-char tokens skipped; malformed input (`[None, 123, "C"]`) never raises |
| 9  | cli.py passes analysis technologies into run_guards; all pre-existing tests pass unmodified (the only permitted change to a pre-existing test was NOT made, replaced by dict-unpacking deviation) | ✓ VERIFIED | src/cli.py:57-58: `run_guards(resume_text, result.content, result.fences_stripped, **{"jd_technologies": analysis["technologies"]} if analysis else {})`; `grep -c 'jd_technologies' src/cli.py` = 1; `pytest src/cli_test.py -x -q` = 12 passed; deviation from plan action (conditional dict-unpacking instead of explicit `None`) is strictly behavior-preserving |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/llm_client.py` | `_build_messages()` with `<ALLOWED>` section and TECHNOLOGY FIDELITY rule | ✓ VERIFIED | Exists; 214 lines; system prompt has ALLOWED (lines 52-69), MUST NOT CHANGE (72-87), TECHNOLOGY FIDELITY (89-94), JD ANALYSIS USAGE (96-101); payload includes temperature=0.2 at line 176; no stubs, no debt markers |
| `src/guards.py` | `_check_fabricated_technologies` function | ✓ VERIFIED | Exists; 71 lines; `_check_fabricated_technologies` at line 47 (definition) and line 70 (called from `run_guards`); grep count 2 matches plan requirement; try/except wrapper, re.escape, len < 2 skip, lookaround boundaries all present |
| `src/cli.py` | `run_guards` call wired with `jd_technologies` | ✓ VERIFIED | Exists; line 57-58 passes `jd_technologies` conditionally via dict-unpacking when analysis is not None |
| `src/guards_test.py` | Unit coverage for fabrication guard | ✓ VERIFIED | `TestCheckFabricatedTechnologies` class at line 116 with 8 test methods; `TestRunGuardsNeverRaises` extended with malformed jd_technologies case at line 113; `grep -c 'fabricat'` = 8 |
| `tests/unit/test_llm_client.py` | Tests for payload temperature, JD ANALYSIS USAGE rule, relevance-ranking phrases, inline reminder count | ✓ VERIFIED | 4 new tests added: lines 302-316 (temperature), 319-321 (JD ANALYSIS USAGE label), 323-328 (relevance-ranking phrases), 331-337 (inline reminder count >= 4); 38 tests total pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/llm_client.py _build_messages()` | `tests/unit/test_llm_client.py::test_build_messages_system_contains_constraints_tag` | `<CONSTRAINTS>`/`</CONSTRAINTS>` tag literals | ✓ WIRED | Test asserts both literals in `result[0]["content"]`; passes |
| `src/cli.py run_guards call` | `src/guards.py run_guards(jd_technologies=...)` | `jd_technologies` keyword argument carrying `analysis["technologies"]` | ✓ WIRED | Line 57-58 in cli.py passes `**{"jd_technologies": analysis["technologies"]} if analysis else {}`; when analysis is not None the kwarg is present; run_guards signature at guards.py:66 accepts `jd_technologies: list \| None = None` |
| `src/guards.py _check_fabricated_technologies` | `log_manager logger` | `logger.warning` on fabricated technology token | ✓ WIRED | Line 59-61: `logger.warning(f'Technology "{tech}" appears in tailored output but not in base resume — possible fabrication.')`; behavioral spot-check confirms the warning fires with correct content |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `src/llm_client.py` | `system_prompt` → `messages[0]["content"]` | Raw string literal (r-prefix), `.strip()` applied | Yes — runtime import of `_build_messages()` returns full rendered prompt with literal backslash sequences intact; temperature=0.2 in payload dict confirmed by mock probe | ✓ FLOWING |
| `src/guards.py` | `jd_technologies` → `_check_fabricated_technologies` | Passed from `run_guards()` caller (cli.py) | Yes — guard receives the actual list from `analysis["technologies"]`; behavioral spot-check confirms it fires a real warning on synthetic fabrication input | ✓ FLOWING |
| `src/cli.py` | `analysis["technologies"]` → `run_guards` kwarg | `analyze_job_description()` return value | Yes — data flows through: `analysis = analyze_job_description(...)` → `**{"jd_technologies": analysis["technologies"]} if analysis else {}` → `run_guards(...)`; `cli_test.py` mock confirms 12 tests pass covering this path | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green | `python3 -m pytest -x -q` | 125 passed, 3 skipped | ✓ PASS |
| temperature=0.2 in payload options | Python mock probe on `generate_tailored_resume` | `{'num_ctx': 8192, 'temperature': 0.2}` | ✓ PASS |
| `<ALLOWED>` section has all 6 elements + byte-for-byte closer + 4 inline reminders | Python runtime probe on `_build_messages()` | All 6 elements: True; closer: True; reminder count: 4 | ✓ PASS |
| `<CONSTRAINTS>` has MUST NOT CHANGE + TECHNOLOGY FIDELITY + JD ANALYSIS USAGE + relevance-ranking phrases | Python runtime probe | All: True | ✓ PASS |
| Kubernetes fabrication triggers warning | Behavioral spot-check with patched logger | "Kubernetes" + "possible fabrication" in warning call | ✓ PASS |
| Case-insensitive matching ("kubernetes" matches "Kubernetes") | Behavioral spot-check | Warning fires | ✓ PASS |
| Token-boundary matching ("Java" does NOT match "JavaScript") | Behavioral spot-check | No warning fired | ✓ PASS |
| Single-char technology name ("C") is skipped | Behavioral spot-check | No warning fired | ✓ PASS |
| Malformed jd_technologies (`[None, 123, "C"]`) never raises | Behavioral spot-check | No exception raised | ✓ PASS |
| No `<INSTRUCTIONS>` legacy tag in prompt | `grep -c '<INSTRUCTIONS>' src/llm_client.py` | 0 | ✓ PASS |
| `_check_fabricated_technologies` appears twice in guards.py | `grep -c '_check_fabricated_technologies' src/guards.py` | 2 | ✓ PASS |
| No debt markers in modified files | grep for TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER | No matches | ✓ PASS |
| Live CLI run with Ollama | — | Ollama not available in this environment | ? SKIP → human verification |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist in the repository. Not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PRMP-01 | 12-01 | `_build_messages()` system prompt defines an explicit ALLOWED list: title line, employer taglines, employer bullets, project subtitle and bullets, skills reordering/reweighting | ✓ SATISFIED | All six elements verified inside `<ALLOWED>` section (src/llm_client.py:52-69); REQUIREMENTS.md marks `[x]` |
| PRMP-02 | 12-01 | `_build_messages()` system prompt defines an explicit MUST-NOT-CHANGE list: candidate name, contact block, education section, languages section, employer header lines, project name/URL/date, all LaTeX structural commands | ✓ SATISFIED | All required items verified in MUST NOT CHANGE list (src/llm_client.py:72-87) with actual inline LaTeX patterns; REQUIREMENTS.md marks `[x]` |
| PRMP-03 | 12-01, 12-02 | System prompt includes anti-fabrication rule: no technology substitution; Azure-present-must-remain / AWS-absent-must-not-appear; plus (from 12-02 extension) temperature=0.2, JD ANALYSIS USAGE rule, inline reminders, deterministic guard | ✓ SATISFIED | TECHNOLOGY FIDELITY rule + Azure/AWS example (lines 89-94); JD ANALYSIS USAGE rule (lines 96-101); inline reminders x4 in ALLOWED; `_check_fabricated_technologies` guard (guards.py:47-63); REQUIREMENTS.md marks `[x]` |

No orphaned requirements: REQUIREMENTS.md maps exactly PRMP-01/02/03 to Phase 12 (all marked complete); no other requirement IDs reference Phase 12 in the traceability table. GARD-05/06/07 are mapped to Phase 13 and are not in scope here.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| All modified files | — | Debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER) | ℹ️ None found | grep clean across llm_client.py, guards.py, cli.py, guards_test.py, tests/unit/test_llm_client.py |
| `src/llm_client.py` | 72-75 (MUST NOT CHANGE contact block) vs 54 (ALLOWED title line) | CR-01 from prior verification: ALLOWED grants title-line rewrite; CONSTRAINTS text says "entire" contact block is protected then carves out the exception | ⚠️ Warning (pre-existing, not introduced by 12-02) | Contradiction inherited from PRMP-01/PRMP-02 requirement wording; present since 12-01; UAT Test 2 passed despite this (model obeys the ALLOWED carve-out); not a blocker |

### Human Verification Required

### 1. Live end-to-end run confirming three-layer defense closes UAT Test 1 gap

**Test:** With Ollama running, execute the CLI against the same (or similar) job description that triggered the fabrication issue in UAT Test 1. Compare tailored output against the original resume — specifically check whether any technology absent from the base resume appears in the output.

**Expected:** No fabricated technologies appear. Protected sections remain byte-identical. If the model does slip through, a `WARNING` log entry appears naming the specific technology and containing the phrase "possible fabrication".

**Why human:** Requires a live LLM call against a running Ollama instance. The prior UAT failure was described as "sometimes" (intermittent), so a single clean run gives reasonable confidence rather than proof. The deterministic guard layer ensures any slip is now auditable via named warning instead of silent pass-through. Static analysis cannot substitute for behavioral confirmation.

### Gaps Summary

No gaps against the roadmap contract or either plan's must-haves. All 9 must-have truths are verified in the codebase:

- ROADMAP success criteria 1-4 (ALLOWED list, MUST NOT CHANGE list, anti-fabrication rule, tests green): all verified.
- 12-02-PLAN must-haves (temperature=0.2, JD ANALYSIS USAGE rule, inline reminders x4, fabrication guard with named warning, cli.py wiring): all verified.
- 125 tests pass, 3 skipped (pre-existing Ollama-dependent).
- No debt markers in any modified file.

One human verification item remains: a live UAT re-run to confirm the three-layer defense closes the fabrication gap in practice. This was the original UAT Test 1 gap that triggered 12-02-PLAN; all four missing items from the UAT Gaps section have now been implemented and verified deterministically. The human test is the behavioral confirmation that the probabilistic layer (temperature + prompt) and the deterministic layer (guard) collectively suppress fabrication in a real run.

---

_Verified: 2026-06-13_
_Verifier: Claude (gsd-verifier)_
