---
phase: 06-two-pass-pipeline
verified: 2026-06-07T18:00:00Z
status: human_needed
score: 8/8 must-haves verified
overrides_applied: 0
re_verification: false
human_verification:
  - test: "Run a live smoke test with Ollama running: echo -e 'Senior ML Engineer\nPython, PyTorch, distributed training, MLOps\nEND' | uv run python -m resume_tailor.cli"
    expected: "Output shows 'Analyzing job description...' then 'Tailoring resume — this may take a minute...' then 'Tailored resume written to: /path/to/tailored_resume_YYYYMMDD_HHMMSS.tex'"
    why_human: "Two-pass LLM call order and analysis injection into the tailoring prompt can only be confirmed by observing a real Ollama run — unit tests mock both calls"
  - test: "On a machine where Ollama is unreachable, run the CLI with a valid JD. Confirm 'Analyzing job description...' prints before the error message."
    expected: "Output: 'Analyzing job description...\\nError: Ollama is not reachable at http://localhost:11434' — tool exits 1 cleanly"
    why_human: "Error message wording and ordering of the progress print + error output requires a real Ollama-absent environment"
---

# Phase 06: Two-Pass Pipeline Verification Report

**Phase Goal:** Implement a two-pass pipeline where pass 1 analyzes the job description via Ollama (producing a structured JSON dict with technologies/requirements/emphasis_areas) and pass 2 injects the analysis into the tailoring prompt. The pipeline must fall back gracefully to single-pass behavior when analysis fails.
**Verified:** 2026-06-07T18:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Providing a JD results in the tool making two LLM calls — one analysis call and one tailoring call — visible via progress messages | VERIFIED | `src/cli.py` line 48 prints "Analyzing job description..." before `analyze_job_description()` call (line 51); line 53 prints "Tailoring resume..." before `generate_tailored_resume()` call (line 54). Both calls confirmed by `test_analyzing_progress_message_printed` passing. |
| 2  | The tailoring call's prompt contains the extracted JD requirements from the analysis call | VERIFIED | `_build_messages` in `src/llm_client.py` lines 105–113 conditionally prepends `<jd_analysis>` XML block with technologies, requirements, emphasis_areas when `analysis is not None`. `generate_tailored_resume` passes `analysis` through to `_build_messages` (line 147). `test_build_messages_with_analysis_includes_jd_analysis_tag` passes. |
| 3  | When the analysis call produces malformed or unparseable output, the tool falls back silently to single-pass behavior and still produces a tailored resume | VERIFIED | `analyze_job_description` in `src/jd_analyzer.py` returns `None` on JSON parse failure, missing keys, and connection errors (lines 34–38, 64). `_build_messages` with `analysis=None` omits the `<jd_analysis>` block (confirmed by `test_build_messages_without_analysis_omits_jd_analysis_tag` passing). `test_generate_called_with_analysis_none_when_analysis_fails` confirms `generate_tailored_resume` receives `analysis=None`. |
| 4  | Both LLM calls are protected by the existing truncation guard — a `done_reason: length` response on either call triggers the same error path as today | VERIFIED | `jd_analyzer.py` lines 58–59 raise `RuntimeError` on `done_reason=length`; `except RuntimeError: raise` at line 62 propagates it. `generate_tailored_resume` in `llm_client.py` lines 176–180 raise `RuntimeError` on `done_reason=length`. `test_analyze_job_description_raises_runtime_error_on_truncation` and `test_generate_tailored_resume_truncated_raises` both pass. |

**Score:** 8/8 truths verified (roadmap truths + plan must-have truths all covered)

### PLAN Must-Have Truths Cross-Check

