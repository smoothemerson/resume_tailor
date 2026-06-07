---
phase: 06
slug: two-pass-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-05
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
| 06-01-01 | 01 | 0 | PIPE-01, PIPE-03, PIPE-04 | — | N/A | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 0 | PIPE-02 | — | N/A | unit | `pytest -m unit tests/unit/test_llm_client.py -x -k jd_analysis` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 0 | PIPE-01, PIPE-03 | — | N/A | unit | `pytest -m unit src/cli_test.py -x` | ✅ modify | ⬜ pending |
| 06-02-01 | 02 | 1 | PIPE-01, PIPE-03, PIPE-04 | — | returns None on all non-truncation failures | unit | `pytest -m unit tests/unit/test_jd_analyzer.py -x` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 1 | PIPE-02 | — | N/A | unit | `pytest -m unit tests/unit/test_llm_client.py -x -k jd_analysis` | ❌ W0 | ⬜ pending |
| 06-04-01 | 04 | 1 | PIPE-01, PIPE-02, PIPE-03 | — | N/A | unit | `pytest -m unit src/cli_test.py -x` | ✅ modify | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_jd_analyzer.py` — stubs covering PIPE-01, PIPE-03, PIPE-04 for `analyze_job_description()`
- [ ] New test cases in `tests/unit/test_llm_client.py` — covers PIPE-02 (`_build_messages` with/without analysis param)
- [ ] Updated `src/cli_test.py` — add `@patch("cli.analyze_job_description")` to all 8 existing `main()` tests to prevent breakage after wiring

*All three test files must exist (or be updated) before implementation tasks run.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Two distinct LLM calls visible via progress messages in terminal | PIPE-01 | Requires live Ollama instance | Run `resume-tailor` with a real JD; confirm "Analyzing job description..." then "Tailoring resume..." appear sequentially |
| Silent fallback when pass-1 fails | PIPE-03 | Requires mock Ollama or network manipulation | Mock Ollama to return malformed JSON for the analysis call; confirm resume output still produced with no error message |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
