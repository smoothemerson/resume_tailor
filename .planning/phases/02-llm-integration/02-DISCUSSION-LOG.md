# Phase 2: LLM Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-28
**Phase:** 2-LLM Integration
**Areas discussed:** System prompt content, generate_tailored_resume() contract, Health check wiring, log_manager vs print

---

## System Prompt Content

### Q1: Rewrite scope

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite: summary + skills + bullets only | Rewrites professional summary, skills section, and experience bullet points. Everything else preserved exactly. | ✓ |
| Rewrite: all non-factual sections | Broader rewrite including section ordering/emphasis. Higher tailoring potential but more drift risk. | |
| You decide | Leave to planner/researcher. | |

**User's choice:** Rewrite summary + skills + bullets only
**Notes:** Safest approach — minimizes hallucination risk.

### Q2: No-hallucination guardrail phrasing

| Option | Description | Selected |
|--------|-------------|----------|
| Hard prohibition: exact text | Explicit "do not invent..." prohibition. | |
| Preservation framing | Frame as preservation rule: "only reword existing content." | |
| Both: prohibition + preservation | Combine both approaches for a stronger guardrail. | ✓ |

**User's choice:** Both prohibition + preservation
**Notes:** Stronger guardrail is worth the slightly longer system prompt.

### Q3: LaTeX-only output enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit instruction + example | Tells the LLM the exact format with structural markers it must produce. | ✓ |
| Instruction only (no example) | Shorter, relies on QUAL-01/QUAL-02 as backstops. | |
| You decide | Leave to planner. | |

**User's choice:** Explicit instruction + example
**Notes:** State the structural markers (\documentclass ... \end{document}) explicitly.

### Q4: Resume owner context in system prompt

| Option | Description | Selected |
|--------|-------------|----------|
| Generic — no persona context | Stays generic, works for any resume/domain. | ✓ |
| Domain-aware — mention AI engineering context | Hint that this is an AI/ML engineer's resume. | |
| You decide | Leave to planner. | |

**User's choice:** Generic — no persona context

---

## generate_tailored_resume() Contract

### Q1: Return value

| Option | Description | Selected |
|--------|-------------|----------|
| LaTeX string only | Returns validated LaTeX content as a string. Phase 3 writes file. | ✓ |
| File path after writing | llm_client.py writes file internally, returns Path. | |

**User's choice:** LaTeX string only
**Notes:** Aligns with "exception catches at main.py boundary only" decision. Single responsibility.

### Q2: Function parameters

| Option | Description | Selected |
|--------|-------------|----------|
| generate_tailored_resume(resume_text, job_description) | Model and URL read from config.py inside function. | ✓ |
| generate_tailored_resume(resume_text, job_description, model, base_url) | More flexible but adds parameters the CLI never needs to vary. | |

**User's choice:** generate_tailored_resume(resume_text, job_description)

---

## Health Check Wiring

### Q1: Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Inside generate_tailored_resume() | Runs automatically, caller cannot forget. | ✓ |
| Separate check_ollama_health() function | More testable in isolation, more Phase 3 surface. | |

**User's choice:** Inside generate_tailored_resume()
**Notes:** Simplicity wins — the function is the single entry point.

---

## log_manager vs print

### Q1: Which pattern for llm_client.py

| Option | Description | Selected |
|--------|-------------|----------|
| Follow CLAUDE.md: print to stderr, remove log_manager | Consistent with project conventions; removes untracked file. | |
| Follow resume_reader.py: use log_manager throughout | Consistent with existing module; commits log_manager.py as real code. | ✓ |

**User's choice:** Follow resume_reader.py — use log_manager throughout
**Notes:** CLAUDE.md "no logging module" was aspirational. Actual code pattern wins. log_manager.py will be committed.

---

## Claude's Discretion

- Internal module structure (whether to split into private helper functions like `_build_messages()`, `_strip_fences()`, `_validate_latex()`)
- Exact wording and sentence ordering of the system prompt beyond locked behavioral rules
- Exception types for each failure mode (RuntimeError vs ValueError vs ConnectionError) — must be raise-able, not sys.exit

## Deferred Ideas

None — discussion stayed within phase scope
