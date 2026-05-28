# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-28
**Phase:** 1-Foundation
**Areas discussed:** Default resume, pyproject.toml name, Default model

---

## Default Resume

| Option | Description | Selected |
|--------|-------------|----------|
| english.tex | resumes/english.tex — most job postings you'll target are likely in English | ✓ |
| portuguese.tex | resumes/portuguese.tex — if most near-term applications are in Portuguese | |

**User's choice:** english.tex
**Notes:** No additional context provided.

---

## pyproject.toml Name

| Option | Description | Selected |
|--------|-------------|----------|
| Keep "en-cv-ai-engineer" | Preserves repo identity as a resume project; CLI entry point still works | |
| Rename to "resume-tailor" | Aligns package name with CLI command; cleaner as a portfolio artifact | ✓ |

**User's choice:** Rename to "resume-tailor"
**Notes:** No additional context provided.

---

## Default Model

| Option | Description | Selected |
|--------|-------------|----------|
| mistral | Strong at following structured output instructions — less likely to add prose or markdown fences | |
| llama3 | Solid general capability but can be chattier | |
| You decide | Pick whichever is most sensible — swappable via config | |
| mistral-small3.2:24b (Other) | Specific model variant provided by user | ✓ |

**User's choice:** `mistral-small3.2:24b` (free-text input)
**Notes:** User specified a precise model string rather than a generic alias.

---

## Claude's Discretion

- Package layout: flat (`resume_tailor/` at project root, not `src/resume_tailor/`)
- `requires-python` stays at `>=3.13` (already set in existing pyproject.toml)

## Deferred Ideas

None.
