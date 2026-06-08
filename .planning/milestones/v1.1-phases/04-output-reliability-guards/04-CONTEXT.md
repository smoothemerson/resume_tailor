# Phase 4: Output Reliability Guards - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement three guard functions that analyze original LaTeX vs tailored LaTeX output and print non-fatal warnings to stderr when problems are detected: dropped sections (GUARD-01), format violations/markdown leakage (GUARD-02), and hallucinated employer fields (GUARD-03). All guards degrade gracefully — no guard failure ever blocks the output file from being written (GUARD-04).

</domain>

<decisions>
## Implementation Decisions

### Guard Architecture
- **D-01:** Guard logic lives in a new `src/guards.py` module, not inside `llm_client.py`. Keeps LLM HTTP logic and validation logic separated. Matches existing raise-not-exit pattern (llm_client raises errors, cli.py orchestrates).
- **D-02:** `guards.py` exports a `run_guards(original_text, tailored_text)` function that `cli.py` calls.
- **D-03:** `run_guards()` is called in `cli.py` **before** `write_resume()`. Guards fire on the content first; then the file is written regardless of how many warnings fired.

### GUARD-02: Format Violations
- **D-04:** `_validate_latex()` in `llm_client.py` stays as-is — hard errors for missing `\documentclass` or `\end{document}` remain fatal (blocking). These are not converted to warnings.
- **D-05:** GUARD-02 is a separate, non-blocking soft check with two sub-checks:
  1. **Stripped fences warning** — warn if `_strip_fences()` actually modified the text (i.e., the model returned markdown fences that had to be stripped). This signals the model ignored the LaTeX-only instruction.
  2. **Inline markdown in body** — warn if the tailored content contains markdown markers embedded inside the document body (e.g., triple-backtick fences, lines starting with `#` or `##`, `**bold**` markers that are not LaTeX commands).
- **D-06:** To enable the stripped-fences check, `_strip_fences()` must be callable from outside `llm_client.py`, or the planner must expose a way to compare before/after. Planner should implement this cleanly (e.g., pass raw content through guard before stripping, or have `generate_tailored_resume()` return fences-were-stripped metadata).

### GUARD-03: Hallucinated Fields
- **D-07:** Extract employer names and date strings from `\employer{name}{dates}{title}` LaTeX commands in the original resume using regex. Verify each appears in the tailored output.
- **D-08:** Scope is `\employer{}` entries only. Education section (`\schoolwithcourses{}`, `\school{}`) is excluded — institutions are rarely hallucinated and keeping scope tight avoids false positives.

### Warning Message Format
- **D-09:** Warnings use `WARNING:` prefix, consistent with the existing `Error:` prefix the tool already uses for fatal errors. No guard IDs, no color, no emoji.
  - Example: `WARNING: Section "Skills" missing from tailored output.`
  - Example: `WARNING: LLM returned markdown fences that were stripped from output.`
  - Example: `WARNING: Employer "Acme Corp" from original resume not found in tailored output.`
- **D-10:** Warnings print inline as each guard fires (no buffering/collect-then-print). Each guard function prints to `sys.stderr` directly when it detects an issue.

### GUARD-01: Section Detection
- **D-11:** Sections are detected via `\header{...}` custom commands, which is the section marker used in this specific resume template (not standard `\section{}`). Extract all `\header{...}` values from original, verify each appears in tailored.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/ROADMAP.md` §Phase 4 — Goal, success criteria, requirements list (GUARD-01 through GUARD-04)
- `.planning/REQUIREMENTS.md` §Output Guards — Full requirement text for GUARD-01, GUARD-02, GUARD-03, GUARD-04

### Source Files (must read before planning)
- `src/llm_client.py` — Contains `_strip_fences()` and `_validate_latex()` which GUARD-02 interacts with; `generate_tailored_resume()` is the function that returns content passed to `run_guards()`
- `src/cli.py` — Integration point: `run_guards()` is called here, before `write_resume()`
- `resumes/english.tex` — The actual resume file; uses `\header{...}` for sections and `\employer{name}{dates}{title}` for job entries — guards must match these exact patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_strip_fences(text)` in `src/llm_client.py` — GUARD-02 needs to detect when this function modified the text; may need to expose or replicate for comparison
- `_validate_latex(text)` in `src/llm_client.py` — stays as hard-error validation; GUARD-02 adds soft checks on top

### Established Patterns
- **raise-not-exit pattern**: `llm_client.py` raises errors, `cli.py` catches and calls `sys.exit(1)`. Guards fit this: `guards.py` prints warnings (never raises), `cli.py` calls it before write.
- **`sys.stderr` for errors**: `cli.py` already prints `Error: ...` to `sys.stderr`. GUARD warnings use same channel with `WARNING:` prefix.
- **Section markers**: Resume uses custom `\header{...}` command (not `\section{}`). Guard regex must target `\header`.
- **Employer entries**: Resume uses `\employer{name}{dates}{title}` — three braced arguments. GUARD-03 regex must handle nested braces in each argument.

### Integration Points
- `cli.py` `main()` — new `run_guards(resume_text, content)` call inserted after `generate_tailored_resume()` returns and before `write_resume()` is called
- `guards.py` — new file in `src/`; `run_guards()` is the single public entry point

</code_context>

<specifics>
## Specific Ideas

No specific references beyond what's captured in decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-Output Reliability Guards*
*Context gathered: 2026-06-02*
