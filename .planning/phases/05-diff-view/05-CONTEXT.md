# Phase 5: Diff View - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement a normalized unified diff between original resume and tailored resume, displayed to stdout when running in an interactive terminal (TTY), automatically suppressed when stdout is piped or redirected. No user flags required. Diff appears before the "Tailored resume written to:" confirmation line.

</domain>

<decisions>
## Implementation Decisions

### Output Order
- **D-01:** Diff appears **before** the "Tailored resume written to:" confirmation. Confirmation lands at the bottom of the output — easy to spot after scrolling past the diff. The flow in `cli.py` becomes: `run_guards()` → `write_resume()` → `show_diff()` → `print("Tailored resume written to: ...")`.

### Color Output
- **D-02:** Diff uses **ANSI colors**: green (`\033[32m`) for `+` (added) lines, red (`\033[31m`) for `-` (removed) lines, reset (`\033[0m`) after each colored line. Context lines (no prefix) printed plain. `@@` hunk headers printed plain. Since the diff is already TTY-gated, colors are always safe — they never leak into pipes.

### Diff Header Labels
- **D-03:** Use simple human-readable labels: `--- original` and `+++ tailored`. No timestamps, no file paths. Context is obvious (always original vs tailored resume).

### Module Structure
- **D-04:** Diff logic lives in a new **`src/diff_view.py`** module. Exports a single public function `show_diff(original: str, tailored: str) -> None`. Follows the `guards.py` pattern — single-concern module, testable in isolation. `cli.py` imports and calls it.

### Normalization (DIFF-03)
- **D-05:** Normalize both texts before diffing: strip trailing whitespace from each line AND collapse runs of 3+ consecutive blank lines into 2. This eliminates trailing-space noise and blank-line-only diffs without losing meaningful spacing. Applied to both `original` and `tailored` before passing to `difflib.unified_diff()`.

### Claude's Discretion
- Context lines shown in `unified_diff()`: use `difflib` default of 3. No need to override — 3 lines of LaTeX context is enough to orient the reader.
- No "Changes:" label or section header before the diff block — the `--- original / +++ tailored` header is self-explanatory.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/ROADMAP.md` §Phase 5 — Goal, success criteria, requirements list (DIFF-01, DIFF-02, DIFF-03)
- `.planning/REQUIREMENTS.md` §Diff View — Full requirement text for DIFF-01, DIFF-02, DIFF-03

### Source Files (must read before planning)
- `src/cli.py` — Integration point: `show_diff()` call inserts between `write_resume()` return and the final `print()`. `resume_text` (original) and `result.content` (tailored) are both in scope here.
- `src/guards.py` — Pattern reference for a single-concern module with one public entry-point function; `diff_view.py` follows this structure.
- `src/llm_client.py` — `TailorResult` NamedTuple provides `result.content` (the tailored text passed to `show_diff`).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sys.stdout.isatty()` — stdlib TTY detection; same predicate used for DIFF-02 (no new dep)
- `difflib.unified_diff()` — stdlib; produces the standard `---/+++/@@ /+/-` unified diff format
- `resume_text` in `cli.py:main()` — original resume, already in scope before the diff call
- `result.content` in `cli.py:main()` — tailored content, already in scope

### Established Patterns
- **Single-concern modules**: `guards.py`, `resume_reader.py`, `resume_writer.py` each export one public function. `diff_view.py` exports `show_diff()`.
- **raise-not-exit pattern**: `llm_client.py` raises, `cli.py` catches. `diff_view.py` should never raise — TTY check and diff are non-fatal operations.
- **`sys.stderr` for warnings, `sys.stdout` for content**: Guards print to stderr. Diff prints to stdout (same channel as the confirmation line).
- **No new dependencies**: All implementation uses stdlib (`difflib`, `sys`) only.

### Integration Points
- `cli.py` `main()` — new `show_diff(resume_text, result.content)` call inserted after `write_resume()` returns `output_path`, before the final `print(f"Tailored resume written to: ...")`.
- `src/diff_view.py` — new file in `src/`; `show_diff()` is the single public entry point.

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard difflib patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 5-Diff View*
*Context gathered: 2026-06-04*
