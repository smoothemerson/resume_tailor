---
phase: 11
slug: e2e-tests
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-08
audited: 2026-06-08
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/e2e/test_cli.py -m e2e -v` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds (error-path only without Ollama) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/e2e/test_cli.py -m e2e -v`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | TEST-10 | — | N/A | e2e | `uv run pytest tests/e2e/test_cli.py::test_empty_jd_exits_1_with_stderr_message -v` | ✅ | ✅ green |
| 11-01-02 | 01 | 1 | TEST-11 | — | N/A | e2e | `uv run pytest tests/e2e/test_cli.py::test_golden_path_exits_0_creates_output_file -v` | ✅ | ✅ green (skips without Ollama) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/e2e/test_cli.py` — covers TEST-10 and TEST-11

*All wave 0 requirements satisfied. pytest infrastructure, markers, conftest, and the e2e directory are all in place.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-06-08

---

## Validation Audit 2026-06-08

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All requirements COVERED. TEST-10 (PASSED) and TEST-11 (SKIPPED when Ollama absent — correct designed behavior). Full suite: 39 passed, 3 skipped.
