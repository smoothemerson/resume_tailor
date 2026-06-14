---
phase: 13
slug: guard-expansion
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-09
audited: 2026-06-12
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest -m unit tests/unit/test_guards.py` |
| **Full suite command** | `pytest -m unit` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -m unit tests/unit/test_guards.py`
- **After every plan wave:** Run `pytest -m unit`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_substitution` | ✅ | ✅ green |
| 13-01-02 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_removal_only` | ✅ | ✅ green |
| 13-01-03 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_addition_only` | ✅ | ✅ green |
| 13-01-04 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_silent_for_identical` | ✅ | ✅ green |
| 13-01-05 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_silent_for_no_skills_section` | ✅ | ✅ green |
| 13-01-06 | 01 | 1 | TEST-12 | — | Guard never raises on malformed input | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_malformed_input_no_raise` | ✅ | ✅ green |
| 13-02-01 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_contact_diff` | ✅ | ✅ green |
| 13-02-02 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_education_diff` | ✅ | ✅ green |
| 13-02-03 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_languages_diff` | ✅ | ✅ green |
| 13-02-04 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_run_guards_warns_on_employer_header_change` | ✅ | ✅ green |
| 13-02-05 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_silent_when_unchanged` | ✅ | ✅ green |
| 13-02-06 | 02 | 1 | TEST-13 | — | Guard never raises on empty strings | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_empty_strings_no_raise` | ✅ | ✅ green |
| 13-03-01 | 03 | 2 | GARD-07 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_run_guards_calls_technology_substitution` | ✅ | ✅ green |
| 13-03-02 | 03 | 2 | GARD-07 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_run_guards_warns_on_contact_block_removed` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_guards.py` — created with 14 `@pytest.mark.unit` tests covering GARD-05, GARD-06, GARD-07, TEST-12, TEST-13
- [x] No `tests/unit/__init__.py` needed — `pythonpath = ["src"]` in `pyproject.toml` resolves imports

*All Wave 0 requirements satisfied. 14/14 tests green.*

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-06-12

---

## Validation Audit 2026-06-12

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Tests verified green | 14 |
| Test name corrections (post-review sync) | 2 |

*Notes: Two test names updated in Per-Task Map to reflect post-code-review renames: `test_protected_sections_warns_on_employer_header_change` → `test_run_guards_warns_on_employer_header_change` (WR-01); `test_run_guards_new_guards_never_raise` → `test_run_guards_warns_on_contact_block_removed` (WR-02). Requirements unchanged; all 14 tests green.*
