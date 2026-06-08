---
phase: 9
slug: unit-test-gaps
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-04
audited: 2026-06-05
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
| 9-01-01 | 01 | 1 | TEST-04 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_llm_client.py -x` | ✅ | ✅ green |
| 9-01-02 | 01 | 1 | TEST-05 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_llm_client.py -x` | ✅ | ✅ green |
| 9-01-03 | 01 | 1 | *(bonus — WR-04)* | — | N/A | unit | `uv run pytest -m unit tests/unit/test_llm_client.py -x` | ✅ | ✅ green |
| 9-02-01 | 02 | 1 | TEST-06 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_resume_reader.py -x` | ✅ | ✅ green |
| 9-02-02 | 02 | 1 | TEST-07 | — | N/A | unit | `uv run pytest -m unit tests/unit/test_resume_writer.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_llm_client.py` — covers TEST-04 and TEST-05 (24 tests; 12 additional added in WR-04)
- [x] `tests/unit/test_resume_reader.py` — covers TEST-06 (2 tests)
- [x] `tests/unit/test_resume_writer.py` — covers TEST-07 (4 tests)

*(All three files created in Wave 1 — phase deliverable complete.)*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 2s (actual: 0.04s for 30 tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-06-05 — all 30 unit tests green, 0 gaps

---

## Validation Audit 2026-06-05

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Total tests verified | 30 |
| Suite runtime | 0.04s |

*Note: test_llm_client.py contains 24 tests (12 from plan 01 + 12 added in WR-04 post-UAT fix covering `_strip_fences`, `_validate_latex`, and `generate_tailored_resume`). Task ID 9-03-01 corrected to 9-02-02 (plan 02 covered both reader and writer).*
