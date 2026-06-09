# Phase 13: Guard Expansion - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Add two new guards to `src/guards.py` — `_check_technology_substitution(original, tailored)` and `_check_protected_sections(original, tailored)` — wire both into `run_guards()`, and ship `tests/unit/test_guards.py` with unit tests for both. Requirements GARD-05, GARD-06, GARD-07, TEST-12, TEST-13.

</domain>

<decisions>
## Implementation Decisions

### Skills Section Extraction (_check_technology_substitution)
- **D-01:** Use `\header{Skills}` as the section boundary — extract content between `\header{Skills}` and the next `\header{...}` command. Consistent with how `_check_missing_sections` already identifies sections, and already validated by the test suite.
- **D-02:** Tokenize on comma-separated items (split on `,\s*`). Skills sections list comma-separated tech names; this correctly handles multi-word names like "Apache Kafka" or "Google Cloud".
- **D-03:** Strip LaTeX formatting macros (`\textbf{}`, `\emph{}`, etc.) before tokenizing. Ensures `\textbf{Python}` and `Python` are treated as the same token.
- **D-04:** If no `\header{Skills}` is found in either original or tailored, return silently — nothing to compare. (GARD-05 spec: "silent for identical or no skills section".)

### Protected Element Patterns (_check_protected_sections)
- **D-05:** Contact block extraction strategy: let the researcher inspect `resumes/english.tex` and identify the actual LaTeX pattern. Guard implementation should match what is found there.
- **D-06:** Education and languages sections: compare full section content between `\header{Education}` and next `\header{...}`, same for `\header{Languages}`. If content differs, emit one warning per changed section.
- **D-07:** Employer header lines: reuse the existing `_EMPLOYER_PATTERN` regex (`\employer{name}{dates}{title}`) to extract employer tuples; warn if any employer header line differs between original and tailored. This is a stricter complement to `_check_hallucinated_employers` (which only catches add/remove).
- **D-08:** Project anchor pattern: let the researcher find the actual project macro in `resumes/english.tex` (likely a custom macro analogous to `\employer`). Guard should be written to match what is actually there.

### Warning Message Content
- **D-09:** `_check_technology_substitution` issues three distinct `logger.warning()` calls for the three GARD-05 cases:
  - Substitution (techs removed AND new techs added): name both removed and added technologies in the message.
  - Removal-only (techs removed, nothing new): name the removed technologies.
  - Addition-only (new techs added, nothing removed): name the added technologies.
- **D-10:** `_check_protected_sections` issues one `logger.warning()` per changed element (e.g., "Education section was modified in tailored output."). One warning per element that differs.

### Test File Placement
- **D-11:** New guard tests (TEST-12, TEST-13) go in `tests/unit/test_guards.py` — a new file. Matches Phase 9 pattern (D-01): `tests/unit/` for `@pytest.mark.unit` tests, `test_*.py` prefix, bare directory, no `__init__.py`.
- **D-12:** Use pytest-style function tests (`def test_*`). Matches existing `tests/unit/` style from Phase 9. Decorate each test with `@pytest.mark.unit`.

### Error Handling
- **D-13:** Both new guards must follow the existing never-raise pattern: wrap all logic in `try/except Exception as exc` and call `logger.warning(f"... check failed: {exc}")`. Matches every existing guard in `guards.py`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/ROADMAP.md` §Phase 13 — Goal, success criteria (5 items), requirements list (GARD-05, GARD-06, GARD-07, TEST-12, TEST-13)
- `.planning/REQUIREMENTS.md` §Guards — Full requirement text for GARD-05, GARD-06, GARD-07
- `.planning/REQUIREMENTS.md` §Guard Tests — Full requirement text for TEST-12, TEST-13

### Source Files (read before implementing)
- `src/guards.py` — Existing guards; study `_check_missing_sections` for the `\header{...}` boundary pattern, `_EMPLOYER_PATTERN` for the employer regex, `run_guards()` for integration point, and the never-raise try/except pattern
- `src/guards_test.py` — Existing tests; shows `patch("guards.logger")` pattern for asserting `logger.warning` calls
- `resumes/english.tex` — **CRITICAL:** Researcher must read this to identify: (a) contact block LaTeX structure, (b) project anchor macro name and arg signature. Guard implementations depend on what is actually in this file.

### Prior Phase Context
- `.planning/milestones/v1.1-phases/09-unit-test-gaps/09-CONTEXT.md` — D-01 to D-12 define test file conventions (tests/unit/, test_*.py, @pytest.mark.unit, pytest-style functions)

### Test Infrastructure
- `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["src", "tests"]`, `pythonpath = ["src"]`, markers (unit, integration, e2e), `addopts = "--strict-markers -ra"` — no changes needed for Phase 13

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')` — in `guards.py`; reuse directly in `_check_protected_sections` for employer header comparison
- `logger` from `log_manager` — already imported in `guards.py`; both new guards use `logger.warning()`
- `\header{...}` boundary pattern from `_check_missing_sections` — `re.findall(r'\\header\{([^}]+)\}', text)` and content extraction between two consecutive `\header{}` calls

### Established Patterns
- **Never-raise pattern**: all guards wrap logic in `try/except Exception as exc` → `logger.warning(f"... check failed: {exc}")`. Both new guards must follow this.
- **Guard → `run_guards()` integration**: each private `_check_*` function is called once in `run_guards(original_text, tailored_text, ...)`. Add both new guards there.
- **Test patch target**: `patch("guards.logger")` — used in all existing guard tests; use the same target in `tests/unit/test_guards.py`.

### Integration Points
- `run_guards(original_text, tailored_text, fences_stripped=False)` in `guards.py:47` — add `_check_technology_substitution(original_text, tailored_text)` and `_check_protected_sections(original_text, tailored_text)` as two new lines.
- `tests/unit/` — new file `test_guards.py` connects here; no `__init__.py` needed; `pythonpath = ["src"]` in `pyproject.toml` resolves `from guards import ...`.

</code_context>

<specifics>
## Specific Ideas

- Section content extraction between two `\header{}` calls:
  ```python
  def _extract_section(text: str, section_name: str) -> str | None:
      pattern = rf'\\header\{{{re.escape(section_name)}\}}(.*?)(?=\\header\{{|$)'
      m = re.search(pattern, text, re.DOTALL)
      return m.group(1) if m else None
  ```
- Technology token extraction:
  ```python
  def _extract_technologies(section_text: str) -> set[str]:
      # strip LaTeX macros
      cleaned = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', section_text)
      return {t.strip() for t in cleaned.split(',') if t.strip()}
  ```
- Substitution detection logic (three cases):
  ```python
  removed = original_techs - tailored_techs
  added = tailored_techs - original_techs
  if removed and added:
      logger.warning(f"Technology substitution in Skills: removed {sorted(removed)}, added {sorted(added)}")
  elif removed:
      logger.warning(f"Technologies removed from Skills: {sorted(removed)}")
  elif added:
      logger.warning(f"Technologies added to Skills not in original: {sorted(added)}")
  ```
- Employer header comparison (reuse `_EMPLOYER_PATTERN`):
  ```python
  original_headers = set(_EMPLOYER_PATTERN.findall(original))
  tailored_headers = set(_EMPLOYER_PATTERN.findall(tailored))
  for header in original_headers - tailored_headers:
      logger.warning(f'Employer header changed or removed: "{header[0]}"')
  ```

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-Guard Expansion*
*Context gathered: 2026-06-09*
