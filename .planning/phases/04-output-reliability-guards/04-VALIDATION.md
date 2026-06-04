---
phase: 4
slug: output-reliability-guards
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-02
audited: 2026-06-04
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing; no config in pyproject.toml yet — Phase 8 adds that) |
| **Config file** | none — guards_test.py follows existing src/cli_test.py pattern |
| **Quick run command** | `python -m pytest src/guards_test.py -v` |
| **Full suite command** | `python -m pytest src/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest src/guards_test.py -v`
- **After every plan wave:** Run `python -m pytest src/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| guards-create | 01 | 1 | GUARD-01, GUARD-02, GUARD-03, GUARD-04 | — | Guards never raise exceptions (GUARD-04) | unit | `python -m pytest src/guards_test.py -v` | ✅ | ✅ green |
| tailor-result | 01 | 1 | GUARD-02 | — | TailorResult.fences_stripped threads fence detection correctly | unit | `python -m pytest src/guards_test.py -k fences -v` | ✅ | ✅ green |
| cli-integration | 01 | 2 | GUARD-04 | — | write_resume always called regardless of guard warnings | unit | `python -m pytest src/cli_test.py -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `src/guards_test.py` — stubs for GUARD-01, GUARD-02, GUARD-03, GUARD-04

*Wave 0 is creating the test file alongside the implementation — no pre-existing test infrastructure needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GUARD-03 dormancy note | GUARD-03 | `\employer{}` macro unused in current english.tex — guard fires 0 warnings in practice | Run tool against a JD and verify no employer warnings appear; this is expected behavior |

---

## Validation Architecture

This phase uses direct pytest unit tests following the `src/cli_test.py` pattern. Tests are colocated in `src/guards_test.py` using `unittest.TestCase`. All tests are isolated — no Ollama, no file I/O required.

### Test Coverage Plan

**GUARD-01 tests:**
- `test_no_missing_sections` — original and tailored have same headers, no warning
- `test_missing_section_warns` — tailored drops "Skills", warning fires with section name
- `test_multiple_missing_sections` — two sections dropped, two warnings fire

**GUARD-02 tests:**
- `test_no_format_violations` — clean LaTeX, no warnings
- `test_fences_stripped_warns` — fences_stripped=True triggers warning
- `test_inline_backticks_warns` — triple backtick in body triggers warning
- `test_markdown_heading_warns` — line starting with `#` triggers warning

**GUARD-03 tests:**
- `test_no_employers_in_original` — current resume case: 0 employers, 0 warnings
- `test_employer_present_no_warn` — employer in original also in tailored, no warning
- `test_employer_missing_warns` — employer in original missing from tailored, warning fires

**GUARD-04 tests (via cli_test.py):**
- Verify `write_resume` is called even when guards would print warnings
- Verify guard exceptions do not propagate (run_guards is exception-safe)

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-06-04 — all 36 tests pass, zero gaps

---

## Validation Audit 2026-06-04

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Tests verified green | 36 |
| Coverage | GUARD-01 (4 tests), GUARD-02 (4 tests), GUARD-03 (3 tests), GUARD-04 (3 unit + 7 integration) |
