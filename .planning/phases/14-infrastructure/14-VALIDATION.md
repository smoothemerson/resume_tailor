---
phase: 14
slug: infrastructure
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-09
audited: 2026-06-13
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
| 14-01-01 | 01 | 1 | PKG-01 | — | N/A | smoke | `uv build && unzip -l dist/*.whl \| grep -E "jd_analyzer\|keyword_matcher"` | ✅ | ✅ green |
| 14-01-02 | 02 | 1 | TEST-14 | — | N/A | unit | `uv run pytest tests/unit/test_jd_analyzer.py -m unit` | ✅ | ✅ green |
| 14-01-03 | 02 | 1 | TEST-15 | — | N/A | unit | `uv run pytest tests/unit/test_resume_reader.py -m unit` | ✅ | ✅ green |
| 14-01-04 | 02 | 1 | TEST-16 | — | N/A | unit | `uv run pytest tests/unit/test_resume_writer.py -m unit` | ✅ | ✅ green |
| 14-01-05 | 01 | 1 | CI-01 | — | No secrets referenced in workflow | manual | `.github/workflows/ci.yml` exists, no ${{ secrets.* }} refs | ✅ | ✅ green |
| 14-01-06 | 03 | 1 | REPO-01 | — | N/A | manual | `git ls-files .claude/` returns nothing | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_jd_analyzer.py` — 6 unit tests for `_parse_analysis_response` (TEST-14) *(delivered at tests/unit/, not src/, per code review)*
- [x] `tests/unit/test_resume_reader.py` — 2 unit tests for `read_resume` (TEST-15)
- [x] `tests/unit/test_resume_writer.py` — 4 unit tests for `write_resume` (TEST-16)
- [x] `.github/workflows/ci.yml` — CI workflow (CI-01)
- [x] Framework already installed: `pytest >=9.0.3` in `[dependency-groups].dev`; no install beyond `uv sync`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI workflow triggers on push/PR to main | CI-01 | Requires a live GitHub push or PR to validate trigger | Push to main or open PR; observe GitHub Actions tab — job must appear and pass |
| `.claude/` removed from git tracking | REPO-01 | Requires `git ls-files` inspection post-commit | Run `git ls-files .claude/` after commit — must return empty |
| `.gitignore` contains `.claude/` | REPO-01 | File content check | `grep '\.claude/' .gitignore` must return a match |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-06-13

---

## Validation Audit 2026-06-13

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Tests passing | 38 (unit -m unit) |
| Requirements covered | 6/6 (PKG-01, CI-01, TEST-14, TEST-15, TEST-16, REPO-01) |

**Notes:** Test files were delivered at `tests/unit/` rather than `src/` (per code review deviation). VALIDATION.md file paths corrected to match actual locations. All 38 unit tests green. Manual verifications (CI trigger, gitignore) confirmed via file inspection and `git ls-files`.
