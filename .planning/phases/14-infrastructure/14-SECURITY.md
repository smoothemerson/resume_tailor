---
phase: 14
slug: infrastructure
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-13
---

# Phase 14 — Security (infrastructure)

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CI runner → GitHub Actions marketplace | GitHub fetches action code from astral-sh/setup-uv and actions/checkout repos | Build tooling artifacts (public, no secrets) |
| test code → src/ modules | Tests import and call production functions directly | In-process function calls; no I/O boundary |
| tmp_path → filesystem | pytest creates isolated temp directories; no cross-test contamination | Ephemeral test fixture files |
| git index → working tree | `git rm --cached` modifies git index only; local files untouched | Index metadata only |
| .gitignore → git tracking | .gitignore prevents re-tracking of `.claude/` on future `git add` | Path patterns; no content |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-14-01 | Tampering | .github/workflows/ci.yml | mitigate | Actions pinned to full semver tags: `astral-sh/setup-uv@v8.2.0`, `actions/checkout@v4` — prevents supply-chain substitution via moving tags | closed |
| T-14-02 | Information Disclosure | .github/workflows/ci.yml | accept | Workflow contains no secrets, tokens, or credentials — only public tool invocations; verified by grep | closed |
| T-14-03 | Tampering | pyproject.toml include list | accept | Wrong include entries cause missing modules (packaging bug), not a security vulnerability; no runtime privilege impact | closed |
| T-14-SC-P01 | Tampering | GitHub Actions installs | mitigate | Both actions are Astral-official and GitHub-official; Package Legitimacy Audit in RESEARCH.md confirmed \[VERIFIED\] status | closed |
| T-14-04 | Tampering | src/\*\_test.py | accept | Test files contain no secrets or credentials; worst case is incorrect assertions caught by CI | closed |
| T-14-05 | Repudiation | pytest -m unit | accept | `--strict-markers` is set in pyproject.toml; unmarked tests cannot silently bypass the marker filter | closed |
| T-14-SC-P02 | Tampering | npm/pip/cargo installs | accept | Zero new packages installed in this plan; all test infrastructure already in dev dependencies | closed |
| T-14-06 | Information Disclosure | git history | accept | `.claude/` will remain in git history before this commit; history rewriting out of scope per REPO-01 spec — only "untracked going forward" was required | closed |
| T-14-07 | Tampering | .gitignore ordering | mitigate | `.gitignore` written before `git rm --cached` — prevents race condition where re-add could occur between removal and ignore entry | closed |
| T-14-08 | Elevation of Privilege | .claude/ contents | accept | `.claude/` contains Claude Code workspace files (settings, session data); local-only tooling artifacts with no credentials or secrets requiring history erasure | closed |
| T-14-SC-P03 | Tampering | npm/pip/cargo installs | accept | Zero packages installed in this plan; no supply-chain risk introduced | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-14-01 | T-14-02 | Workflow file verified by grep to contain no secrets, tokens, or credentials — disclosure surface is zero | gsd-secure-phase | 2026-06-13 |
| AR-14-02 | T-14-03 | Wrong include entries in pyproject.toml cause packaging bugs (missing modules), not privilege escalation or data exposure | gsd-secure-phase | 2026-06-13 |
| AR-14-03 | T-14-04 | Test files examined; confirmed no embedded credentials — CI would catch incorrect assertions regardless | gsd-secure-phase | 2026-06-13 |
| AR-14-04 | T-14-05 | `--strict-markers` is a pytest enforcement mechanism; marker bypass requires deliberate misconfiguration of pyproject.toml, not an attack vector in this context | gsd-secure-phase | 2026-06-13 |
| AR-14-05 | T-14-SC-P02 | No packages were installed; supply-chain surface is unchanged from previous phase state | gsd-secure-phase | 2026-06-13 |
| AR-14-06 | T-14-06 | REPO-01 spec explicitly scoped to "untracked going forward"; history rewrite was not in scope. `.claude/` contains no credentials — history retention carries no confidentiality risk | gsd-secure-phase | 2026-06-13 |
| AR-14-07 | T-14-08 | `.claude/` holds IDE session files and workspace settings; no tokens, API keys, or personal data present that would require erasure | gsd-secure-phase | 2026-06-13 |
| AR-14-08 | T-14-SC-P03 | No packages installed; supply-chain surface unchanged | gsd-secure-phase | 2026-06-13 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-13 | 11 | 11 | 0 | gsd-secure-phase (short-circuit: all plan-time threats verified CLOSED via SUMMARY flags) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-13
