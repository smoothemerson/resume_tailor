# Roadmap: Resume Tailor CLI

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-05-29)
- ✅ **v1.1 Output Quality + Test Coverage** — Phases 4-11 (shipped 2026-06-08)
- 🔄 **v1.2 Precision & CI** — Phases 12-14 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-05-29</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-05-28
- [x] Phase 2: LLM Integration (1/1 plan) — completed 2026-05-28
- [x] Phase 3: CLI Wiring (1/1 plan) — completed 2026-05-29

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>✅ v1.1 Output Quality + Test Coverage (Phases 4-11) — SHIPPED 2026-06-08</summary>

- [x] Phase 4: Output Reliability Guards (3/3 plans) — completed 2026-06-02
- [x] Phase 5: Diff View (2/2 plans) — completed 2026-06-04
- [x] Phase 6: Two-Pass Pipeline (5/5 plans) — completed 2026-06-07
- [x] Phase 7: JD Keyword Match Summary (2/2 plans) — completed 2026-06-08
- [x] Phase 8: Test Infrastructure (2/2 plans) — completed 2026-06-02
- [x] Phase 9: Unit Test Gaps (2/2 plans) — completed 2026-06-04
- [x] Phase 10: Integration Tests (1/1 plan) — completed 2026-06-07
- [x] Phase 11: E2E Tests (1/1 plan) — completed 2026-06-08

Full archive: `.planning/milestones/v1.1-ROADMAP.md`

</details>

## v1.2 Precision & CI (Phases 12–14)

### Phase 12: Prompt Precision

**Goal:** Replace INSTRUCTIONS + CONSTRAINTS in `_build_messages()` with explicit ALLOWED/PROTECTED rules matching actual resume LaTeX patterns.

**Requirements:** PRMP-01, PRMP-02, PRMP-03

**Plans:** 2/2 plans complete
Plans:

- [x] 12-01-PLAN.md — Rewrite _build_messages() system_prompt with ALLOWED/MUST-NOT-CHANGE/TECHNOLOGY FIDELITY sections
- [x] 12-02-PLAN.md — Gap closure (UAT test 1): temperature option, jd_analysis priming defusal, technology-fidelity guard

**Success criteria:**

1. System prompt has a clearly labeled ALLOWED section listing exactly which LaTeX elements may be rewritten
2. System prompt has a clearly labeled MUST NOT CHANGE section listing protected elements
3. System prompt states the anti-fabrication rule: technologies present in original must appear; absent technologies must not appear
4. All existing tests pass without modification

---

### Phase 13: Guard Expansion

**Goal:** Add two new guards that catch technology substitution and protected-section mutations, and ship unit tests for both.

**Requirements:** GARD-05, GARD-06, GARD-07, TEST-12, TEST-13

**Success criteria:**

1. `run_guards()` calls both new guards and cannot raise
2. `_check_technology_substitution` warns correctly for substitution, removal-only, addition-only; silent for identical or no skills section
3. `_check_protected_sections` warns correctly for each protected element type; silent when all sections match
4. All new tests tagged `@pytest.mark.unit` and pass with `pytest -m unit`
5. All existing tests continue to pass

---

### Phase 14: Infrastructure

**Goal:** Fix the packaging gap, ship CI, fill unit test gaps, and remove `.claude/` from git tracking.

**Requirements:** PKG-01, CI-01, TEST-14, TEST-15, TEST-16, REPO-01

**Success criteria:**

1. `uv build` wheel includes `jd_analyzer.py` and `keyword_matcher.py`
2. CI workflow is valid YAML, triggers on push/PR to main, no secrets
3. All 11 new unit tests tagged `@pytest.mark.unit` and pass with `pytest -m unit`
4. `git ls-files .claude/` returns nothing
5. `.gitignore` contains `.claude/`
6. All existing tests continue to pass

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-05-28 |
| 2. LLM Integration | v1.0 | 1/1 | Complete | 2026-05-28 |
| 3. CLI Wiring | v1.0 | 1/1 | Complete | 2026-05-29 |
| 4. Output Reliability Guards | v1.1 | 3/3 | Complete | 2026-06-02 |
| 5. Diff View | v1.1 | 2/2 | Complete | 2026-06-04 |
| 6. Two-Pass Pipeline | v1.1 | 5/5 | Complete | 2026-06-07 |
| 7. JD Keyword Match Summary | v1.1 | 2/2 | Complete | 2026-06-08 |
| 8. Test Infrastructure | v1.1 | 2/2 | Complete | 2026-06-02 |
| 9. Unit Test Gaps | v1.1 | 2/2 | Complete | 2026-06-04 |
| 10. Integration Tests | v1.1 | 1/1 | Complete | 2026-06-07 |
| 11. E2E Tests | v1.1 | 1/1 | Complete | 2026-06-08 |
| 12. Prompt Precision | v1.2 | 2/2 | Complete    | 2026-06-13 |
| 13. Guard Expansion | v1.2 | 3/3 | Complete   | 2026-06-14 |
| 14. Infrastructure | v1.2 | 0/1 | Pending | — |
