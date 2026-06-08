# Phase 07: JD Keyword Match Summary - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

After tailoring completes, display a keyword match summary that shows how many JD-extracted keywords appear in the tailored resume — and which ones. The summary is printed only in interactive TTY sessions (suppressed on pipe/redirect). Keywords come from the pass-1 analysis dict (`technologies`, `requirements`, `emphasis_areas`). When analysis is `None` (pass-1 failed), no summary is shown. Requirements: MATCH-01, MATCH-02, MATCH-03.

</domain>

<decisions>
## Implementation Decisions

### Display Format
- **D-01:** Display format is count + matched list: header line `"Keyword match: N/M"` followed by matched keywords as a flat comma-separated list on the next line (e.g., `"  Python, FastAPI, RAG, Docker"`). Not grouped by category — all matched keywords in one flat line.
- **D-02:** Position in CLI output flow: after `show_diff()`, before `"Tailored resume written to: ..."`. All post-processing output (diff + match summary) appears together before the closing path line.
- **D-03:** TTY-gated — same `sys.stdout.isatty()` predicate as `show_diff()`. Suppressed automatically when stdout is piped or redirected. No flag needed.

### Keyword Matching
- **D-04:** Minimal stop word list (~15 words): `a, an, the, and, or, of, in, to, for, with, is, are, be, on, at`. Defined as a module-level `frozenset` constant named `STOP_WORDS` — named, visible, easy to extend. Fits the auditable code portfolio constraint.
- **D-05:** Whole-word regex matching — use `re.search(r'\b' + re.escape(kw.lower()) + r'\b', tailored_lower)`. Case-insensitive. Keyword source: all three fields from the analysis dict (`technologies`, `requirements`, `emphasis_areas`) pooled together, after stop word filtering.

### Module Structure
- **D-06:** New `src/keyword_matcher.py` module — consistent with single-concern pattern (`guards.py`, `diff_view.py`, `jd_analyzer.py`). Keeps `cli.py` thin.
- **D-07:** Single public entry point: `show_keyword_match(analysis: dict, tailored_text: str) -> None`. Mirrors `show_diff(original, tailored)` signature style from `diff_view.py`. Does matching + TTY check + printing internally. Never raises (same non-fatal pattern as `run_guards()` and `show_diff()`).

### Edge Cases (Claude's Discretion)
- When `analysis` is `None`: caller (`cli.py`) already guards with `if analysis is not None:` before calling `show_keyword_match()` — no special handling needed inside the module.
- When 0 keywords match: show `"Keyword match: 0/N"` with no keyword list line — still useful feedback.
- When all keywords match: show count + full list normally.
- Minimum keyword length cutoff (e.g., skip single-char tokens like "C") left to the planner.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/ROADMAP.md` §Phase 7 — Goal, success criteria (3 items), requirements list (MATCH-01, MATCH-02, MATCH-03)
- `.planning/REQUIREMENTS.md` §JD Match Summary — Full requirement text for MATCH-01, MATCH-02, MATCH-03

### Source Files (read before writing)
- `src/cli.py` — Integration point: `show_keyword_match()` is called after `show_diff()` and before the final `print(f"Tailored resume written to: ...")`. The `analysis` dict (or `None`) is already available in `main()` from the `analyze_job_description()` call.
- `src/diff_view.py` — Pattern reference: TTY-gating with `sys.stdout.isatty()`, single public entry point `show_diff(original, tailored)`, never raises. `keyword_matcher.py` follows the same structure.
- `src/jd_analyzer.py` — Defines the analysis dict structure: `{"technologies": [...], "requirements": [...], "emphasis_areas": [...]}` — these are the keyword source fields.
- `src/guards.py` — Pattern reference for non-fatal module with one public entry point and `try/except Exception` guard.

### Prior Phase Context
- `.planning/phases/06-two-pass-pipeline/06-CONTEXT.md` — Analysis dict format (D-01: three-key JSON), fallback behavior (D-02: `None` return on failure), and progress message pattern (D-03/D-04).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sys.stdout.isatty()` TTY check in `src/diff_view.py` — exact predicate to reuse in `keyword_matcher.py` for MATCH-03
- `src/jd_analyzer.py` `analyze_job_description()` — returns `dict | None`; the dict's three lists are the keyword source; `None` means pass-1 failed and caller skips the match summary
- `re` module (stdlib) — already available; whole-word regex pattern: `r'\b' + re.escape(kw.lower()) + r'\b'` with `re.IGNORECASE`

### Established Patterns
- **Single-concern module + one public entry point**: `guards.py` exports `run_guards()`, `diff_view.py` exports `show_diff()`, `jd_analyzer.py` exports `analyze_job_description()`. New `keyword_matcher.py` exports `show_keyword_match()`.
- **Never raises**: `show_diff()` and `run_guards()` both wrap bodies in `try/except Exception`. `show_keyword_match()` follows the same pattern — a matching failure should not abort the run.
- **No new dependencies**: stdlib `re` + no imports beyond existing modules. Stays within stdlib + `requests` constraint.
- **flush=True on progress**: Not applicable here — match summary is post-processing output, not a progress message.

### Integration Points
- `src/cli.py` `main()` — new call sequence in the `try` block:
  ```python
  show_diff(resume_text, result.content)          # existing
  if analysis is not None:                        # existing guard
      show_keyword_match(analysis, result.content) # NEW
  print(f"Tailored resume written to: ...")       # existing
  ```
- `src/keyword_matcher.py` — new file; no existing file to modify

</code_context>

<specifics>
## Specific Ideas

- Output example the user expects:
  ```
  Keyword match: 14/20
    Python, FastAPI, RAG, Docker, LLM, fine-tuning, vector store, TypeScript
  ```
- `STOP_WORDS` should be a `frozenset` (O(1) lookup), not a list.
- Keywords pool all three analysis categories together before filtering — no category headers in output.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-JD Keyword Match Summary*
*Context gathered: 2026-06-08*
