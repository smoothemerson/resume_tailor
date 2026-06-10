---
phase: 13
slug: guard-expansion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-09
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
| 13-01-01 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_substitution` | ❌ Wave 0 | ⬜ pending |
| 13-01-02 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_removal_only` | ❌ Wave 0 | ⬜ pending |
| 13-01-03 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_addition_only` | ❌ Wave 0 | ⬜ pending |
| 13-01-04 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_silent_for_identical` | ❌ Wave 0 | ⬜ pending |
| 13-01-05 | 01 | 1 | GARD-05 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_silent_for_no_skills_section` | ❌ Wave 0 | ⬜ pending |
| 13-01-06 | 01 | 1 | TEST-12 | — | Guard never raises on malformed input | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_malformed_input_no_raise` | ❌ Wave 0 | ⬜ pending |
| 13-02-01 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_contact_diff` | ❌ Wave 0 | ⬜ pending |
| 13-02-02 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_education_diff` | ❌ Wave 0 | ⬜ pending |
| 13-02-03 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_languages_diff` | ❌ Wave 0 | ⬜ pending |
| 13-02-04 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_employer_header_change` | ❌ Wave 0 | ⬜ pending |
| 13-02-05 | 02 | 1 | GARD-06 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_silent_when_unchanged` | ❌ Wave 0 | ⬜ pending |
| 13-02-06 | 02 | 1 | TEST-13 | — | Guard never raises on empty strings | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_empty_strings_no_raise` | ❌ Wave 0 | ⬜ pending |
| 13-03-01 | 03 | 2 | GARD-07 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_run_guards_calls_technology_substitution` | ❌ Wave 0 | ⬜ pending |
| 13-03-02 | 03 | 2 | GARD-07 | — | N/A | unit | `pytest -m unit tests/unit/test_guards.py::test_run_guards_new_guards_never_raise` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_guards.py` — new file with stubs for GARD-05, GARD-06, GARD-07, TEST-12, TEST-13
- [ ] No `tests/unit/__init__.py` needed — `pythonpath = ["src"]` in `pyproject.toml` resolves imports

*Existing infrastructure covers all framework and config requirements.*

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
