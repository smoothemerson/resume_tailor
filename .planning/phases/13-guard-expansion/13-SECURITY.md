---
phase: 13
slug: guard-expansion
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-12
---

# Phase 13 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| LLM output → run_guards() | Strings produced by Ollama flow into run_guards() and both new guards (_check_technology_substitution, _check_protected_sections) | Untrusted string content; no PII beyond what is already on disk |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-01 | Denial of Service | `_check_technology_substitution` | mitigate | `try/except Exception` wrapper (lines 58–74 guards.py); guard never raises; exception logged as warning | closed |
| T-13-02 | Tampering | `guards.py` — `_EMPLOYER_PATTERN`, section extraction | accept | Pure text comparison; no state mutation; no external calls; output is `logger.warning()` only | closed |
| T-13-03 | Denial of Service | `_check_protected_sections` | mitigate | `try/except Exception` wrapper (lines 77–107 guards.py); guard never raises; exception logged as warning | closed |
| T-13-04 | Tampering | `_check_protected_sections` — contact block and section comparison | accept | Pure read-only text comparison; no state mutation; no external calls; output is `logger.warning()` only | closed |
| T-13-05 | Information Disclosure | `logger.warning()` outputs | accept | Warnings written to local log only (log_manager); no external sink; PII in resume is already on disk | closed |
| T-13-06 | Denial of Service | `run_guards()` dispatch to new guards | mitigate | Each new guard has its own `try/except Exception` wrapper (T-13-01, T-13-03); exception caught inside guard; `run_guards()` itself is never interrupted | closed |
| T-13-07 | Tampering | `run_guards()` call order | accept | Guards are stateless; execution order does not affect correctness; no shared mutable state between guards | closed |
| T-13-SC | Tampering | npm/pip/cargo supply chain | accept | No new packages installed in Phase 13; all implementation uses stdlib `re` + existing project deps | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-13-01 | T-13-02 | Guard performs pure text comparison on already-on-disk data; no mutation or external calls. Risk surface is negligible. | Emerson Faria | 2026-06-12 |
| AR-13-02 | T-13-04 | Guard performs pure read-only text comparison; no state mutation or external calls. Risk surface is negligible. | Emerson Faria | 2026-06-12 |
| AR-13-03 | T-13-05 | Log warnings are emitted to the local log_manager only. Resume PII is already stored on disk; no new exposure path introduced. | Emerson Faria | 2026-06-12 |
| AR-13-04 | T-13-07 | Guards are individually stateless; call order in run_guards() is irrelevant to correctness or security. | Emerson Faria | 2026-06-12 |
| AR-13-05 | T-13-SC | Phase 13 introduces zero new packages. All new code uses stdlib `re` and existing project dependencies. | Emerson Faria | 2026-06-12 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-12 | 8 | 8 | 0 | gsd-security-auditor (automated — workflow short-circuit: register_authored_at_plan_time: true, threats_open: 0) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-12
