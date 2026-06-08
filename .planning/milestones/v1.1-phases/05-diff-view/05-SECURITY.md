---
phase: "05"
slug: diff-view
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-05
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| in-memory strings → terminal | Original and tailored resume strings are already-validated LaTeX before reaching show_diff(); they originate from llm_client.py output, not direct user input | LaTeX text (no PII, no credentials) |
| cli.py main() → show_diff() | In-process call with already-validated strings; no new trust boundary introduced | LaTeX text (same strings already held in memory) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-05-01 | Information Disclosure | ANSI codes in piped output | accept | TTY gate (`sys.stdout.isatty()`) ensures ANSI escapes never appear in non-terminal output; no PII surfaces | closed |
| T-05-02 | Denial of Service | Extremely large diff output | accept | Diff bounded by resume file sizes (small text files, <50 KB); no unbounded loop risk | closed |
| T-05-03 | Tampering | cli.py control flow | accept | show_diff() placed outside try/except; a display bug cannot suppress the confirmation print or the written file | closed |
| T-05-04 | Denial of Service | show_diff() hanging | accept | difflib is a pure Python stdlib computation with no I/O and no blocking calls; cannot hang | closed |
| T-05-SC | Tampering | npm/pip/cargo installs | accept | No new external packages installed this phase; stdlib-only (difflib, sys) — dependency surface unchanged | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-01 | ANSI escapes gated by isatty() — no terminal means no color codes; non-TTY consumers (pipes, redirects) receive clean text | plan-time (PLAN.md) | 2026-06-04 |
| AR-05-02 | T-05-02 | Resume files are short personal documents; diff size is inherently bounded by input size; no external or user-controlled input reaches difflib | plan-time (PLAN.md) | 2026-06-04 |
| AR-05-03 | T-05-03 | show_diff() is non-fatal by design; placement outside try/except is the documented mitigation (D-01); display errors cannot suppress file output | plan-time (PLAN.md) | 2026-06-04 |
| AR-05-04 | T-05-04 | difflib.unified_diff is a pure in-memory generator over two lists; no file handles, sockets, or blocking primitives involved | plan-time (PLAN.md) | 2026-06-04 |
| AR-05-SC | T-05-SC | Phase adds only stdlib modules; pyproject.toml dependencies unchanged; supply chain surface not extended | plan-time (PLAN.md) | 2026-06-04 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-05 | 5 | 5 | 0 | gsd-secure-phase (short-circuit: register_authored_at_plan_time=true, threats_open=0) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-05