| Plan | Truth | Status | Evidence |
|------|-------|--------|----------|
| 06-01 | `pytest -m unit tests/unit/test_jd_analyzer.py -x` exits 0 | VERIFIED | 6 passed in test run |
| 06-01 | `_build_messages` with analysis=non-None produces user content containing `<jd_analysis>` tag | VERIFIED | `test_build_messages_with_analysis_includes_jd_analysis_tag` passes |
| 06-01 | `_build_messages` with analysis=None produces user content with no `<jd_analysis>` tag | VERIFIED | `test_build_messages_without_analysis_omits_jd_analysis_tag` passes |
| 06-01 | `analyze_job_description` returns None on JSON parse failure (not raises) | VERIFIED | `jd_analyzer.py` line 35 (`except Exception: return None`) + test passes |
| 06-01 | `analyze_job_description` raises RuntimeError on done_reason=length (not returns None) | VERIFIED | `jd_analyzer.py` lines 58–63 + test passes |
| 06-03 | `analyze_job_description('some jd')` returns dict with keys technologies, requirements, emphasis_areas | VERIFIED | `jd_analyzer.py` lines 42–65; test confirms dict return |
| 06-03 | Returns None on connection error, HTTP error, JSON parse failure, or missing required keys | VERIFIED | `except Exception: return None` at line 64; 4 tests cover each case |
| 06-03 | Raises RuntimeError (not returns None) when done_reason=length | VERIFIED | Lines 58–63; `except RuntimeError: raise` before catch-all |
| 06-03 | Does NOT call `_check_ollama_health` | VERIFIED | `grep _check_ollama_health src/jd_analyzer.py` returns no matches |
| 06-03 | Fence-wrapped JSON from LLM is stripped and parsed correctly | VERIFIED | `_parse_analysis_response` lines 29–31 apply `re.sub` fence stripping; `test_analyze_job_description_returns_none_on_fence_wrapped_valid_json` (misleadingly named but asserts `result is dict`) passes |
| 06-04 | `_build_messages` with analysis=non-None returns user message containing `<jd_analysis>` block | VERIFIED | `llm_client.py` lines 105–113 |
| 06-04 | `_build_messages` without analysis returns user message with no `<jd_analysis>` tag | VERIFIED | Conditional block only executes when `analysis is not None` |
| 06-04 | `generate_tailored_resume` accepts analysis keyword argument with default None | VERIFIED | Signature at line 142: `analysis: dict | None = None` |
| 06-04 | All existing llm_client unit tests continue to pass | VERIFIED | 26/26 tests pass |
| 06-05 | "Analyzing job description..." is printed with flush=True before the analysis call | VERIFIED | `cli.py` line 48; the `try` block begins at line 50 |
| 06-05 | "Tailoring resume — this may take a minute..." is printed with flush=True before the tailoring call | VERIFIED | `cli.py` line 53 |
| 06-05 | `generate_tailored_resume` is called with `analysis=<result of analyze_job_description>` | VERIFIED | `cli.py` line 54: `generate_tailored_resume(..., analysis=analysis, ...)` |
| 06-05 | When `analyze_job_description` returns None, `generate_tailored_resume` is called with `analysis=None` | VERIFIED | `test_generate_called_with_analysis_none_when_analysis_fails` passes |
| 06-05 | All 11 tests in `src/cli_test.py` pass after wiring | VERIFIED | 11/11 pass |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/jd_analyzer.py` | `analyze_job_description(job_description, model=None) -> dict \| None` with `_build_analysis_messages` and `_parse_analysis_response` | VERIFIED | File exists, 66 lines, all 3 functions present, no health check call |
| `tests/unit/test_jd_analyzer.py` | 6 unit tests covering success, fallback, truncation, fence-stripping | VERIFIED | File exists, 88 lines, 6 `@pytest.mark.unit` tests |
| `tests/unit/test_llm_client.py` | 2 new `_build_messages` analysis tests appended | VERIFIED | Both `test_build_messages_with_analysis_includes_jd_analysis_tag` and `test_build_messages_without_analysis_omits_jd_analysis_tag` present at lines 221–230 |
| `src/llm_client.py` | `_build_messages` and `generate_tailored_resume` extended with `analysis: dict \| None = None` | VERIFIED | 2 matches for `analysis: dict \| None = None`; `jd_analysis` injection block present; `_build_messages` call updated |
| `src/cli.py` | Two-pass orchestration with `from jd_analyzer import analyze_job_description` | VERIFIED | Import at line 8; two-pass flow at lines 48–61 |
| `src/cli_test.py` | 8 existing tests patched + 3 new two-pass tests (11 total) | VERIFIED | 11 `def test_` functions; 11 `cli.analyze_job_description` patch occurrences |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/unit/test_jd_analyzer.py` | `src/jd_analyzer.py` | `from jd_analyzer import analyze_job_description` | WIRED | Import at line 5 of test file; all 6 tests call `analyze_job_description` |
| `tests/unit/test_llm_client.py` | `src/llm_client.py` | `_build_messages` called with 3 args | WIRED | `_build_messages("r", "jd", {...})` at line 222; `_build_messages("r", "jd")` at line 229 |
| `src/cli_test.py` | `src/cli.py` | `@patch('cli.analyze_job_description', return_value=None)` | WIRED | 11 occurrences of `cli.analyze_job_description` patch |
| `src/jd_analyzer.py` | `src/config.py` | `from config import OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT` | WIRED | Line 6 of `jd_analyzer.py` |
| `src/jd_analyzer.py` | `http://localhost:11434/api/chat` | `requests.post(f"{OLLAMA_BASE_URL}/api/chat")` | WIRED | Line 51–55 of `jd_analyzer.py` |
| `_build_messages` | user_message | `<jd_analysis>` block prepended when `analysis is not None` | WIRED | Lines 105–113 of `llm_client.py` |
| `generate_tailored_resume` | `_build_messages` | passes analysis argument through | WIRED | Line 147: `messages = _build_messages(resume_text, job_description, analysis)` |
| `src/cli.py` | `src/jd_analyzer.py` | `from jd_analyzer import analyze_job_description` | WIRED | Line 8 of `cli.py` |
| `src/cli.py` | `src/llm_client.py` | `generate_tailored_resume(..., analysis=analysis, ...)` | WIRED | Line 54 of `cli.py` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `cli.py` — analysis injection | `analysis` | `analyze_job_description(job_description, model=args.model)` returns dict or None based on real Ollama response | Yes (dict from `_parse_analysis_response` on real LLM output, or None on failure) | FLOWING |
| `llm_client.py` — `_build_messages` | `analysis_block` | `analysis['technologies']`, `analysis['requirements']`, `analysis['emphasis_areas']` from validated dict | Yes (only whitelisted keys extracted by `_parse_analysis_response`) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 6 jd_analyzer tests pass | `uv run pytest tests/unit/test_jd_analyzer.py -m unit -v` | 6 passed | PASS |
| 26 llm_client tests pass (24 pre-existing + 2 new) | `uv run pytest tests/unit/test_llm_client.py -m unit -v` | 26 passed | PASS |
| 11 cli_test.py tests pass | `uv run pytest src/cli_test.py -v` | 11 passed | PASS |
| Full suite green | `uv run pytest --tb=short -q` | 89 passed, 2 skipped (Ollama integration, expected) | PASS |
| analyze_job_description returns None on ConnectionError | `test_analyze_job_description_returns_none_on_connection_error` | PASS | PASS |
| analyze_job_description raises RuntimeError on truncation | `test_analyze_job_description_raises_runtime_error_on_truncation` | PASS | PASS |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| PIPE-01 | 06-01, 06-02, 06-03, 06-05 | Tool performs a JD analysis pass (pass 1) before the tailoring call | SATISFIED | `jd_analyzer.py` exists with `analyze_job_description`; called in `cli.py` line 51 before `generate_tailored_resume` at line 54 |
| PIPE-02 | 06-01, 06-04, 06-05 | Analysis output is injected into the tailoring prompt (pass 2) | SATISFIED | `_build_messages` in `llm_client.py` injects `<jd_analysis>` XML block when `analysis is not None`; `cli.py` forwards `analysis=analysis` to `generate_tailored_resume` |
| PIPE-03 | 06-01, 06-02, 06-03, 06-05 | If pass 1 fails, tool falls back to single-pass behavior — no abort | SATISFIED | `analyze_job_description` returns `None` on all non-truncation failures; `_build_messages` with `None` omits `<jd_analysis>`; pipeline continues normally |
| PIPE-04 | 06-01, 06-03, 06-04 | Both LLM calls respect existing done_reason truncation guard | SATISFIED | `jd_analyzer.py` raises `RuntimeError` on `done_reason=length`; `generate_tailored_resume` in `llm_client.py` raises `RuntimeError` on `done_reason=length` |

