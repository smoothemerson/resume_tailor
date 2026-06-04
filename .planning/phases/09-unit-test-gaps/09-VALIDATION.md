---
phase: 9
slug: unit-test-gaps
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-04
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest -m unit tests/unit/ -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -m unit tests/unit/ -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 9-01-01 | 01 | 1 | TEST-04 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_llm_client.py -x` | ❌ W0 | ⬜ pending |
| 9-01-02 | 01 | 1 | TEST-05 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_llm_client.py -x` | ❌ W0 | ⬜ pending |
| 9-02-01 | 02 | 1 | TEST-06 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_resume_reader.py -x` | ❌ W0 | ⬜ pending |
| 9-03-01 | 03 | 1 | TEST-07 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_resume_writer.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_llm_client.py` — covers TEST-04 and TEST-05
- [ ] `tests/unit/test_resume_reader.py` — covers TEST-06
- [ ] `tests/unit/test_resume_writer.py` — covers TEST-07

*(All three files must be created in Wave 1 — they are the phase deliverable.)*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
