---
phase: 10
slug: integration-tests
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-07
---

# Phase 10 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| test process → localhost:11434 | Test code makes outbound HTTP GET/POST to Ollama on loopback; response is LLM-generated LaTeX string | LLM-generated LaTeX (non-sensitive, local only) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-10-01 | Tampering | test inputs (MINIMAL_RESUME, MINIMAL_JD) | accept | Inputs are hardcoded string constants in the test file; no user-controlled data reaches the test layer; no injection surface | closed |
| T-10-02 | Information Disclosure | LLM response content in test output | accept | LLM output is printed only on test failure; contains no PII; local dev tool with no sensitive data | closed |
| T-10-03 | Denial of Service | 300-second read timeout per TEST-09 | accept | Intentional — TIMEOUT=(10,300) is the production config; overriding it in tests would mask real behavior; single test call, not a loop | closed |
| T-10-SC | Tampering | npm/pip/cargo installs | accept | No new packages installed in this phase; Package Legitimacy Audit confirmed empty in RESEARCH.md | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-10-01 | T-10-01 | Test inputs are hardcoded constants with no user-controlled data path; injection surface does not exist in the test layer | gsd-secure-phase | 2026-06-07 |
| AR-10-02 | T-10-02 | LLM output is local dev data, non-PII, printed only on failure; no confidentiality risk in a single-user offline tool | gsd-secure-phase | 2026-06-07 |
| AR-10-03 | T-10-03 | 300s timeout is intentional production-fidelity design; masking it would invalidate the test's purpose; single call, no loop | gsd-secure-phase | 2026-06-07 |
| AR-10-SC | T-10-SC | Zero new dependencies introduced in this phase; supply-chain risk is nil | gsd-secure-phase | 2026-06-07 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-07 | 4 | 4 | 0 | gsd-secure-phase (short-circuit: threats_open=0, register_authored_at_plan_time=true) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-07
