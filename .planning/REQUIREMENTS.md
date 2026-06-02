# Requirements: Resume Tailor CLI

**Defined:** 2026-06-02
**Core Value:** Given a job description, produce a ready-to-compile LaTeX resume that is genuinely better aligned with that job — not just syntactically valid but actually usable.

## v1.1 Requirements

Requirements for Output Quality milestone. Each maps to roadmap phases.

### Output Guards

- [ ] **GUARD-01**: Tool warns when a section present in the original resume is missing from the tailored output
- [ ] **GUARD-02**: Tool warns when tailored output contains markdown prose or other format violations (LaTeX-only rule broken)
- [ ] **GUARD-03**: Tool warns when structured fields (employer names, dates, skills tokens) appear in output but were not in original resume
- [ ] **GUARD-04**: Guards degrade gracefully — any guard failure prints a warning to stderr but does not block the output write

### Diff View

- [ ] **DIFF-01**: Tool shows a normalized unified diff of original vs tailored resume after tailoring, when stdout is a TTY
- [ ] **DIFF-02**: Diff is suppressed automatically when stdout is piped or redirected (no flag required)
- [ ] **DIFF-03**: Diff normalization eliminates whitespace-only noise (trailing space, blank line collapsing) so only meaningful changes appear

### Two-Pass Pipeline

- [ ] **PIPE-01**: Tool performs a JD analysis pass (pass 1) before the tailoring call — extracts key technologies, role requirements, and emphasis areas from the job description
- [ ] **PIPE-02**: Analysis output is injected into the tailoring prompt (pass 2) to guide section-specific rewrites
- [ ] **PIPE-03**: If pass 1 fails (malformed output, parse error), tool falls back to single-pass behavior — no abort, no error surfaced to user
- [ ] **PIPE-04**: Both LLM calls respect existing done_reason truncation guard

### JD Match Summary

- [ ] **MATCH-01**: After tailoring, tool displays which keywords from pass 1's analysis appear in the tailored resume
- [ ] **MATCH-02**: Keyword matching uses whole-word regex with stop word filtering to prevent substring false positives
- [ ] **MATCH-03**: Match summary is displayed to stdout only when running interactively (TTY guard, same as diff)

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
| GUARD-01 | Phase 4 | Pending |
| GUARD-02 | Phase 4 | Pending |
| GUARD-03 | Phase 4 | Pending |
| GUARD-04 | Phase 4 | Pending |
| DIFF-01 | Phase 5 | Pending |
| DIFF-02 | Phase 5 | Pending |
| DIFF-03 | Phase 5 | Pending |
| PIPE-01 | Phase 6 | Pending |
| PIPE-02 | Phase 6 | Pending |
| PIPE-03 | Phase 6 | Pending |
| PIPE-04 | Phase 6 | Pending |
| MATCH-01 | Phase 7 | Pending |
| MATCH-02 | Phase 7 | Pending |
| MATCH-03 | Phase 7 | Pending |

**Coverage:**
- v1.1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-02*
*Last updated: 2026-06-02 after initial v1.1 definition*
