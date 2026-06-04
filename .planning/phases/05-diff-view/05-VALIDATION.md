---
phase: 05
slug: diff-view
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-04
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | DIFF-01 | — | N/A | unit | `uv run pytest src/diff_view_test.py -x -q` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | DIFF-02 | — | N/A | unit | `uv run pytest src/diff_view_test.py::TestShowDiffTTYGate::test_suppressed_when_not_tty -x -q` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | DIFF-03 | — | N/A | unit | `uv run pytest src/diff_view_test.py::TestShowDiffNormalization -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/diff_view_test.py` — unit tests for DIFF-01, DIFF-02, DIFF-03 (created by Plan 05-01 Task 2)
- [ ] No conftest.py needed — tests use unittest.TestCase with patch

*Existing test infrastructure (pytest via pyproject.toml) detected — only new test stubs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Diff renders with ANSI color in interactive terminal | DIFF-01 | ANSI color rendering requires a real TTY; cannot be automated in pytest without a PTY harness | Run `uv run resume-tailor` in a real terminal, confirm green/red coloring appears on diff lines |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
