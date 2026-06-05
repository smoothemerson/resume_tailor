---
phase: 09
slug: unit-test-gaps
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-05
---

# Phase 09 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| test code → source code | Unit tests import and call internal functions directly — no new trust boundary introduced | None (test-only imports) |
| test code → filesystem | Tests write and read files via tmp_path — all confined to pytest's temp directory, auto-cleaned | Temporary fixture files, no sensitive data |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-09-01 | Tampering | tests/unit/test_llm_client.py | accept | Test-only file; no production code path; no security surface | closed |
| T-09-02 | Tampering | tests/unit/test_resume_reader.py | accept | Test-only file; reads from tmp_path only; no production path | closed |
| T-09-03 | Tampering | tests/unit/test_resume_writer.py | accept | Test-only file; writes to tmp_path only; no production path | closed |
| T-09-SC | Tampering | npm/pip/cargo installs | accept | No new packages installed in this plan; all dependencies already present in pyproject.toml | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-09-01 | T-09-01 | Test files introduce no new production attack surface; pytest isolation guarantees test code does not execute in production | plan-time | 2026-06-05 |
| AR-09-02 | T-09-02 | Test file reads only from pytest's tmp_path (auto-cleaned); no production data accessed | plan-time | 2026-06-05 |
| AR-09-03 | T-09-03 | Test file writes only to pytest's tmp_path (auto-cleaned); no production files written | plan-time | 2026-06-05 |
| AR-09-SC | T-09-SC | No new packages introduced; existing dependency surface unchanged | plan-time | 2026-06-05 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-05 | 4 | 4 | 0 | gsd-secure-phase (plan-time register, all accept) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-05
