---
phase: 8
slug: test-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-02
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
| **Estimated runtime** | ~1 second (collect-only < 0.5s; full suite ~0.15s for 18 tests) |

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
| 08-01-01 | 01 | 1 | TEST-01 | — | N/A | smoke | `uv run pytest --co -q` | n/a | ⬜ pending |
| 08-01-02 | 01 | 1 | TEST-01 | — | N/A | smoke | `uv run pytest -m foo; test $? -ne 0` | n/a | ⬜ pending |
| 08-01-03 | 01 | 1 | TEST-02 | — | N/A | smoke | `uv run pytest -m integration` (Ollama down → exit 0, SKIPPED) | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 1 | TEST-03 | — | N/A | structural | `ls tests/unit tests/integration tests/e2e` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — `ollama_available` + `require_ollama` fixtures (TEST-02)
- [ ] `tests/unit/`, `tests/integration/`, `tests/e2e/` — empty directories (TEST-03)
- [ ] `pyproject.toml` — `[tool.pytest.ini_options]` section with testpaths, pythonpath, markers, addopts (TEST-01)

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
