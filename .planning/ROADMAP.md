# Roadmap: Resume Tailor CLI

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-05-29)
- 🚧 **v1.1 Output Quality + Test Coverage** — Phases 4-11 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-05-29</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-05-28
- [x] Phase 2: LLM Integration (1/1 plan) — completed 2026-05-28
- [x] Phase 3: CLI Wiring (1/1 plan) — completed 2026-05-29

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Output Quality + Test Coverage (In Progress)

**Milestone Goal:** Upgrade the tailoring pipeline to produce measurably better output — with visible feedback, stronger JD-targeting, and guards against common LLM failures — then validate the full codebase with a complete unit/integration/e2e test pyramid.

- [x] **Phase 4: Output Reliability Guards** - Warn users when the tailored output drops sections, introduces hallucinated fields, or violates LaTeX-only format constraints (completed 2026-06-02)
- [ ] **Phase 5: Diff View** - Show a normalized unified diff between original and tailored resume on interactive terminals
- [ ] **Phase 6: Two-Pass Pipeline** - Restructure LLM calls to perform a JD analysis pass before tailoring, injecting extracted requirements into the tailoring prompt
- [ ] **Phase 7: JD Keyword Match Summary** - After tailoring, display which JD keywords from the analysis pass appear in the tailored resume
- [x] **Phase 8: Test Infrastructure** - Configure pytest, create conftest.py with Ollama fixtures, and establish tests/ directory layout (completed 2026-06-02)
- [x] **Phase 9: Unit Test Gaps** - Cover _build_messages(), _check_ollama_health(), reader, and writer modules with isolated unit tests (completed 2026-06-04)
- [ ] **Phase 10: Integration Tests** - Verify real Ollama health check and generate call with structural assertions; skipable when Ollama is absent
- [ ] **Phase 11: E2E Tests** - Verify full CLI subprocess invocation — error paths without Ollama, golden path with Ollama

## Phase Details

### Phase 4: Output Reliability Guards

**Goal**: Users receive warnings when the tailored resume silently drops content, introduces hallucinated fields, or breaks LaTeX formatting — without ever blocking the output file from being written
**Depends on**: Phase 3 (v1.0 CLI Wiring)
**Requirements**: GUARD-01, GUARD-02, GUARD-03, GUARD-04
**Success Criteria** (what must be TRUE):

  1. Running the tool against a JD that causes a section to be dropped prints a warning to stderr identifying the missing section
  2. Running the tool when the LLM returns markdown fences or prose before `\documentclass` prints a format violation warning to stderr
  3. Running the tool when the LLM introduces employer names or dates not in the original resume prints a hallucination warning to stderr
  4. All guard warnings are non-fatal — the tailored `.tex` file is written to disk regardless of how many warnings fire

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 04-01-PLAN.md — TailorResult refactor in llm_client.py + create guards.py with run_guards() — COMPLETE 2026-06-02

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02-PLAN.md — Wire run_guards into cli.py + create guards_test.py unit test suite — COMPLETE 2026-06-02

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-03-PLAN.md — Update cli_test.py mocks for TailorResult + full suite green gate — COMPLETE 2026-06-02

### Phase 5: Diff View

**Goal**: Users can immediately see what changed between their original resume and the tailored version without opening two files in an editor — and the output stays clean when the tool is used in scripts or pipelines
**Depends on**: Phase 4
**Requirements**: DIFF-01, DIFF-02, DIFF-03
**Success Criteria** (what must be TRUE):

  1. Running the tool in an interactive terminal prints a unified diff of original vs tailored resume after the file is written
  2. Running the tool with stdout piped or redirected produces no diff output — the file is still written normally
  3. The diff omits trailing-space and blank-line-only changes so only semantically meaningful edits are visible

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 05-01-PLAN.md — Create src/diff_view.py module + unit tests + pyproject.toml wheel include (DIFF-01, DIFF-02, DIFF-03)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 05-02-PLAN.md — Wire show_diff() into cli.py + update cli_test.py (DIFF-01, DIFF-02, DIFF-03)

### Phase 6: Two-Pass Pipeline

**Goal**: The tailoring call is guided by an explicit machine-extracted understanding of the job description — key technologies, role requirements, and emphasis areas are extracted in a first LLM pass and injected into the tailoring prompt — with the existing single-pass behavior preserved as a fallback
**Depends on**: Phase 5
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04
**Success Criteria** (what must be TRUE):

  1. Providing a JD results in the tool making two LLM calls — one analysis call and one tailoring call — visible via progress messages
  2. The tailoring call's prompt contains the extracted JD requirements from the analysis call
  3. When the analysis call produces malformed or unparseable output, the tool falls back silently to single-pass behavior and still produces a tailored resume
  4. Both LLM calls are protected by the existing truncation guard — a `done_reason: length` response on either call triggers the same error path as today

**Plans**: TBD
**UI hint**: no

