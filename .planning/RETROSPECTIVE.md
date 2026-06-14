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

## Milestone: v1.1 — Output Quality + Test Coverage

**Shipped:** 2026-06-08
**Phases:** 8 (Phases 4–11) | **Plans:** 18 | **Timeline:** 7 days (2026-06-02 → 2026-06-08)

### What Was Built

- Output reliability guards: non-fatal `guards.py` with three check functions; `TailorResult` NamedTuple threads `fences_stripped` metadata through the pipeline
- Normalized diff view with ANSI color using `difflib`; TTY-gated with zero config (no `--diff` flag)
- Two-pass pipeline: `jd_analyzer.py` extracts structured requirements; injected into `_build_messages()` as second context block; silent fallback on any parse failure
- JD keyword match summary with whole-word regex and stop-word filtering; same TTY guard as diff
- pytest infrastructure: `--strict-markers`, `importlib` import mode, session-scoped Ollama skip fixtures, organized `unit/` / `integration/` / `e2e/` layout (removes all `sys.path` hacks)
- Test pyramid: 107 tests — 99 unit (src + tests/unit), 2 integration (real Ollama, skipable), 2 E2E subprocess

### What Worked

- TDD sequence for Phase 6: test scaffolds written before implementation; test files compile-checked on first run; zero wasted cycles on mock mismatches
- TTY guard reuse: deciding once (`sys.stdout.isatty()`) and applying it identically to diff and keyword summary kept UX consistent with no duplication
- Non-fatal guard architecture (GUARD-04 as rule): wrapping every `_check_*` in `try/except Exception` made the guards trivially extendable — each new guard is isolated, can't break others
- `TailorResult` NamedTuple: adding metadata to the return type without global state or extra arguments; tests could assert on `fences_stripped` independently

### What Was Inefficient

- Traceability table in REQUIREMENTS.md left TEST-08/09 as "Pending" even after Phase 10 shipped; caused false alarm at milestone close — should have been updated in the phase-complete step
- Phase 6 introduced `--import-mode=importlib` as a deviation; should have been in the original plan since the module naming collision between `test_llm_client.py` in unit/ vs integration/ was predictable from the layout

### Patterns Established

- `TTY-gate-by-default`: interactive output (diff, keyword summary) uses `sys.stdout.isatty()` with no opt-in flag; pipelines stay clean automatically
- `non-fatal-guard`: guard functions never raise; wrap in `try/except Exception`; each guard is independently skippable
- `NamedTuple-for-metadata`: use a NamedTuple return type to thread additional context alongside primary value without changing callers or adding global state
- `importlib-mode`: use `--import-mode=importlib` in pytest when test directories share file basenames without `__init__.py`

### Key Lessons

1. Update traceability table rows to "Complete" in the same commit that completes the phase — stale rows become noise at milestone close
2. Predict module naming collisions early: if multiple test subdirectories will have same-named test files, set `--import-mode=importlib` in Phase 8 (test infrastructure), not Phase 10 (integration tests)
3. The TTY gate pattern is reusable — define it once as a predicate function, apply to every feature that should be interactive-only; keeps all such features consistent
4. Non-fatal architecture for advisory subsystems (guards, linters): wrap body in `try/except Exception` from the start; makes the subsystem composable and safe to extend

### Cost Observations

- Model mix: claude-sonnet-4-6 throughout
- Sessions: ~8-10 sessions across 7 days
- Notable: 215 commits for 8 phases (avg ~27/phase) reflects consistent atomic-commit discipline; phase summaries are traceable through git log

---

## Milestone: v1.2 — Precision & CI

**Shipped:** 2026-06-14
**Phases:** 3 (Phases 12–14) | **Plans:** 8 | **Timeline:** 5 days

### What Was Built

- System prompt `<ALLOWED>` whitelist + `<CONSTRAINTS>` MUST-NOT-CHANGE list with exact inline LaTeX patterns — replaces vague INSTRUCTIONS block
- Three-layer anti-fabrication defense: temperature=0.2, JD ANALYSIS USAGE rule in CONSTRAINTS, `_check_fabricated_technologies` guard with token-boundary regex
- `_check_technology_substitution` guard: Skills section set-diff with three-way warning (substituted / removed-only / added-only)
- `_check_protected_sections` guard: contact block, Education, Languages, employer headers, project anchors via regex set-diff
- GitHub Actions CI: ruff lint/format-check + `pytest -m unit` on every push/PR to main (first CI in the project)
- Wheel include list fixed to ship all 10 modules; 35 new unit tests; `.claude/` permanently untracked (429 files removed from index)

