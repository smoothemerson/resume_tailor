# Requirements: Resume Tailor CLI

**Defined:** 2026-06-02
**Core Value:** Given a job description, produce a ready-to-compile LaTeX resume that is genuinely better aligned with that job — not just syntactically valid but actually usable.

## v1.1 Requirements

Requirements for Output Quality + Test Coverage milestone. Each maps to roadmap phases.

### Output Guards

- [x] **GUARD-01**: Tool warns when a section present in the original resume is missing from the tailored output
- [x] **GUARD-02**: Tool warns when tailored output contains markdown prose or other format violations (LaTeX-only rule broken)
- [x] **GUARD-03**: Tool warns when structured fields (employer names, dates, skills tokens) appear in output but were not in original resume
- [x] **GUARD-04**: Guards degrade gracefully — any guard failure prints a warning to stderr but does not block the output write

### Diff View

- [x] **DIFF-01**: Tool shows a normalized unified diff of original vs tailored resume after tailoring, when stdout is a TTY
- [x] **DIFF-02**: Diff is suppressed automatically when stdout is piped or redirected (no flag required)
- [x] **DIFF-03**: Diff normalization eliminates whitespace-only noise (trailing space, blank line collapsing) so only meaningful changes appear

### Two-Pass Pipeline

- [x] **PIPE-01**: Tool performs a JD analysis pass (pass 1) before the tailoring call — extracts key technologies, role requirements, and emphasis areas from the job description
- [x] **PIPE-02**: Analysis output is injected into the tailoring prompt (pass 2) to guide section-specific rewrites
- [x] **PIPE-03**: If pass 1 fails (malformed output, parse error), tool falls back to single-pass behavior — no abort, no error surfaced to user
- [x] **PIPE-04**: Both LLM calls respect existing done_reason truncation guard

### JD Match Summary

- [ ] **MATCH-01**: After tailoring, tool displays which keywords from pass 1's analysis appear in the tailored resume
- [ ] **MATCH-02**: Keyword matching uses whole-word regex with stop word filtering to prevent substring false positives
- [ ] **MATCH-03**: Match summary is displayed to stdout only when running interactively (TTY guard, same as diff)

### Test Infrastructure

- [x] **TEST-01**: pytest configured in pyproject.toml — testpaths includes both `src` and `tests`, pythonpath set to `["src"]`, three markers registered (`unit`, `integration`, `e2e`), `--strict-markers` and `-ra` in addopts
- [x] **TEST-02**: `tests/conftest.py` provides a session-scoped `ollama_available` fixture (HTTP probe, runs once per session) and a `require_ollama` fixture that skips the test when Ollama is unreachable
- [x] **TEST-03**: `tests/` organized into `unit/`, `integration/`, and `e2e/` subdirectories; existing `src/*_test.py` files left in place

### Unit Test Gaps

- [x] **TEST-04**: `_build_messages()` tested: returns 2-element list with roles `"system"` then `"user"`; user content contains `<job_description>` and `<resume>` XML tags embedding the provided inputs; system content contains `<PERSONA>` and `<CONSTRAINTS>` markers
- [x] **TEST-05**: `_check_ollama_health()` tested in isolation: raises `RuntimeError` on `ConnectionError`; raises `RuntimeError` on `Timeout`; does not raise when response status is 200
- [x] **TEST-06**: `read_resume()` tested: returns file text content when file exists; raises `FileNotFoundError` when file does not exist
- [x] **TEST-07**: `write_resume()` tested: creates output directory if it does not exist; returns a `Path`; written filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex` pattern; file content equals the input string

### Integration Tests

- [ ] **TEST-08**: Integration test: Ollama health endpoint returns 200 when Ollama is running; test is skipped (not failed) when Ollama is unreachable
- [ ] **TEST-09**: Integration test: `generate_tailored_resume()` with a minimal synthetic resume and a short JD returns a string starting with `\documentclass` and ending with `\end{document}`, with no markdown fences; test is skipped when Ollama is unreachable

### E2E Tests

- [ ] **TEST-10**: E2E test: CLI subprocess exits 1 and prints an error to stderr when given empty JD input (END sentinel immediately); does not require Ollama running
- [ ] **TEST-11**: E2E test: CLI subprocess exits 0 when given a real JD, creates an output file in a temp directory with filename matching the timestamp pattern, and stdout contains `"Tailored resume written to:"`; test is skipped when Ollama is unreachable

## Future Requirements

### Workflow

- Opt-in `--no-diff` flag to suppress diff for scripted use
- Persistent match history to compare scores across runs
- Interactive accept/reject of individual changes

### Guards

- Per-section change magnitude warning (guard against over-rewriting)
- Structured output schema enforcement (Ollama `json_schema` format field)

## Out of Scope

| Feature | Reason |
|---------|--------|
| PDF compilation | User runs pdflatex; out of scope by design |
| LangChain or LLM frameworks | Project constraint: stdlib + requests only |
| Web UI or GUI | CLI-only tool |
| Multi-resume management | Single base resume; deferred |
| Blocking on guard warnings | Guards are advisory, never abort pipeline |
| `--diff` opt-in flag | Always-on with TTY guard is simpler; no flag to remember |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GUARD-01 | Phase 4 | In Progress (04-01 complete — wiring in 04-02) |
| GUARD-02 | Phase 4 | In Progress (04-01 complete — wiring in 04-02) |
| GUARD-03 | Phase 4 | In Progress (04-01 complete — wiring in 04-02) |
| GUARD-04 | Phase 4 | In Progress (04-01 complete — wiring in 04-02) |
| DIFF-01 | Phase 5 | Complete |
| DIFF-02 | Phase 5 | Complete |
| DIFF-03 | Phase 5 | Complete |
| PIPE-01 | Phase 6 | Complete |
| PIPE-02 | Phase 6 | Complete |
| PIPE-03 | Phase 6 | Complete |
| PIPE-04 | Phase 6 | Complete |
| MATCH-01 | Phase 7 | Pending |
| MATCH-02 | Phase 7 | Pending |
| MATCH-03 | Phase 7 | Pending |
| TEST-01 | Phase 8 | Complete |
| TEST-02 | Phase 8 | Complete |
| TEST-03 | Phase 8 | Complete |
| TEST-04 | Phase 9 | Complete |
| TEST-05 | Phase 9 | Complete |
| TEST-06 | Phase 9 | Complete |
| TEST-07 | Phase 9 | Complete |
| TEST-08 | Phase 10 | Pending |
| TEST-09 | Phase 10 | Pending |
| TEST-10 | Phase 11 | Pending |
| TEST-11 | Phase 11 | Pending |

**Coverage:**

- v1.1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-02*
*Last updated: 2026-06-02 after merging test coverage into v1.1*
