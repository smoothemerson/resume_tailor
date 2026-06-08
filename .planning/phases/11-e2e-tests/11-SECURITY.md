---
phase: 11
slug: e2e-tests
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-08
---

# Phase 11 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| test process → child process | subprocess.run spawns cli.py as a child; stdin is controlled literal strings, not user input | Hardcoded test strings only — no user-supplied data crosses this boundary |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-11-01 | Tampering | CLI_PATH derivation | accept | CLI_PATH derived from `__file__` (not user input); off-by-one in `parents[]` index would cause FileNotFoundError at test runtime, not a security risk | closed |
| T-11-SC | Tampering | npm/pip/cargo installs | accept | No new packages installed in this phase; stdlib + existing pytest only | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-11-01 | T-11-01 | CLI_PATH derivation uses `__file__` which is a trusted interpreter value, not user-controlled input. Any misconfiguration results in a test failure (FileNotFoundError), not a security breach. Risk is bounded to the test process. | Emerson Faria | 2026-06-08 |
| AR-11-02 | T-11-SC | Phase 11 adds no new dependencies — only stdlib modules (`subprocess`, `sys`, `os`, `re`) and the already-pinned `pytest` are used. Supply-chain risk is unchanged from prior phases. | Emerson Faria | 2026-06-08 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-08 | 2 | 2 | 0 | gsd-secure-phase (short-circuit: plan-time dispositions verified) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-08
