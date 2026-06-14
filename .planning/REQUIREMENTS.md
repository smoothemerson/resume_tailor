# Requirements: Resume Tailor CLI

**Defined:** 2026-06-09
**Core Value:** Given a job description, produce a ready-to-compile LaTeX resume that is genuinely better aligned with that job — not just syntactically valid but actually usable.

## v1.2 Requirements

### Prompt Precision

- [x] **PRMP-01**: `_build_messages()` system prompt defines an explicit ALLOWED list: title line, employer taglines, employer bullets, project subtitle and bullets, skills reordering/reweighting
- [x] **PRMP-02**: `_build_messages()` system prompt defines an explicit MUST-NOT-CHANGE list: candidate name, contact block, education section, languages section, employer header lines, project name/URL/date, all LaTeX structural commands
- [x] **PRMP-03**: System prompt includes an anti-fabrication rule: do not substitute one named technology for another — if Azure is in the original it must appear in output; if AWS is not in the original it must not appear

### Guards

- [ ] **GARD-05**: `_check_technology_substitution(original, tailored)` extracts the Skills section from each text and warns when technologies are substituted, only removed, or only added
- [ ] **GARD-06**: `_check_protected_sections(original, tailored)` warns when any of the following differ between original and tailored: contact block, education section, languages section, employer header lines, project anchors (name/URL/date)
- [ ] **GARD-07**: Both new guards are called from `run_guards()` and never raise — all exceptions are caught and logged as warnings

### Guard Tests

- [ ] **TEST-12**: Unit tests cover `_check_technology_substitution`: substitution, removal-only, addition-only, identical, no-skills-section, malformed input
- [ ] **TEST-13**: Unit tests cover `_check_protected_sections`: contact block diff, education diff, languages diff, employer header changed, unchanged, empty strings passed

### Packaging

- [ ] **PKG-01**: `jd_analyzer.py` and `keyword_matcher.py` are added to the `[tool.hatch.build.targets.wheel]` include list in `pyproject.toml`

### CI

- [ ] **CI-01**: `.github/workflows/ci.yml` triggers on push and pull_request to main, uses ubuntu-latest + Python 3.13, installs deps with uv, runs `ruff check src/` and `pytest -m unit`

### Test Coverage

- [ ] **TEST-14**: `src/jd_analyzer_test.py` covers `_parse_analysis_response`: valid JSON, missing key, non-list value, fenced JSON, non-JSON string, empty string
- [ ] **TEST-15**: `src/resume_reader_test.py` covers `read_resume`: existing file returns content, missing file raises `FileNotFoundError`
- [ ] **TEST-16**: `src/resume_writer_test.py` covers `write_resume`: file created in given dir, filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex`, file content matches input

### Repository Hygiene

- [ ] **REPO-01**: `.claude/` is added to `.gitignore` and untracked from git history so the directory is no longer versioned

## v2 Requirements

### Guards (deferred from v1.1)

- **GARD-08**: Per-section change magnitude warning
- **GARD-09**: Structured output schema enforcement via Ollama `json_schema`

### Workflow (deferred from v1.1)

- **WORK-01**: `--no-diff` opt-in flag to suppress diff output
- **WORK-02**: Persistent keyword match history across runs
- **WORK-03**: Interactive accept/reject of individual changes

## Out of Scope

| Feature | Reason |
|---------|--------|
| LangChain or LLM frameworks | Explicit project constraint — stdlib + requests only |
| Web server or GUI | CLI only |
| Auto-compilation to PDF | User runs pdflatex themselves |
| Multi-resume management | Single base resume for now |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRMP-01 | Phase 12 | Complete |
| PRMP-02 | Phase 12 | Complete |
| PRMP-03 | Phase 12 | Complete |
| GARD-05 | Phase 13 | Pending |
| GARD-06 | Phase 13 | Pending |
| GARD-07 | Phase 13 | Pending |
| TEST-12 | Phase 13 | Pending |
| TEST-13 | Phase 13 | Pending |
| PKG-01 | Phase 14 | Pending |
| CI-01 | Phase 14 | Pending |
| TEST-14 | Phase 14 | Pending |
| TEST-15 | Phase 14 | Pending |
| TEST-16 | Phase 14 | Pending |
| REPO-01 | Phase 14 | Pending |

**Coverage:**

- v1.2 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-09*
*Last updated: 2026-06-09 after initial definition*
