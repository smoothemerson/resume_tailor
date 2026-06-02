# Roadmap: Resume Tailor CLI

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-05-29)
- 🚧 **v1.1 Output Quality** — Phases 4-7 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-05-29</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-05-28
- [x] Phase 2: LLM Integration (1/1 plan) — completed 2026-05-28
- [x] Phase 3: CLI Wiring (1/1 plan) — completed 2026-05-29

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Output Quality (In Progress)

**Milestone Goal:** Upgrade the tailoring pipeline to produce measurably better output — with visible feedback, stronger JD-targeting, and guards against common LLM failures.

- [ ] **Phase 4: Output Reliability Guards** - Warn users when the tailored output drops sections, introduces hallucinated fields, or violates LaTeX-only format constraints
- [ ] **Phase 5: Diff View** - Show a normalized unified diff between original and tailored resume on interactive terminals
- [ ] **Phase 6: Two-Pass Pipeline** - Restructure LLM calls to perform a JD analysis pass before tailoring, injecting extracted requirements into the tailoring prompt
- [ ] **Phase 7: JD Keyword Match Summary** - After tailoring, display which JD keywords from the analysis pass appear in the tailored resume

## Phase Details

### Phase 4: Output Reliability Guards
**Goal**: Users receive warnings when the tailored resume silently drops content, introduces hallucinated fields, or breaks LaTeX formatting — without ever blocking the output file from being written
**Depends on**: Phase 3 (v1.0 CLI Wiring)
**Requirements**: GUARD-01, GUARD-02, GUARD-03, GUARD-04
**Success Criteria** (what must be TRUE):
  1. Running the tool against a JD that causes a section to be dropped prints a warning to stderr identifying the missing section
  2. Running the tool when the LLM returns markdown fences or prose before `\documentclass` prints a format violation warning to stderr
  3. Running the tool when the LLM introduces employer names or dates not in the original resume prints a hallucination warning to stderr
  4. All guard warnings are non-fatal — the tailored `.tex` file is written to disk regardless of how many warnings fire
**Plans**: TBD

### Phase 5: Diff View
**Goal**: Users can immediately see what changed between their original resume and the tailored version without opening two files in an editor — and the output stays clean when the tool is used in scripts or pipelines
**Depends on**: Phase 4
**Requirements**: DIFF-01, DIFF-02, DIFF-03
**Success Criteria** (what must be TRUE):
  1. Running the tool in an interactive terminal prints a unified diff of original vs tailored resume after the file is written
  2. Running the tool with stdout piped or redirected produces no diff output — the file is still written normally
  3. The diff omits trailing-space and blank-line-only changes so only semantically meaningful edits are visible
**Plans**: TBD

### Phase 6: Two-Pass Pipeline
**Goal**: The tailoring call is guided by an explicit machine-extracted understanding of the job description — key technologies, role requirements, and emphasis areas are extracted in a first LLM pass and injected into the tailoring prompt — with the existing single-pass behavior preserved as a fallback
**Depends on**: Phase 5
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04
**Success Criteria** (what must be TRUE):
  1. Providing a JD results in the tool making two LLM calls — one analysis call and one tailoring call — visible via progress messages
  2. The tailoring call's prompt contains the extracted JD requirements from the analysis call
  3. When the analysis call produces malformed or unparseable output, the tool falls back silently to single-pass behavior and still produces a tailored resume
  4. Both LLM calls are protected by the existing truncation guard — a `done_reason: length` response on either call triggers the same error path as today
**Plans**: TBD
**UI hint**: no

### Phase 7: JD Keyword Match Summary
**Goal**: Users see a post-tailoring summary of which JD-extracted keywords appear in the tailored resume, giving a measurable signal of alignment quality — visible only in interactive terminal sessions
**Depends on**: Phase 6
**Requirements**: MATCH-01, MATCH-02, MATCH-03
**Success Criteria** (what must be TRUE):
  1. After tailoring completes in an interactive terminal, a keyword match summary is printed showing which extracted JD keywords appear in the tailored resume
  2. The match summary is suppressed when stdout is piped or redirected
  3. Keywords are matched as whole words and common stop words are excluded — searching for "and" or "the" does not produce false positives
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-05-28 |
| 2. LLM Integration | v1.0 | 1/1 | Complete | 2026-05-28 |
| 3. CLI Wiring | v1.0 | 1/1 | Complete | 2026-05-29 |
| 4. Output Reliability Guards | v1.1 | 0/? | Not started | - |
| 5. Diff View | v1.1 | 0/? | Not started | - |
| 6. Two-Pass Pipeline | v1.1 | 0/? | Not started | - |
| 7. JD Keyword Match Summary | v1.1 | 0/? | Not started | - |
