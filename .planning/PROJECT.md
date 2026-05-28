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

### Active

- [ ] Read base resume from a configurable .tex file path
- [ ] Accept multiline job description via terminal (END to submit)
- [ ] Call local Ollama model via REST API using only `requests`
- [ ] System prompt preserves LaTeX structure, rewrites summary/skills/bullets, forbids hallucinated experiences
- [ ] Write tailored output to `resumes/output/tailored_resume_YYYYMMDD_HHMMSS.tex`
- [ ] Print success message with output file path
- [ ] Handle file-not-found and Ollama connection errors explicitly
- [ ] Model and paths configurable via `config.py` without touching other files

### Out of Scope

- LangChain or other LLM frameworks — keep deps to stdlib + requests only
- Web server or GUI — CLI only
- Auto-compilation to PDF — user runs pdflatex themselves
- Hallucination guardrail beyond prompt — diff review step deferred to later
- Multi-resume management — single base resume for now

## Context

- Directory: `en-cv-ai-engineer` — this is the owner's own AI engineer resume
- Base `.tex` resume already exists; the project only needs to wrap tooling around it
- Ollama must be running locally before execution; no daemon management needed
- Target models: mistral or llama3 first; model is swappable via config
- Output is raw `.tex` — pdflatex or equivalent handles compilation
- Project doubles as a portfolio artifact: code quality and structure matter

## Constraints

- **Dependencies**: stdlib + `requests` only — no LangChain, no heavy frameworks; keeps the tool auditable and dependency-light
- **Runtime**: Ollama running locally at `http://localhost:11434` — tool is offline-first by design
- **Output format**: Raw LaTeX only — model must return valid `.tex`, no markdown fences or prose

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| requests over LangChain | Keeps deps minimal, code readable, no abstraction overhead for a single API call | — Pending |
| Ollama REST API directly | No SDK dependency; /api/generate or /api/chat is stable and simple | — Pending |
| Timestamped output filenames | Prevents overwrites, preserves history of tailored versions | — Pending |
| System prompt as guardrail | Simplest approach; diff review can be added later without changing architecture | — Pending |

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
*Last updated: 2026-05-28 after Phase 2: LLM Integration complete*
