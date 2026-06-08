# Milestones — Resume Tailor CLI

## v1.0 MVP

**Shipped:** 2026-05-29
**Phases:** 1-3
**Plans:** 4
**Requirements:** 16/16 v1 requirements completed

### Delivered

End-to-end working CLI tool: reads a LaTeX resume, accepts a multiline job description, calls a local Ollama LLM via /api/chat with full output safety guards, and writes a timestamped tailored .tex file — installable as a shell command via `uv tool install .`.

### Key Accomplishments

1. Five-module resume_tailor package with Path(__file__)-anchored config, FileNotFoundError-safe reader, and timestamped writer — testable without Ollama
2. pyproject.toml + hatchling packaging: `resume-tailor` shell command registered via `uv tool install .`
3. Ollama /api/chat integration with unconditional fence stripping, done_reason truncation guard, and documentclass/end{document} LaTeX validation — all five safety guards built in from Phase 2
4. Full CLI orchestration: banner, END-sentinel input loop, empty-JD guard, progress flush, try/except error boundary, absolute-path success message
5. 16 unit tests (11 in llm_client_test.py + 5 in cli_test.py) covering all behavioral contracts

### Stats

- Phases: 3 | Plans: 4 | Timeline: 2 days (2026-05-28 → 2026-05-29)
- Python files: 8 source files, ~429 LOC
- Commits: 73
- Git range: 0b6bb1a → 884dd9e

### Archived Artifacts

- `.planning/milestones/v1.0-ROADMAP.md` — full phase details
- `.planning/milestones/v1.0-REQUIREMENTS.md` — all requirements with outcomes

---

## v1.1 Output Quality + Test Coverage

**Shipped:** 2026-06-08
**Phases:** 4–11
**Plans:** 18
**Requirements:** 25/25 v1.1 requirements completed

### Delivered

Upgraded the tailoring pipeline with output reliability guards, a normalized diff view, a two-pass JD analysis pipeline, and a keyword match summary — then validated the entire codebase with a complete unit/integration/e2e test pyramid (107 tests).

### Key Accomplishments

1. Output reliability guards: non-fatal warnings for dropped sections, format violations, and hallucinated employer fields — `TailorResult` NamedTuple threads metadata from `llm_client.py` to `cli.py` without global state
2. Normalized diff view with ANSI color, auto-suppressed when stdout is piped — no flag required; always-on with TTY guard
3. Two-pass pipeline: `jd_analyzer.py` extracts technologies/requirements/emphasis in pass 1, injected into tailoring prompt in pass 2; silent fallback on any failure
4. JD keyword match summary with whole-word regex and stop-word filtering, TTY-gated alongside diff
5. Full pytest infrastructure: `--strict-markers`, `importlib` import mode, session-scoped Ollama skip fixtures, organized `unit/` / `integration/` / `e2e/` layout
6. Complete test pyramid: 107 tests — 99 unit (src + tests/unit), 2 integration (real Ollama, skipable), 2 E2E subprocess (error path + golden path)

### Stats

- Phases: 4–11 (8 phases) | Plans: 18 | Timeline: 7 days (2026-06-02 → 2026-06-08)
- Python files: 22 (15 src + 7 tests), ~1,738 LOC
- Commits: ~215 during v1.1
- Git range: post-v1.0 tag → 42b394e

### Archived Artifacts

- `.planning/milestones/v1.1-ROADMAP.md` — full phase details
- `.planning/milestones/v1.1-REQUIREMENTS.md` — all requirements with outcomes

---

*Next: `/gsd-new-milestone` to plan v1.2*
