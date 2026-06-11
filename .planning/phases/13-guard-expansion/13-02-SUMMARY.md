---
phase: 13-guard-expansion
plan: "02"
subsystem: guards
tags: [guards, tdd, unit-tests, latex-parsing, protected-sections, contact-block, employer-headers, project-anchors]
dependency_graph:
  requires: [13-01]
  provides: [_check_protected_sections]
  affects: [src/guards.py, tests/unit/test_guards.py]
tech_stack:
  added: []
  patterns:
    - contact block extraction via re.search(r'\\begin{center}(.*?)\\end{center}', text, re.DOTALL)
    - Education/Languages section comparison via _extract_section() helper from Plan 01
    - employer header set-diff via _EMPLOYER_PATTERN.findall()
    - project anchor tuple set-diff via \href{url}{\textbf{Name}} regex
    - never-raise try/except Exception wrapper per D-13
key_files:
  created: []
  modified:
    - src/guards.py
    - tests/unit/test_guards.py
decisions:
  - Contact block extracted as first \begin{center}...\end{center} block per Pattern 4 in RESEARCH.md
  - Employer headers compared via set-diff (original_headers - tailored_headers); guard is forward-compatible (silent on current english.tex since it uses raw bold text, not \employer{})
  - Project anchors compared as (url, name) tuples; dates and subtitles excluded (can legitimately be tailored per D-08 resolution)
  - _extract_section() helper from Plan 01 reused directly for Education and Languages checks
metrics:
  duration: "1m"
  completed: "2026-06-11T21:15:26Z"
  tasks_completed: 2
  files_changed: 2
---

# Phase 13 Plan 02: Protected Sections Guard Summary

TDD implementation of `_check_protected_sections(original, tailored)` in `src/guards.py` (GARD-06) with six `@pytest.mark.unit` tests appended to `tests/unit/test_guards.py` (TEST-13). The guard detects mutations to protected resume elements — contact block, Education section, Languages section, employer header macros, and project anchors — emitting one warning per changed element per D-10.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Write failing tests for _check_protected_sections | fe7d25e | tests/unit/test_guards.py (updated) |
| 2 (GREEN) | Implement _check_protected_sections in guards.py | 95460a2 | src/guards.py (modified) |

## Verification Results

- `pytest -m unit tests/unit/test_guards.py -v` — 12 passed (6 Plan-01 + 6 Plan-02)
- `pytest src/guards_test.py` — 14 passed (existing tests unaffected)
- `ruff check src/guards.py` — All checks passed
- `grep -c "def _check_protected_sections" src/guards.py` — 1

## TDD Gate Compliance

- RED gate commit: `fe7d25e` — `test(13-02): add failing tests for _check_protected_sections (RED)` — ImportError at collection time confirmed
- GREEN gate commit: `95460a2` — `feat(13-02): implement _check_protected_sections in guards.py (GREEN)` — all 12 tests pass

## Deviations from Plan

None - plan executed exactly as written.

## Implementation Notes

- Contact block extraction: `re.search(r'\\begin\{center\}(.*?)\\end\{center\}', text, re.DOTALL)` — compares `.group(1).strip()` results; silently skips if either side has no center block
- `_extract_section()` reused for Education and Languages checks per the plan's `key_links`; comparison only fires when both sections are not None
- Employer header comparison: `set(_EMPLOYER_PATTERN.findall(original)) - set(_EMPLOYER_PATTERN.findall(tailored))`; `header[0]` is the employer name from the three-tuple match
- Project anchor comparison: `re.findall(r'\\href\{([^}]+)\}\{\\textbf\{([^}]+)\}\}', text)` yields `(url, name)` tuples; set-diff emits one warning per missing project
- Never-raise wrapper: `try/except Exception as exc: logger.warning(f"Protected sections check failed: {exc}")` per D-13
- `run_guards()` NOT modified in this plan — GARD-07 wiring is handled in Plan 03

## Known Stubs

None. The function is fully implemented with all five element checks. `run_guards()` is not yet updated (per plan spec — Plan 03 handles GARD-07 wiring).

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. The guard processes in-memory strings from an existing pipeline and emits `logger.warning()` only.

## Self-Check: PASSED

- `src/guards.py` — FOUND (contains `def _check_protected_sections`)
- `tests/unit/test_guards.py` — FOUND (contains 12 `@pytest.mark.unit` tests)
- Commit `fe7d25e` — FOUND (`test(13-02): add failing tests for _check_protected_sections (RED)`)
- Commit `95460a2` — FOUND (`feat(13-02): implement _check_protected_sections in guards.py (GREEN)`)
