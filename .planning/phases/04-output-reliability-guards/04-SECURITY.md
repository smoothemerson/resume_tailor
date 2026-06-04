---
phase: 04-output-reliability-guards
slug: output-reliability-guards
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-04
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| LLM output → guard functions | Untrusted LLM-generated LaTeX string enters `_check_*` functions | Unvalidated text string |
| Guard functions → stderr | Warning strings derived from LLM content written to stderr | Low-sensitivity diagnostic messages |
| cli.py try block → run_guards | Untrusted LLM output (`result.content`) enters guard pipeline | Unvalidated LaTeX string |
| run_guards → write_resume | Pipeline continues to file write regardless of guard findings | Validated LaTeX string |
| test process → cli.main() | Tests invoke main() via mocked dependencies; no real I/O occurs | Mocked/fixture data only |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-04-01 | Tampering | TailorResult.fences_stripped computation | mitigate | `fences_stripped = raw.strip() != _strip_fences(raw)` computed before any mutation at `llm_client.py:177`; `_strip_fences` is idempotent | closed |
| T-04-02 | Information Disclosure | logger.warning() with section names | accept | Section names come from original resume (trusted source), not LLM output; local CLI — no remote disclosure | closed |
| T-04-03 | Denial of Service | Regex backtracking on adversarial LLM output | mitigate | All regexes use `[^}]+` or `[^*]+` character classes (linear, no nested quantifiers): `guards.py:6,11,27` | closed |
| T-04-04 | Elevation of Privilege | Guard exception propagating to cli.py, aborting write | mitigate | Each `_check_*` wraps body in `try/except Exception`: `guards.py:15,29,43`; `run_guards` never raises | closed |
| T-04-05 | Tampering | cli.py result.content passed to write_resume | accept | Same post-validated LaTeX as before; only variable name changed from `content` to `result.content`; no new trust boundary | closed |
| T-04-06 | Denial of Service | run_guards() exception propagating through cli.py try/except | mitigate | `try/except Exception` in each `_check_*` function; `run_guards` itself never raises (`guards.py:47-50`) | closed |
| T-04-07 | Information Disclosure | Warning messages with LLM-generated content to stderr | accept | Section/employer names in warnings come from original resume (trusted); local CLI tool — no remote disclosure | closed |
| T-04-08 | Spoofing | cli_test.py mocking run_guards | accept | Correct test isolation practice; guard logic covered independently in guards_test.py | closed |
| T-04-09 | Information Disclosure | TailorResult.fences_stripped=False hardcoded in CLI mocks | accept | CLI tests verify orchestration only; guards_test.py covers the fences_stripped=True path | closed |
| T-04-SC | Tampering | Supply chain (npm/pip/cargo installs) | accept | No new packages installed in this phase; stdlib + existing modules only | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-02 | Section names printed to stderr come from the original resume (trusted), not LLM output. Local CLI — no remote disclosure path. | gsd-secure-phase | 2026-06-04 |
| AR-04-02 | T-04-05 | cli.py result.content change is a variable rename only; same validated LaTeX reaches write_resume. No new trust boundary introduced. | gsd-secure-phase | 2026-06-04 |
| AR-04-03 | T-04-07 | Warning content (section/employer names) originates from original resume. Local tool; no external exposure. | gsd-secure-phase | 2026-06-04 |
| AR-04-04 | T-04-08 | Patching run_guards in CLI tests is standard isolation practice; guards covered by dedicated guards_test.py. | gsd-secure-phase | 2026-06-04 |
| AR-04-05 | T-04-09 | CLI mock hardcodes fences_stripped=False (happy path); fences_stripped=True path tested in guards_test.py. | gsd-secure-phase | 2026-06-04 |
| AR-04-06 | T-04-SC | Phase adds no new packages; supply chain surface unchanged from baseline. | gsd-secure-phase | 2026-06-04 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-04 | 10 | 10 | 0 | gsd-secure-phase (orchestrator) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-04
