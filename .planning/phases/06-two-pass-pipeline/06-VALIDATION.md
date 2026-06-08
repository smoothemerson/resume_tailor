---
phase: 06
slug: two-pass-pipeline
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-05
audited: 2026-06-08
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest -m unit -x -q` |
| **Full suite command** | `pytest --tb=short -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -m unit -x -q`
- **After every plan wave:** Run `pytest --tb=short -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 0 | PIPE-01, PIPE-03, PIPE-04 | — | N/A | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x` | ✅ | ✅ green |
| 06-01-02 | 01 | 0 | PIPE-02 | — | N/A | unit | `pytest -m unit tests/unit/test_llm_client.py -x -k jd_analysis` | ✅ | ✅ green |
| 06-01-03 | 01 | 0 | PIPE-01, PIPE-03 | — | N/A | unit | `pytest -m unit src/cli_test.py -x` | ✅ | ✅ green |
| 06-02-01 | 02 | 1 | PIPE-01, PIPE-03, PIPE-04 | — | returns None on all non-truncation failures | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x` | ✅ | ✅ green |
| 06-03-01 | 03 | 1 | PIPE-02 | — | N/A | unit | `pytest -m unit tests/unit/test_llm_client.py -x -k jd_analysis` | ✅ | ✅ green |
| 06-04-01 | 04 | 1 | PIPE-01, PIPE-02, PIPE-03 | — | N/A | unit | `pytest -m unit src/cli_test.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_jd_analyzer.py` — 6 tests covering PIPE-01, PIPE-03, PIPE-04 for `analyze_job_description()`
- [x] New test cases in `tests/unit/test_llm_client.py` — covers PIPE-02 (`_build_messages` with/without analysis param)
- [x] Updated `src/cli_test.py` — all 8 existing `main()` tests patched with `@patch("cli.analyze_job_description")`; 3 new two-pass behavior tests added

*All three test files exist and all tests pass.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Two distinct LLM calls visible via progress messages in terminal | PIPE-01 | Requires live Ollama instance | Run `resume-tailor` with a real JD; confirm "Analyzing job description..." then "Tailoring resume..." appear sequentially |
| Silent fallback when pass-1 fails | PIPE-03 | Requires mock Ollama or network manipulation | Mock Ollama to return malformed JSON for the analysis call; confirm resume output still produced with no error message |

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all requirements
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-06-08

---

## Validation Audit 2026-06-08

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |

**Gap:** `src/cli_test.py` was missing `@pytest.mark.unit` on all 11 tests — the command `pytest -m unit src/cli_test.py -x` deselected everything. Added the marker to all 11 functions; full suite remains 89 passed, 2 skipped.