**Note:** REQUIREMENTS.md still shows PIPE-01 through PIPE-04 as `[ ]` (unchecked) and "Pending" in the traceability table. This is a documentation gap — the checkbox states were not updated after phase 6 completion. The implementations are fully present and all tests pass. This is a WARNING-level finding, not a BLOCKER.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, `PLACEHOLDER` markers found in any phase-modified file. No stub implementations (empty returns, placeholder values, disconnected props). One `SyntaxWarning` for `\d` invalid escape in `llm_client.py` system prompt string (pre-existing from before this phase, not introduced by phase 6).

### Human Verification Required

#### 1. Live Two-Pass Smoke Test

**Test:** Run the CLI with Ollama running locally: `echo -e "Senior ML Engineer\nPython, PyTorch, distributed training, MLOps\nEND" | uv run python -m resume_tailor.cli`

**Expected:**
```
Resume Tailor
Paste the job description below. Type END on a new line to submit.

>
Analyzing job description...
Tailoring resume — this may take a minute...
Tailored resume written to: /path/to/tailored_resume_YYYYMMDD_HHMMSS.tex
```

**Why human:** The two-pass LLM call sequence — analysis call producing a real dict that is injected into the tailoring prompt — can only be confirmed by observing an actual Ollama run. Unit tests mock both calls. This is the PLAN 05 `checkpoint:human-verify` gate that was deferred.

#### 2. Fallback Path Validation (Ollama Unreachable)

**Test:** Run the CLI on a machine where Ollama is not running (or with `OLLAMA_BASE_URL` pointing to an unreachable host).

**Expected:**
```
Analyzing job description...
Error: Ollama is not reachable at http://localhost:11434
```
Exit code 1. Only one progress message printed (the analysis message, not the tailoring message).

**Why human:** The specific error wording, exit code, and absence of the second progress message require a real environment where Ollama is absent.

### Gaps Summary

No blocking gaps found. All 8 ROADMAP success criteria truths are verified in the codebase. All required artifacts exist, are substantive, and are fully wired. Data flows from `analyze_job_description` through `analysis=analysis` into `_build_messages` and into the tailoring prompt. The full test suite (89 passed, 2 skipped) confirms no regressions.

**Documentation gap (WARNING, non-blocking):** REQUIREMENTS.md PIPE-01 through PIPE-04 checkboxes and traceability table still show "Pending" — they were not updated after phase 6 completion. This does not affect functionality.

**Human verification pending:** The PLAN 05 `checkpoint:human-verify` gate (Task 2) requires a human to confirm the live two-pass progress message sequence on a machine running Ollama. Automated checks passed. Awaiting human approval.

---

_Verified: 2026-06-07T18:00:00Z_
_Verifier: Claude (gsd-verifier)_