### Phase 7: JD Keyword Match Summary

**Goal**: Users see a post-tailoring summary of which JD-extracted keywords appear in the tailored resume, giving a measurable signal of alignment quality — visible only in interactive terminal sessions
**Depends on**: Phase 6
**Requirements**: MATCH-01, MATCH-02, MATCH-03
**Success Criteria** (what must be TRUE):

  1. After tailoring completes in an interactive terminal, a keyword match summary is printed showing which extracted JD keywords appear in the tailored resume
  2. The match summary is suppressed when stdout is piped or redirected
  3. Keywords are matched as whole words and common stop words are excluded — searching for "and" or "the" does not produce false positives

**Plans**: TBD

### Phase 8: Test Infrastructure

**Goal**: pytest is fully configured and the tests/ directory hierarchy is in place — markers registered, imports work without sys.path hacks, and the Ollama skip fixture is available to all test layers
**Depends on**: Phase 7
**Requirements**: TEST-01, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):

  1. Running `pytest --co` (collect-only) discovers all existing 18 unit tests in `src/` plus the new empty test directories with no warnings
  2. Running `pytest -m integration` when Ollama is down exits 0 with all integration tests shown as SKIPPED, not FAILED
  3. Running `pytest -m foo` (unknown marker) exits non-zero immediately due to `--strict-markers`

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 08-01-PLAN.md — Configure pytest in pyproject.toml (TEST-01)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-02-PLAN.md — Create tests/ scaffold, conftest.py fixtures, and remove sys.path hacks (TEST-02, TEST-03)

### Phase 9: Unit Test Gaps

**Goal**: Every untested function in the existing codebase has at least one unit test — `_build_messages()`, `_check_ollama_health()`, `read_resume()`, and `write_resume()` — all mocked, all fast
**Depends on**: Phase 8
**Requirements**: TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):

  1. `pytest -m unit tests/unit/` passes in under 2 seconds with zero Ollama dependency
  2. `_build_messages()` tests verify the 2-message structure, role ordering, and XML tag presence without asserting prompt prose
  3. `write_resume()` test uses `tmp_path` and asserts filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex` pattern
  4. `_check_ollama_health()` Timeout path is covered (not just ConnectionError)

**Plans**: 2 plans
Plans:
**Wave 1** *(both plans parallel — no shared files)*

- [x] 09-01-PLAN.md — Create tests/unit/test_llm_client.py covering _build_messages and _check_ollama_health (TEST-04, TEST-05)
- [x] 09-02-PLAN.md — Create tests/unit/test_resume_reader.py and test_resume_writer.py (TEST-06, TEST-07)

### Phase 10: Integration Tests

**Goal**: A real Ollama call is made in CI and the integration layer verifies structural invariants — the response is valid LaTeX, not just that no exception was raised
**Depends on**: Phase 9
**Requirements**: TEST-08, TEST-09
**Success Criteria** (what must be TRUE):

  1. `pytest -m integration` with Ollama running passes — response starts with `\documentclass`, ends with `\end{document}`, contains no markdown fences
  2. `pytest -m integration` with Ollama stopped shows SKIPPED for all integration tests with a clear skip reason; exit code is 0
  3. Integration tests use a minimal inline fixture resume (not `english.tex`) to minimize inference time

**Plans**: TBD

### Phase 11: E2E Tests

**Goal**: The CLI can be invoked as a subprocess and the full user-visible behavior is verified — exit codes, output file creation, success message — including error paths that run without Ollama
**Depends on**: Phase 10
**Requirements**: TEST-10, TEST-11
**Success Criteria** (what must be TRUE):

  1. Empty-JD e2e test runs without Ollama and exits 1 with an error message on stderr
  2. Golden-path e2e test exits 0, creates a file in `tmp_path` (not `resumes/output/`), and stdout contains `"Tailored resume written to:"`
  3. `pytest -m e2e` with Ollama stopped skips the golden-path test and passes the error-path test

**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-05-28 |
| 2. LLM Integration | v1.0 | 1/1 | Complete | 2026-05-28 |
| 3. CLI Wiring | v1.0 | 1/1 | Complete | 2026-05-29 |
| 4. Output Reliability Guards | v1.1 | 3/3 | Complete    | 2026-06-04 |
| 5. Diff View | v1.1 | 1/2 | In Progress|  |
| 6. Two-Pass Pipeline | v1.1 | 0/? | Not started | - |
| 7. JD Keyword Match Summary | v1.1 | 0/? | Not started | - |
| 8. Test Infrastructure | v1.1 | 2/2 | Complete    | 2026-06-04 |
| 9. Unit Test Gaps | v1.1 | 2/2 | Complete   | 2026-06-04 |
| 10. Integration Tests | v1.1 | 0/? | Not started | - |
| 11. E2E Tests | v1.1 | 0/? | Not started | - |
