---
phase: 07
slug: jd-keyword-match-summary
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-08
---

# Phase 07 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| LLM output → analysis dict | jd_analyzer.py parses LLM-generated JSON; keywords are LLM-generated strings | Untrusted string content |
| analysis dict → regex engine | Keyword strings passed to re.escape() before inclusion in a regex pattern | Escaped string literals |
| analysis dict → cli.py → show_keyword_match | Analysis dict flows through cli.py's None guard before reaching keyword_matcher.py | Structured dict (may be None) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-07-01 | Tampering | `re.escape(kw)` in `_match_keywords` | mitigate | `re.escape()` applied to every keyword before regex compilation — prevents regex injection via LLM-generated keyword strings. Verified at `src/keyword_matcher.py:37`. | closed |
| T-07-02 | Denial of Service | Large keyword list from analysis dict | accept | LLM output bounded by model context window; keyword lists typically <50 items; no loop amplification risk | closed |
| T-07-03 | Information Disclosure | Match summary printed to stdout | accept | Local CLI for personal use; stdout output is intentional and TTY-gated; no sensitive data disclosed | closed |
| T-07-04 | Spoofing | `sys.stdout.isatty()` check | accept | TTY check is process-level; no trust boundary crossing; non-TTY suppression is a UX feature, not a security control | closed |
| T-07-05 | Tampering | `cli.py` None guard for analysis | mitigate | Explicit `if analysis is not None:` guard in `main()` prevents `AttributeError` if analysis is None; `show_keyword_match` never called with None. Verified at `src/cli.py:60`. | closed |
| T-07-06 | Information Disclosure | `show_keyword_match` output visible in CLI stdout | accept | Output is intentional user-facing feedback; TTY-gated in `keyword_matcher.py`; keyword list contains only what user typed as the JD | closed |
| T-07-SC | Tampering | Supply chain (pip/npm/cargo installs) | accept | No new packages installed in this phase; stdlib + requests only; no new supply chain risk introduced | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-07-01 | T-07-02 | Keyword list size bounded by LLM context window; typical payload <50 items; no amplification vector | Emerson Faria | 2026-06-08 |
| AR-07-02 | T-07-03 | Tool is a local personal-use CLI; stdout is the intended delivery channel; TTY gate prevents accidental disclosure to pipes | Emerson Faria | 2026-06-08 |
| AR-07-03 | T-07-04 | isatty() check is a UX feature, not an authentication control; no security boundary crossed | Emerson Faria | 2026-06-08 |
| AR-07-04 | T-07-06 | Keywords are user-supplied JD text reflected back to the same user; no third-party exposure | Emerson Faria | 2026-06-08 |
| AR-07-05 | T-07-SC | Phase uses stdlib + requests only; no new packages; supply chain surface unchanged | Emerson Faria | 2026-06-08 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-08 | 7 | 7 | 0 | gsd-secure-phase (orchestrator) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-08
