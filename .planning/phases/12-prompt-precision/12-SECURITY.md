---
phase: 12
slug: prompt-precision
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-11
---

# Phase 12 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| LLM prompt string -> Ollama API | The system prompt is a string literal sent to the local Ollama endpoint; it is not parsed by any runtime code in this project | Prompt text (resume content + job description); no secrets or PII beyond user's own resume; localhost-only HTTP |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-12-01 | Tampering | system_prompt string in _build_messages() | accept | String literal in source-controlled Python file; no injection surface — the prompt is read by the LLM, not executed | closed |
| T-12-02 | Information Disclosure | system_prompt content | accept | No PII or secrets in the prompt; Ollama is localhost-only; low-value target | closed |
| T-12-SC | Tampering (supply chain) | npm/pip/cargo installs | accept | No packages installed in this phase — pure string edit, no dependency changes | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-12-01 | T-12-01 | Prompt is a source-controlled string literal consumed only by the LLM; no runtime parsing or execution path exists for injected content | plan-time threat model (12-01-PLAN.md) | 2026-06-11 |
| R-12-02 | T-12-02 | Prompt contains no PII or secrets; Ollama endpoint is localhost-only and offline-first by project constraint | plan-time threat model (12-01-PLAN.md) | 2026-06-11 |
| R-12-03 | T-12-SC | Phase made no dependency changes — pure string-literal edit confirmed by SUMMARY (files modified: src/llm_client.py only) | plan-time threat model (12-01-PLAN.md) | 2026-06-11 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-11 | 3 | 3 | 0 | gsd-secure-phase (short-circuit: plan-time register, all dispositions accepted, SUMMARY threat flags: none) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-11
