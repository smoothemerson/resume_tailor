# Resume Tailor CLI

## What This Is

A Python CLI tool that reads a LaTeX resume, accepts a job description via terminal input, and uses a local Ollama LLM to produce a tailored LaTeX resume aligned with the job requirements. Built for personal use (tailoring an AI engineer's own resume) and as a portfolio piece showcasing practical LLM tooling skills.

## Core Value

Given a job description, produce a ready-to-compile LaTeX resume that is genuinely better aligned with that job — not just syntactically valid but actually usable.

## Current Milestone: v1.2 Precision & CI

**Goal:** Harden the LLM prompt with exact allowed/protected rules, expand output guards to catch technology substitution and protected-section mutations, fix a packaging gap, ship a CI pipeline, and fill remaining unit test gaps.

**Target features:**
- Update `_build_messages()` with explicit ALLOWED/PROTECTED section rules matching real resume LaTeX patterns
- New guard: `_check_technology_substitution` — warns when Skills section swaps technologies
- New guard: `_check_protected_sections` — warns if contact block, education, languages, employer headers, or project anchors are mutated
- Unit tests for both new guards in `guards_test.py`
- Fix pyproject.toml wheel include list (add `jd_analyzer.py`, `keyword_matcher.py`)
- GitHub Actions CI: ruff + `pytest -m unit` on push/PR to main
- Unit tests for `jd_analyzer`, `resume_reader`, `resume_writer`
- Remove `.claude/` from git tracking and add to `.gitignore`

## Requirements

### Validated

- [x] Call local Ollama model via REST API using only `requests` — Phase 2: LLM Integration
- [x] Handle file-not-found and Ollama connection errors explicitly — Phase 2: LLM Integration
- [x] System prompt preserves LaTeX structure, rewrites summary/skills/bullets, forbids hallucinated experiences — Phase 2: LLM Integration
- [x] Accept multiline job description via terminal (END/EOF to submit) — Phase 3: CLI Wiring
- [x] Print progress message before LLM call, success message with absolute path on completion — Phase 3: CLI Wiring
- [x] RuntimeError/ValueError from LLM client caught at CLI boundary, printed to stderr, exit 1, no traceback — Phase 3: CLI Wiring
- [x] Read base resume from configurable .tex file path via config.py — Phase 3: CLI Wiring
- [x] Write tailored output to timestamped .tex file — Phase 3: CLI Wiring
- [x] Tool warns when a section present in the original resume is missing from tailored output (GUARD-01) — Phase 4: Output Reliability Guards
- [x] Tool warns when tailored output contains markdown prose or format violations (GUARD-02) — Phase 4: Output Reliability Guards
- [x] Tool warns when structured fields appear in output but were not in original resume (GUARD-03) — Phase 4: Output Reliability Guards
- [x] Guards degrade gracefully — warnings to stderr, never block output write (GUARD-04) — Phase 4: Output Reliability Guards
- [x] Tool shows normalized unified diff of original vs tailored when stdout is a TTY (DIFF-01 to DIFF-03) — Phase 5: Diff View
- [x] Tool performs JD analysis pass before tailoring to extract key requirements (PIPE-01 to PIPE-04) — Phase 6: Two-Pass Pipeline
- [x] Tool displays JD keyword match summary after tailoring (MATCH-01 to MATCH-03) — Phase 7: JD Keyword Match Summary
- [x] pytest configured with testpaths, pythonpath, markers, --strict-markers (TEST-01) — Phase 8: Test Infrastructure
- [x] tests/conftest.py provides Ollama availability fixtures (TEST-02 to TEST-03) — Phase 8: Test Infrastructure
- [x] Unit tests cover _build_messages(), _check_ollama_health(), reader, writer (TEST-04 to TEST-07) — Phase 9: Unit Test Gaps
- [x] Integration tests verify real Ollama call with structural LaTeX assertions (TEST-08 to TEST-09) — Phase 10: Integration Tests
- [x] E2E tests verify CLI subprocess exit codes, output file, error paths (TEST-10 to TEST-11) — Phase 11: E2E Tests
- [x] pyproject.toml wheel include list ships `jd_analyzer.py` and `keyword_matcher.py` (PKG-01) — Phase 14: Infrastructure
- [x] GitHub Actions CI runs ruff + unit tests on push/PR to main (CI-01) — Phase 14: Infrastructure
- [x] Unit tests for `jd_analyzer`, `resume_reader`, `resume_writer` (TEST-14 to TEST-16) — Phase 14: Infrastructure
- [x] `.claude/` removed from git tracking, comprehensive Python .gitignore (REPO-01) — Phase 14: Infrastructure

### Active

- [ ] Update `_build_messages()` with precise ALLOWED/PROTECTED LaTeX rewriting rules
- [ ] Add `_check_technology_substitution` guard to `guards.py`
- [ ] Add `_check_protected_sections` guard to `guards.py`
- [ ] Unit tests for new guards in `guards_test.py`

### Out of Scope

- LangChain or other LLM frameworks — keep deps to stdlib + requests only
- Web server or GUI — CLI only
- Auto-compilation to PDF — user runs pdflatex themselves
- Hallucination guardrail beyond prompt — diff review step deferred to later
- Multi-resume management — single base resume for now

## Context

**v1.1 shipped 2026-06-08 — full test pyramid in place**

- Directory: `en-cv-ai-engineer` — this is the owner's own AI engineer resume
- Base `.tex` resume exists at `resumes/english.tex`; config.py points to it via Path(__file__) anchoring
- Ollama must be running locally before execution; tool health-checks at startup and fails fast
- Default model: `qwen3:14b` — swappable via `OLLAMA_MODEL` in config.py
- System prompt: structured XML prompt with Alexandra persona (surgeon-precise tailoring instructions)
- Pipeline: two-pass (JD analysis → tailoring with extracted requirements injected)
- Output: timestamped `.tex` files under `resumes/output/`; user compiles with pdflatex; diff shown on TTY
- Tech stack: Python 3.11+, requests>=2.32.0, hatchling build backend, uv packaging, pytest dev dep
- Codebase: ~12 Python source files + test suite; installable via `uv tool install .`
- Test coverage: 107 tests (63 unit in src/, 36 unit in tests/unit/, 2 integration, 2 e2e) — 3 skipped when Ollama absent
- Project doubles as a portfolio artifact: minimal deps, auditable code, clean separation of concerns

## Constraints

- **Dependencies**: stdlib + `requests` only — no LangChain, no heavy frameworks; keeps the tool auditable and dependency-light
- **Runtime**: Ollama running locally at `http://localhost:11434` — tool is offline-first by design
- **Output format**: Raw LaTeX only — model must return valid `.tex`, no markdown fences or prose

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| requests over LangChain | Keeps deps minimal, code readable, no abstraction overhead for a single API call | ✓ Good — clean single-file integration, zero framework overhead |
| /api/chat over /api/generate | Role-separated system/user messages maps directly to prompt strategy; cleaner than conflating into single string | ✓ Good — system prompt / user prompt separation worked well |
| Path(__file__) anchoring | Survives `uv tool install` where cwd is unrelated to package location | ✓ Good — critical for correct behavior post-install |
| raise-not-exit in llm_client | llm_client.py raises RuntimeError/ValueError; only cli.py calls sys.exit — keeps modules testable in isolation | ✓ Good — all 11 unit tests could mock freely without sys.exit side effects |
| hatchling build backend | PyPA-maintained, uv's default, required for `uv tool install .` to register shell command | ✓ Good — install worked on first try after adding [build-system] |
| Timestamped output filenames | Prevents overwrites, preserves history of tailored versions | ✓ Good — clean output; user can compare runs by timestamp |
| System prompt as guardrail | Simplest approach; diff review can be added later without changing architecture | ✓ Good — separating fence stripping and LaTeX validation as code guards (not prompt-only) was the right call |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-11 — Phase 14 complete: packaging fix, CI workflow, unit test gaps filled, .claude/ untracked*
