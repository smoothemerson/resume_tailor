---
phase: 10
slug: integration-tests
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-05
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest -m "not integration"` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~5 seconds (unit suite); integration tests skip if Ollama down |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -m "not integration"` (fast suite; integration tests not required per commit)
- **After every plan wave:** Run `uv run pytest` (full suite; integration tests skip cleanly if Ollama down)
- **Before `/gsd-verify-work`:** `uv run pytest -m integration` must pass with Ollama running
- **Max feedback latency:** ~5 seconds (unit suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | TEST-08 | — | N/A — test-only code, localhost-only | integration | `uv run pytest -m integration -k health` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | TEST-09 | — | N/A — test-only code, localhost-only | integration | `uv run pytest -m integration -k latex` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/integration/test_llm_client.py` — covers TEST-08, TEST-09 (the entire phase deliverable)

*`tests/integration/` directory already exists (Phase 8). pytest config and `integration` marker already registered. `require_ollama` fixture already in `tests/conftest.py`. No framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `pytest -m integration` SKIPPED when Ollama stopped | TEST-08, TEST-09 | Requires stopping Ollama service | Stop Ollama (`killall ollama` or stop the service), run `uv run pytest -m integration`, verify all tests show SKIPPED (not FAILED), exit code 0 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
