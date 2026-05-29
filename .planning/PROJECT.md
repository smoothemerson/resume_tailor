# Resume Tailor CLI

## What This Is

A Python CLI tool that reads a LaTeX resume, accepts a job description via terminal input, and uses a local Ollama LLM to produce a tailored LaTeX resume aligned with the job requirements. Built for personal use (tailoring an AI engineer's own resume) and as a portfolio piece showcasing practical LLM tooling skills.

## Core Value

Given a job description, produce a ready-to-compile LaTeX resume that is genuinely better aligned with that job — not just syntactically valid but actually usable.

## Requirements

### Validated

- [x] Call local Ollama model via REST API using only `requests` — Validated in Phase 2: LLM Integration
- [x] Handle file-not-found and Ollama connection errors explicitly — Validated in Phase 2: LLM Integration
- [x] System prompt preserves LaTeX structure, rewrites summary/skills/bullets, forbids hallucinated experiences — Validated in Phase 2: LLM Integration
- [x] Accept multiline job description via terminal (END/EOF to submit) — Validated in Phase 3: CLI Wiring
- [x] Print progress message before LLM call, success message with absolute path on completion — Validated in Phase 3: CLI Wiring
- [x] RuntimeError/ValueError from LLM client caught at CLI boundary, printed to stderr, exit 1, no traceback — Validated in Phase 3: CLI Wiring
- [x] Read base resume from configurable .tex file path via config.py — Validated in Phase 3: CLI Wiring
- [x] Write tailored output to timestamped .tex file — Validated in Phase 3: CLI Wiring

### Active

_(No active requirements — all core requirements validated through Phase 3)_

### Out of Scope

- LangChain or other LLM frameworks — keep deps to stdlib + requests only
- Web server or GUI — CLI only
- Auto-compilation to PDF — user runs pdflatex themselves
- Hallucination guardrail beyond prompt — diff review step deferred to later
- Multi-resume management — single base resume for now

## Context

**v1.0 shipped 2026-05-29 — tool is end-to-end functional**

- Directory: `en-cv-ai-engineer` — this is the owner's own AI engineer resume
- Base `.tex` resume exists at `resumes/english.tex`; config.py points to it via Path(__file__) anchoring
- Ollama must be running locally before execution; tool health-checks at startup and fails fast
- Default model: `mistral-small3.2:24b` — swappable by changing `OLLAMA_MODEL` in config.py
- Output: timestamped `.tex` files under `resumes/output/`; user compiles with pdflatex
- Tech stack: Python 3.11+, requests>=2.32.0, hatchling build backend, uv packaging, pytest dev dep
- Codebase: 8 Python files, ~429 LOC, 73 commits; installable via `uv tool install .`
- 16 unit tests (llm_client_test.py: 11, cli_test.py: 5) cover all safety guard behavioral contracts
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
*Last updated: 2026-05-29 after v1.0 milestone — all core requirements validated, tool shipped*
