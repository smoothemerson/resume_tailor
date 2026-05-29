---
phase: "03"
slug: cli-wiring
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-29
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| stdin → main() | User types job description; raw text enters the tool with no prior sanitization | Job description text (untrusted user input) |
| main() → generate_tailored_resume() | Assembled job description string passed to LLM client module | String payload forwarded to Ollama REST API |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-03-01 | Tampering | stdin input | accept | User-supplied text for own resume; no third-party input path; QUAL-04 XML delimiter wrapping already implemented in llm_client.py (Phase 2) | closed |
| T-03-02 | Information Disclosure | success message (stdout) | accept | Prints absolute path of output file; single-user personal CLI, no multi-user context, no secrets in path | closed |
| T-03-03 | Denial of Service | empty JD guard | mitigate | `cli.py:41-43` — `if not job_description.strip()` prints to stderr and exits 1 before calling LLM; prevents empty payload to Ollama | closed |
| T-03-04 | Elevation of Privilege | argparse flags | accept | Flags (--model, --resume, --output-dir) added post-plan via code-review fix (commit b8e76fd); all paths handled by `pathlib.Path`, no shell execution, no injection surface | closed |
| T-03-SC | Tampering | dependency installs | accept | No production packages installed in this phase; only `pytest>=9.0.3` added as dev dependency (commit 739f373); no slopcheck needed | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-01 | Tampering via stdin is inherent to any terminal input; QUAL-04 XML delimiters in Phase 2 already bound the job description in the LLM prompt, preventing injection into the system prompt. Personal single-user tool with no multi-tenant attack surface. | emerson | 2026-05-29 |
| AR-03-02 | T-03-02 | Output file path disclosed on stdout is intentional UX (user needs to know where the file was written). No credentials, tokens, or sensitive data appear in the path. | emerson | 2026-05-29 |
| AR-03-04 | T-03-04 | Three flags expand user control over file paths and model selection. All values passed to internal Python functions (not shell commands). `pathlib.Path` normalizes paths; `requests` POSTs model name as a JSON string to localhost. No privilege escalation vector exists. | emerson | 2026-05-29 |
| AR-03-SC | T-03-SC | Only dev-time tooling (pytest) was added; not installed in production wheel. No supply-chain risk in this phase. | emerson | 2026-05-29 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-29 | 5 | 5 | 0 | orchestrator (secure-phase workflow, short-circuit: register_authored_at_plan_time=true, threats_open=0) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-29
