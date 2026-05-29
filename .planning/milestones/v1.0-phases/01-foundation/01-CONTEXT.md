# Phase 1: Foundation - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Project scaffold, configuration, file I/O modules, and packaging — testable without Ollama running. Delivers: `pyproject.toml` (updated), `resume_tailor/` package with `config.py`, `resume_reader.py`, `resume_writer.py`, and `__init__.py`. Phase is complete when `resume-tailor --help` works after `uv tool install .` and the reader/writer modules operate correctly in isolation.

</domain>

<decisions>
## Implementation Decisions

### Default Resume
- **D-01:** `BASE_RESUME_PATH` in `config.py` defaults to `resumes/english.tex` (anchored via `Path(__file__).parent.parent / "resumes" / "english.tex"`)

### Package Identity
- **D-02:** `pyproject.toml` project name renamed from `"en-cv-ai-engineer"` to `"resume-tailor"` — aligns the package name with the CLI command; `uv tool list` shows the tool by what it does, not the resume it wraps

### Default Model
- **D-03:** `OLLAMA_MODEL = "mistral-small3.2:24b"` — specific model string chosen by user; config is the only change point for swapping models

### Claude's Discretion
- Package layout: flat (`resume_tailor/` directly under project root, not `src/resume_tailor/`) — appropriate scale for a single-dep CLI tool; no import ambiguity issue given no test runner that would shadow the package
- `requires-python` can stay at `>=3.13` (already set in existing pyproject.toml) or be relaxed to `>=3.11`; 3.13 is fine since user is on a modern Python

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Scope
- `.planning/REQUIREMENTS.md` — Phase 1 requirements: CONF-01, CONF-02, PKG-01, CORE-01, CORE-05, ERR-01; traceability table maps each req to its phase
- `.planning/PROJECT.md` — core value, constraints (stdlib + requests only), key decisions table, out-of-scope list

### Roadmap & Success Criteria
- `.planning/ROADMAP.md` §"Phase 1: Foundation" — goal statement and 5 success criteria that must all be TRUE before phase is complete

### Existing Files to Update
- `pyproject.toml` — exists at project root; needs: name renamed to "resume-tailor", `requests>=2.32.0` dep added, `[project.scripts]` entry `resume-tailor = "resume_tailor.cli:main"`, dev deps `ruff` and `mypy`
- `resumes/english.tex` — the base resume file; `BASE_RESUME_PATH` in `config.py` must point here

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `resumes/english.tex`: base resume content — reader module returns this as a string; writer places output in `resumes/output/`
- `resumes/portuguese.tex`: alternate resume — not the default, but `BASE_RESUME_PATH` swap is the only change needed to use it

### Established Patterns
- `pyproject.toml` already present at root with `requires-python = ">=3.13"` and no deps — update in-place, do not create a second one
- No existing Python source — package directory `resume_tailor/` is a new creation

### Integration Points
- Phase 2 (`llm_client.py`) imports `config.py` constants directly — keep all constants at module level with no class wrapping
- Phase 3 (`main.py`) imports `resume_reader`, `resume_writer`, and `llm_client` — flat package structure required

</code_context>

<specifics>
## Specific Ideas

- Model string is `"mistral-small3.2:24b"` — use this exact string as the constant value, not a short alias
- CLI entry point registered in pyproject.toml as `resume-tailor = "resume_tailor.cli:main"` — `cli.py` is Phase 3's concern but the entry point must be declared in Phase 1's packaging work

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 1-Foundation*
*Context gathered: 2026-05-28*
