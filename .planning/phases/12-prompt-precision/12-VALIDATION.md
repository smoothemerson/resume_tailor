---
phase: 12
slug: prompt-precision
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-09
audited: 2026-06-12
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3+ |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest -m unit -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -m unit -x`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | PRMP-01 | — | N/A | unit | `pytest tests/unit/test_llm_client.py -x -q -k "allowed or legacy_instructions"` | ✅ | ✅ green |
| 12-01-02 | 01 | 1 | PRMP-02 | — | N/A | unit | `pytest tests/unit/test_llm_client.py -x -q -k "constraints"` | ✅ | ✅ green |
| 12-01-03 | 01 | 1 | PRMP-03 | — | N/A | unit | `pytest tests/unit/test_llm_client.py -x -q -k "technology_fidelity"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification via existing test suite.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved via /gsd-validate-phase audit, 2026-06-12

---

## Validation Audit 2026-06-12

| Metric | Count |
|--------|-------|
| Gaps found | 3 |
| Resolved | 3 |
| Escalated | 0 |

Gap detail: PRMP-01 (MISSING — no `<ALLOWED>` assertions), PRMP-02 (PARTIAL — only tag-boundary asserted), PRMP-03 (MISSING — no TECHNOLOGY FIDELITY assertions). Resolved with 8 new unit tests in `tests/unit/test_llm_client.py`, scoped to the extracted `<CONSTRAINTS>` block and asserting actual LaTeX patterns. Full suite: 112 passed, 3 skipped (Ollama-dependent).

Environment note: `/workspace/.venv/bin/python` is a broken symlink; run tests via `PYTHONPATH=/workspace/.venv/lib/python3.13/site-packages python3 -m pytest`.
