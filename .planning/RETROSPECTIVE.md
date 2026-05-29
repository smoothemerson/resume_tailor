# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-05-29
**Phases:** 3 | **Plans:** 4 | **Timeline:** 2 days (2026-05-28 → 2026-05-29)

### What Was Built

- Five-module resume_tailor package with config, reader, writer — fully testable before Ollama was involved
- Ollama /api/chat integration with unconditional fence stripping, done_reason truncation guard, and LaTeX boundary validation — all safety guards in Phase 2 as planned
- Full CLI orchestration: banner, END-sentinel input loop, empty-JD guard, progress flush, try/except error boundary, absolute-path success message
- 16 unit tests covering all safety guard behavioral contracts (11 in llm_client, 5 in CLI)
- Installable as `resume-tailor` shell command via `uv tool install .`

### What Worked

- Building Phase 1 without Ollama dependency: isolated file I/O testing before any LLM risk; caught packaging issues early
- Raise-not-exit pattern decided upfront: llm_client.py never calls sys.exit, only raises; Phase 3 test isolation was trivially easy
- All five safety guards (fence strip, LaTeX validate, done_reason, health check, XML delimiters) built in Phase 2 rather than bolted on later — no rework needed
- TDD RED/GREEN on CLI wiring caught the argparse/pytest argv clash immediately; would have been a confusing integration bug otherwise

### What Was Inefficient

- log_manager.py was untracked in the main workspace, causing a blocking deviation in Phase 2 (had to create it in the worktree); should have been committed before Phase 2 began
- pyproject.toml README.md reference vs missing file: plan listed `readme = "README.md"` but didn't include creating the file; caught at first build attempt

### Patterns Established

- `raise-not-exit`: modules raise, CLI layer owns sys.exit — makes every module independently testable
- `Path(__file__) anchoring`: all paths in config.py derive from `__file__`, not cwd; survives `uv tool install`
- Safety-guards-in-phase: all output safety for a given integration belong in that phase's module, not retrofitted in future phases
- `done_reason` check before fence strip: truncation detection must run before any processing of potentially-truncated content

### Key Lessons

1. Build the testable layer first (Phase 1 file I/O without Ollama) — it surfaces packaging issues before LLM complexity is added
2. Decide error propagation contract (raise vs exit) before writing any module — retrofitting is expensive
3. All output safety guards for an integration belong in the integration module, not the caller — they're easier to test in isolation and can't be accidentally bypassed
4. Commit all files before starting the next phase — untracked files in the workspace don't appear in worktrees

### Cost Observations

- Model mix: claude-sonnet-4-6 throughout
- Sessions: ~3-4 sessions across 2 days
- Notable: 73 commits for a 2-day, 429-LOC project reflects the atomic-commit discipline; git log is a clean execution trace

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0      | 3      | 4     | First milestone — baseline established |

### Cumulative Quality

| Milestone | Tests | Zero-Dep Additions |
|-----------|-------|--------------------|
| v1.0      | 16    | 0 (requests was the sole runtime dep from day one) |

### Top Lessons (Verified Across Milestones)

1. Commit all files before starting a new phase — worktrees are git-state, not filesystem-state
2. Decide raise-vs-exit contracts upfront — retrofitting them after modules are written requires touching every test