### What Worked

- UAT test failure in Phase 12 Plan 01 surfaced a real gap (prompt alone insufficient for anti-fabrication) → triggered Plan 02 gap closure with three-layer defense; gap closure was faster than a new phase would have been
- Module-private helper extraction in Phase 13 Plan 01 (`_extract_section`, `_extract_technologies`): Plan 02 reused both without modification — the right call to extract upfront
- Atomic commit for `.gitignore` + `git rm --cached`: no race window; `git check-ignore` confirmed active on first try
- Feature branch + PR workflow with CI: lint failures caught by CI gave concrete, actionable feedback (3 fixable F401s + format drift); cleaner than catching these in review

### What Was Inefficient

- REQUIREMENTS.md traceability rows for GARD-05/06/07, TEST-12/13 were not updated to "Complete" after Phase 13 executed — required manual correction at milestone close; same lesson as v1.1 still being learned
- `uv.lock` removed from `.gitignore` (CR-01) but never generated and committed — CI failed with `--locked` on first run; CR-01 should have included generating the lockfile as a task
- Local `main` branch diverged from `origin/main` by the time Phase 14 was shipped; merge required at complete-milestone time; would have been cleaner to `git pull --rebase` after each PR merged

### Patterns Established

- `three-layer-anti-fabrication`: sampling temperature + prompt framing rule + post-generation guard — any two-layer approach has a gap; three layers are independently testable and independently effective
- `atomic-gitignore-untrack`: always commit `.gitignore` addition and `git rm --cached` in the same commit; never split them
- `extract-helpers-for-guard-reuse`: when writing two guards that operate on the same document structure, extract shared extraction helpers in Plan 01; Plan 02 should reuse without re-implementing
- `CI-as-lint-gate`: CI running ruff + unit tests on every PR caught formatting drift accumulated across 3 phases; worth the Phase 14 investment retroactively

### Key Lessons

1. Update traceability table rows to "Complete" in the same commit that finishes the phase — this is the third milestone this appeared; add it to the phase-completion checklist
2. When a PR removes a file from `.gitignore` to enable tracking it, the generating step (e.g. `uv lock`) must be part of the same PR or the very next commit — don't leave that window open
3. Pull after each PR merges; diverged local `main` complicates `complete-milestone` more than the extra pull costs
4. UAT failure is a feature: Phase 12 UAT caught a real fabrication risk that test coverage couldn't have surfaced (probabilistic failure); budget for a gap-closure plan in any phase involving LLM behavior

### Cost Observations

- Model mix: claude-sonnet-4-6 throughout
- Sessions: ~5-6 sessions across 5 days
- Notable: Phase 13 executed 3 plans via TDD (RED/GREEN commits) in under 3 hours — the non-fatal guard pattern and helper extraction made each plan fast and isolated

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0      | 3      | 4     | First milestone — baseline established |
| v1.1      | 8      | 18    | TDD sequence + worktrees for parallel wave execution |
| v1.2      | 3      | 8     | Feature branch PRs + CI gate; gap-closure plan pattern |

### Cumulative Quality

| Milestone | Tests | Zero-Dep Additions |
|-----------|-------|--------------------|
| v1.0      | 16    | 0 (requests was the sole runtime dep from day one) |
| v1.1      | 107   | 0 (all features built on stdlib + requests) |
| v1.2      | 142   | 0 (guards, CI, test coverage — zero new runtime deps) |

### Top Lessons (Verified Across Milestones)

1. Commit all files before starting a new phase — worktrees are git-state, not filesystem-state
2. Decide raise-vs-exit contracts upfront — retrofitting them after modules are written requires touching every test
3. Update traceability rows to "Complete" in the same commit that finishes the phase — stale rows cause false alarms at milestone close
4. Predict module naming collisions early in test infrastructure phases — `--import-mode=importlib` is the right fix, not `__init__.py`
5. When a PR removes a file from `.gitignore` to enable tracking it, generate that file in the same PR — don't leave the lockfile-missing window open for CI to trip on
6. UAT failure is a feature, not a setback — for probabilistic systems (LLMs), budget a gap-closure plan before declaring any LLM-behavior phase done
