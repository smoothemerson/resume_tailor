---
phase: "08"
slug: test-infrastructure
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-04
---

# Phase 08 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| pyproject.toml → pytest | pytest reads ini options from pyproject.toml at startup; values accepted without validation | pytest config values (no sensitive data) |
| tests/conftest.py → localhost:11434 | Single read-only HTTP GET to Ollama health endpoint; no user-controlled input | Health check result (boolean only) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-08-01 | Tampering | pyproject.toml addopts | accept | Local dev config; changes visible in git diff; no external input; low-value target | closed |
| T-08-02 | Information Disclosure | testpaths in pyproject.toml | accept | Exposes src/ layout intentionally; already public in repo; no secrets involved | closed |
| T-08-03 | Information Disclosure | ollama_available fixture | accept | Probes localhost only; intended behavior for local test runner; reveals no sensitive data | closed |
| T-08-04 | Denial of Service | ollama_available fixture hang | mitigate | `timeout=3` on `requests.get` at `tests/conftest.py:9` — prevents test session hang if Ollama is slow | closed |
| T-08-05 | Spoofing | OLLAMA_BASE_URL source | accept | URL imported from `config.py`; single source of truth; attacker would need repo write access | closed |
| T-08-SC | Tampering | supply chain (installs) | accept | No new packages installed; all deps (pytest, requests) are existing verified dev dependencies | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-08-01 | T-08-01 | pyproject.toml addopts is a local dev config with no external input; all changes are git-tracked | Emerson Faria | 2026-06-04 |
| AR-08-02 | T-08-02 | src/ layout exposure is intentional; repository is not a secret; no sensitive data exposed | Emerson Faria | 2026-06-04 |
| AR-08-03 | T-08-03 | Localhost-only Ollama health probe reveals only runtime availability to the local test runner | Emerson Faria | 2026-06-04 |
| AR-08-05 | T-08-05 | OLLAMA_BASE_URL sourced exclusively from config.py; no user input path; requires repo write access to alter | Emerson Faria | 2026-06-04 |
| AR-08-SC | T-08-SC | No new packages installed in this phase; pytest and requests are existing verified dev dependencies | Emerson Faria | 2026-06-04 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-04 | 6 | 6 | 0 | gsd-security-auditor (short-circuit: all plan-time threats verified closed) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-04
