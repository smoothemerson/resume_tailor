---
phase: 07
slug: jd-keyword-match-summary
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-08
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 (via `.venv`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q` |
| **Full suite command** | `/workspace/.venv/bin/pytest -x -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q`
- **After every plan wave:** Run `/workspace/.venv/bin/pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 0 | MATCH-01 | — | N/A | unit | `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | MATCH-01 | — | N/A | unit | `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | MATCH-02 | — | N/A | unit | `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | MATCH-03 | — | N/A | unit | `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q` | ❌ W0 | ⬜ pending |
| 07-01-05 | 01 | 2 | MATCH-01/03 | — | N/A | unit | `/workspace/.venv/bin/pytest src/cli_test.py -x -q` | ✅ needs new test | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/keyword_matcher_test.py` — stubs for MATCH-01, MATCH-02, MATCH-03
- [ ] `src/keyword_matcher.py` — module stub with `show_keyword_match()` signature

*Wave 0 creates the test file and module stub before any implementation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Match summary appears in TTY session | MATCH-03 | Requires a real terminal (isatty=True) | Run `python -m resume_tailor.cli` with a job description; verify summary prints after diff |
| Match summary suppressed when piped | MATCH-03 | Requires pipe redirect | Run `python -m resume_tailor.cli > /tmp/out.tex`; verify no match summary in stdout |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
