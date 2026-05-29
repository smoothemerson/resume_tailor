---
phase: "03"
slug: cli-wiring
status: compliant
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-29
audited: 2026-05-29
---

# Phase 03 — Validation Strategy

> Per-phase validation contract. Audited retroactively from 03-01-PLAN.md and 03-01-SUMMARY.md.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `/workspace/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest src/cli_test.py -v --tb=short` |
| **Full suite command** | `uv run pytest src/ -v --tb=short` |
| **Estimated runtime** | ~0.1 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest src/cli_test.py -v --tb=short`
- **After every plan wave:** Run `uv run pytest src/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** <1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | CORE-02 | — | END sentinel breaks loop; lines assembled and passed to LLM | unit | `uv run pytest src/cli_test.py::TestInputLoop::test_end_sentinel_breaks_loop -v` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | CORE-02 | — | EOFError treated as submission; generate_tailored_resume called | unit | `uv run pytest src/cli_test.py::TestInputLoop::test_eof_treated_as_submission -v` | ✅ | ✅ green |
| 03-01-03 | 01 | 1 | CORE-02 | T-03-03 | Empty JD guard → stderr + exit 1 before any LLM call | unit | `uv run pytest src/cli_test.py::TestInputLoop::test_empty_jd_exits_1 -v` | ✅ | ✅ green |
| 03-01-04 | 01 | 1 | CORE-03 | — | Progress message "Tailoring resume…" printed to stdout before LLM call | unit | `uv run pytest src/cli_test.py::TestSuccessPath::test_progress_message_printed -v` | ✅ | ✅ green |
| 03-01-05 | 01 | 1 | D-02 | T-03-03 | RuntimeError from LLM → "Error: {msg}" to stderr + exit 1 | unit | `uv run pytest src/cli_test.py::TestErrorHandling::test_runtime_error_from_llm_exits_1 -v` | ✅ | ✅ green |
| 03-01-06 | 01 | 1 | D-02 | T-03-03 | ValueError from LLM → "Error: {msg}" to stderr + exit 1 | unit | `uv run pytest src/cli_test.py::TestErrorHandling::test_value_error_from_llm_exits_1 -v` | ✅ | ✅ green |
| 03-01-07 | 01 | 1 | CORE-06 | T-03-02 | Success path prints "Tailored resume written to:" with absolute path | unit | `uv run pytest src/cli_test.py::TestSuccessPath::test_success_prints_absolute_path -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covered all phase requirements.

- `src/cli_test.py` — created during TDD RED gate (commit aba9cff), extended during Nyquist audit
- pytest 9.0.3 installed as dev dependency (commit 739f373)

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Audit 2026-05-29

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |

**Gaps resolved:**
1. CORE-03 (PARTIAL) → added `test_progress_message_printed` in `TestSuccessPath`
2. ValueError error path (MISSING) → added `test_value_error_from_llm_exits_1` in `TestErrorHandling`

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] Sampling continuity: all 7 tasks have automated verification
- [x] No Wave 0 gaps outstanding
- [x] No watch-mode flags
- [x] Feedback latency < 1s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-29
