---
phase: 8
slug: test-infrastructure
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-02
audited: 2026-06-04
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (added in this phase) |
| **Quick run command** | `uv run pytest --co -q` |
| **Full suite command** | `uv run pytest -v` |
| **Estimated runtime** | ~1 second (collect-only < 0.5s; full suite ~0.05s for 36 tests) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest --co -q`
- **After every plan wave:** Run `uv run pytest -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | TEST-01 | — | N/A | smoke | `uv run pytest --co -q` | n/a | ✅ green |
| 08-01-02 | 01 | 1 | TEST-01 | — | N/A | smoke | `uv run pytest -m foo; test $? -ne 0` | n/a | ✅ green |
| 08-01-03 | 01 | 1 | TEST-02 | — | N/A | smoke | `uv run pytest -m integration` (Ollama down → exit 5, no tests collected) | ✅ exists | ✅ green |
| 08-01-04 | 01 | 1 | TEST-03 | — | N/A | structural | `ls tests/unit tests/integration tests/e2e` | ✅ exists | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/conftest.py` — `ollama_available` + `require_ollama` fixtures (TEST-02)
- [x] `tests/unit/`, `tests/integration/`, `tests/e2e/` — empty directories (TEST-03)
- [x] `pyproject.toml` — `[tool.pytest.ini_options]` section with testpaths, pythonpath, markers, addopts (TEST-01)

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 2s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-06-04 — all 4 tasks COVERED, 36 tests green, 0 gaps

---

## Validation Audit 2026-06-04

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Tasks audited | 4 |
| Tests collected | 36 |

All requirements (TEST-01, TEST-02, TEST-03) verified green. No new test files needed.
