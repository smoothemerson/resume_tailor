# Phase 12: Prompt Precision - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Update `_build_messages()` in `src/llm_client.py` — replace the existing `<INSTRUCTIONS>` and the content of `<CONSTRAINTS>` with explicit ALLOWED / MUST-NOT-CHANGE lists that mirror the actual LaTeX patterns in the resume.

Scope: one function, one file. No new features, no new tests (existing tests must pass without modification), no changes to the guard pipeline or CLI.

</domain>

<decisions>
## Implementation Decisions

### XML Tag Structure
- **D-01:** Rename `<INSTRUCTIONS>` to `<ALLOWED>`. No existing test checks for `<INSTRUCTIONS>`, so this is a free rename.
- **D-02:** Keep `<CONSTRAINTS>` as the outer XML tag name. One existing test (`test_build_messages_system_contains_constraints_tag`) asserts the `<CONSTRAINTS>` tag is present — renaming would break it and the success criterion requires all existing tests to pass without modification. The *content* inside `<CONSTRAINTS>` is restructured to a MUST-NOT-CHANGE list, but the tag name stays.

### LaTeX Command Precision
- **D-03:** The ALLOWED and MUST-NOT-CHANGE sections must reference actual LaTeX command names where known. The codebase already confirms two macros:
  - `\employer{name}{dates}{title}` — employer header (3-arg, all three args are protected in MUST-NOT-CHANGE)
  - `\header{SectionName}` — section headers (protected in MUST-NOT-CHANGE)
- **D-04:** For project macros and the contact block, the researcher must read `resumes/english.tex` to extract the exact LaTeX commands used, then the planner must reference those commands by name in the prompt. Do not guess or leave as "project name/URL/date" in semantic-only form.

### Anti-Fabrication Rule (PRMP-03)
- **D-05:** The technology anti-fabrication rule lives inside `<CONSTRAINTS>` as a named, prominently labeled bullet — not a separate XML section. Suggested label: `TECHNOLOGY FIDELITY`. Rule: technologies present in the original resume must appear in the output; technologies absent from the original must not appear, even if present in the JD.

### Prompt Section Order
- **D-06:** Final section order: `<PERSONA>` → `<TASK>` → `<CONTEXT>` → `<ALLOWED>` → `<CONSTRAINTS>` → `<OUTPUT_FORMAT>`. This matches the current order with only the `<INSTRUCTIONS>` rename and `<CONSTRAINTS>` content rewrite.

### Claude's Discretion
- Exact prose/wording within each section — the decisions above fix the structure and content categories; the researcher/planner writes the actual sentences.
- Whether to use a bulleted list, numbered list, or sub-headers inside `<ALLOWED>` and `<CONSTRAINTS>` — choose whatever reads most clearly for an LLM.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Prompt Precision — PRMP-01, PRMP-02, PRMP-03 definitions (the authoritative spec for what ALLOWED and MUST-NOT-CHANGE contain)
- `.planning/ROADMAP.md` §Phase 12 — success criteria (all 4, including "all existing tests pass without modification")

### Source Files to Modify
- `src/llm_client.py` — contains `_build_messages()` (lines 26–121); this is the only file that changes in Phase 12

### Test Files (must not be modified)
- `tests/unit/test_llm_client.py` — the full unit test suite; `test_build_messages_system_contains_constraints_tag` (line 32) is the key test constraining tag naming
- `src/llm_client_test.py` — in-src tests; also must pass unchanged

### Resume (researcher must read)
- `resumes/english.tex` — the actual resume LaTeX source; researcher must extract the exact LaTeX macro names used for projects and the contact block so the planner can reference them precisely in the ALLOWED/MUST-NOT-CHANGE lists

### Guard Patterns (for alignment)
- `src/guards.py` — lines 6 and 11 define the `\employer{}{}{}` and `\header{}` regex patterns that confirm the two known LaTeX macros

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_build_messages()` at `src/llm_client.py:26` — the entire function body is the target; the surrounding call site (`src/llm_client.py:150`) does not change
- Current `<CONSTRAINTS>` content (lines 70–81) covers the MUST-NOT-CHANGE ground in natural language — it is the starting point for restructuring, not a throw-away

### Established Patterns
- XML tag structure is used throughout the entire system prompt — keep this pattern; the LLM has been trained on it and guards/tests assume it
- Two-pass pipeline injects JD analysis into the *user* message (not the system prompt); Phase 12 only touches the system prompt; do not touch the user message assembly

### Integration Points
- `generate_tailored_resume()` at `src/llm_client.py:144` calls `_build_messages()` — no signature change needed, Phase 12 is a pure content update
- All guards (`run_guards()`) run after the LLM response; Phase 12 does not touch the guard pipeline

</code_context>

<specifics>
## Specific Ideas

- The PRMP-03 technology rule should be explicitly named/labeled (e.g., `TECHNOLOGY FIDELITY:`) so it stands out as a distinct rule rather than blending into a list of bullets.
- Concrete example language from requirements: "if Azure is in the original it must appear in output; if AWS is not in the original it must not appear" — use this as illustrative guidance (or a literal example) in the prompt.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-prompt-precision*
*Context gathered: 2026-06-09*
