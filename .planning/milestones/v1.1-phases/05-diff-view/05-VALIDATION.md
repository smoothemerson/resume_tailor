---
phase: 05
slug: diff-view
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-04
audited: 2026-06-05
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest src/ tests/ -x -q` |
| **Full suite command** | `uv run pytest src/ tests/ -v` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest src/ tests/ -x -q`
- **After every plan wave:** Run `uv run pytest src/ tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | DIFF-01 | — | N/A | unit | `uv run pytest src/diff_view_test.py -x -q` | ✅ | ✅ green |
| 05-01-02 | 01 | 1 | DIFF-02 | — | N/A | unit | `uv run pytest src/diff_view_test.py::TestShowDiffTTYGate::test_suppressed_when_not_tty -x -q` | ✅ | ✅ green |
| 05-01-03 | 01 | 1 | DIFF-03 | — | N/A | unit | `uv run pytest src/diff_view_test.py::TestShowDiffNormalization -x -q` | ✅ | ✅ green |
| 05-02-01 | 02 | 2 | DIFF-01 | T-05-03 | show_diff outside try/except; never suppresses confirmation | integration | `uv run pytest src/cli_test.py::test_show_diff_called_with_resume_and_tailored -x -q` | ✅ | ✅ green |
| 05-02-02 | 02 | 2 | DIFF-01,DIFF-02,DIFF-03 | — | N/A | integration | `uv run pytest src/cli_test.py -x -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `src/diff_view_test.py` — unit tests for DIFF-01, DIFF-02, DIFF-03 (created by Plan 05-01 Task 2)
- [x] No conftest.py needed — tests use unittest.TestCase with patch

*Existing test infrastructure (pytest via pyproject.toml) detected — only new test stubs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Diff renders with ANSI color in interactive terminal | DIFF-01 | ANSI color rendering requires a real TTY; cannot be automated in pytest without a PTY harness | Run `uv run resume-tailor` in a real terminal, confirm green/red coloring appears on diff lines |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-06-05

| Metric | Count |
|--------|-------|
| Tasks audited | 5 |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Missing Plan 05-02 tasks added | 2 |

All 5 tasks COVERED. `src/diff_view_test.py` (11 tests) and `src/cli_test.py` (48 tests, 78 total suite) all green. No test files generated — existing coverage was complete.
