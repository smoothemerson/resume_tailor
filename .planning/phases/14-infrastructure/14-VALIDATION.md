---
phase: 14
slug: infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-09
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest -m unit` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -m unit`
- **After every plan wave:** Run `uv run pytest -m unit`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | PKG-01 | — | N/A | smoke | `uv build && unzip -l dist/*.whl \| grep -E "jd_analyzer\|keyword_matcher"` | ✅ | ⬜ pending |
| 14-01-02 | 01 | 1 | TEST-14 | — | N/A | unit | `uv run pytest src/jd_analyzer_test.py -m unit` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 1 | TEST-15 | — | N/A | unit | `uv run pytest src/resume_reader_test.py -m unit` | ❌ W0 | ⬜ pending |
| 14-01-04 | 01 | 1 | TEST-16 | — | N/A | unit | `uv run pytest src/resume_writer_test.py -m unit` | ❌ W0 | ⬜ pending |
| 14-01-05 | 01 | 1 | CI-01 | — | No secrets referenced in workflow | manual | `yamllint .github/workflows/ci.yml` | ❌ W0 | ⬜ pending |
| 14-01-06 | 01 | 1 | REPO-01 | — | N/A | manual | `git ls-files .claude/` returns nothing | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/jd_analyzer_test.py` — 6 unit tests for `_parse_analysis_response` (TEST-14)
- [ ] `src/resume_reader_test.py` — 2 unit tests for `read_resume` (TEST-15)
- [ ] `src/resume_writer_test.py` — 3 unit tests for `write_resume` (TEST-16)
- [ ] `.github/workflows/ci.yml` — CI workflow (CI-01)
- [ ] Framework already installed: `pytest >=9.0.3` in `[dependency-groups].dev`; no install beyond `uv sync`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI workflow triggers on push/PR to main | CI-01 | Requires a live GitHub push or PR to validate trigger | Push to main or open PR; observe GitHub Actions tab — job must appear and pass |
| `.claude/` removed from git tracking | REPO-01 | Requires `git ls-files` inspection post-commit | Run `git ls-files .claude/` after commit — must return empty |
| `.gitignore` contains `.claude/` | REPO-01 | File content check | `grep '\.claude/' .gitignore` must return a match |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
