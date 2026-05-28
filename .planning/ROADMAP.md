# Roadmap: Resume Tailor CLI

## Overview

Three phases deliver a working CLI tool: Phase 1 builds the pure file I/O foundation (config, reader, writer, packaging) that can be tested without Ollama running. Phase 2 integrates the LLM — the highest-risk module — with all output safety guards built in from the start. Phase 3 wires the full flow together in main.py and delivers the end-to-end working tool.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffold, config, file I/O modules, and packaging — testable without Ollama
- [x] **Phase 2: LLM Integration** - llm_client.py with Ollama health check, API call, all output safety guards (completed 2026-05-28)
- [ ] **Phase 3: CLI Wiring** - main.py orchestration, multiline JD input, progress message, end-to-end working tool

## Phase Details

### Phase 1: Foundation

**Goal**: The project scaffold, configuration, file I/O, and packaging are in place and verifiable without Ollama running
**Depends on**: Nothing (first phase)
**Requirements**: CONF-01, CONF-02, PKG-01, CORE-01, CORE-05, ERR-01
**Success Criteria** (what must be TRUE):

  1. Running `resume-tailor --help` (after `uv tool install .`) produces a usage message without error
  2. `config.py` constants are importable and all paths resolve correctly regardless of which directory the tool is invoked from
  3. Given a valid `.tex` file path, the reader returns the file content as a string
  4. Given LaTeX content, the writer creates a timestamped `.tex` file under `resumes/output/` (creating the directory if it does not exist)
  5. If the base resume file is missing, the tool prints a human-readable error to stderr and exits with code 1 — no raw traceback

**Plans**: 2 plans

**Wave 1**

- [x] 01-01-PLAN.md — Create resume_tailor package: config.py (D-01/D-02/D-03), resume_reader.py (CORE-01/ERR-01), resume_writer.py (CORE-05), __init__.py, cli.py stub

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Update pyproject.toml with [build-system] + [project.scripts] + dependencies; verify `uv tool install .` registers the resume-tailor command (PKG-01)

### Phase 2: LLM Integration

**Goal**: llm_client.py can call Ollama, validate its response, and return safe LaTeX content — or fail with a clear error
**Depends on**: Phase 1
**Requirements**: CORE-04, QUAL-01, QUAL-02, QUAL-03, QUAL-04, ERR-02, ERR-03
**Success Criteria** (what must be TRUE):

  1. If Ollama is not running at startup, the tool fails fast with a clear "Ollama not reachable" message before attempting any LLM call
  2. A call to `generate_tailored_resume()` with valid inputs reaches Ollama using `/api/chat` with `stream: false`, `num_ctx: 8192`, and `timeout=(10, 300)`
  3. Any markdown code fences in the LLM response are stripped unconditionally before further processing
  4. If the response does not contain `\documentclass` and `\end{document}`, the function raises an error and no file is written
  5. If `done_reason` is `"length"`, the function aborts with a clear truncation error and no file is written

**Plans**: 1 plan

**Wave 1**

- [x] 02-01-PLAN.md — Create src/llm_client.py: Ollama health check (ERR-03), /api/chat call (CORE-04), fence stripping (QUAL-01), LaTeX validation (QUAL-02), done_reason check (QUAL-03), XML delimiter wrapping (QUAL-04), exception handling (ERR-02)

### Phase 3: CLI Wiring

**Goal**: Users can run the complete tool end-to-end — input a job description, receive a tailored LaTeX resume file
**Depends on**: Phase 2
**Requirements**: CORE-02, CORE-03, CORE-06
**Success Criteria** (what must be TRUE):

  1. Running `resume-tailor` prompts the user to paste a job description, accepts multiple lines, and submits when the user types END on a new line (or sends EOF)
  2. After job description submission, a progress message appears before the LLM call starts so the terminal does not appear frozen
  3. On success, the tool prints the full absolute path of the written `.tex` file and exits with code 0

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete    | 2026-05-28 |
| 2. LLM Integration | 1/1 | Complete    | 2026-05-28 |
| 3. CLI Wiring | 0/TBD | Not started | - |
