# Phase 07: JD Keyword Match Summary - Research

**Researched:** 2026-06-08
**Domain:** Python stdlib `re` module, TTY-gating pattern, single-concern module pattern
**Confidence:** HIGH

## Summary

Phase 07 adds a post-tailoring keyword match summary that measures JD alignment by checking which extracted keywords appear in the tailored resume. All decisions are locked in CONTEXT.md; there are no open technology choices. The implementation is entirely stdlib — `re`, `sys`, `frozenset` — with no new dependencies.

The domain is simple but has one verified pitfall: `\b` word-boundary anchors do not work for keywords containing only non-word characters (e.g., `C++`). Since `re.escape("C++")` produces `C\+\+` and `+` is a non-word character, `\bC\+\+\b` never matches. This is a known `re` module behavior, verified in this session. The CONTEXT.md-specified pattern (`\b + re.escape(kw.lower()) + \b`) works correctly for all alphanumeric keywords and hyphenated terms; the C++ limitation should be documented in the module and accepted as a known edge case.

The new `src/keyword_matcher.py` follows the exact same structural pattern as `src/diff_view.py` (TTY-gate, single public entry point, never raises). Integration into `src/cli.py` is a three-line change. Tests belong in `src/keyword_matcher_test.py` following the `unittest.TestCase` style used by `diff_view_test.py` and `guards_test.py`.

**Primary recommendation:** Implement `src/keyword_matcher.py` as a direct structural copy of `diff_view.py`'s scaffolding. The matching logic is the sole new concern.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Display format: header line `"Keyword match: N/M"` followed by matched keywords as a flat comma-separated list on next line (e.g., `"  Python, FastAPI, RAG, Docker"`). Not grouped by category.
- **D-02:** Position in CLI output flow: after `show_diff()`, before `"Tailored resume written to: ..."`.
- **D-03:** TTY-gated via `sys.stdout.isatty()` — same predicate as `show_diff()`. No flag needed.
- **D-04:** Minimal stop word list (~15 words): `a, an, the, and, or, of, in, to, for, with, is, are, be, on, at`. Defined as module-level `frozenset` named `STOP_WORDS`.
- **D-05:** Whole-word regex matching: `re.search(r'\b' + re.escape(kw.lower()) + r'\b', tailored_lower)` with `re.IGNORECASE`. All three analysis dict fields pooled together, after stop word filtering.
- **D-06:** New module `src/keyword_matcher.py` — single-concern, mirrors `guards.py` / `diff_view.py` / `jd_analyzer.py`.
- **D-07:** Single public entry point `show_keyword_match(analysis: dict, tailored_text: str) -> None`. Never raises (wraps in `try/except Exception`).

### Claude's Discretion

- Minimum keyword length cutoff (e.g., skip single-char tokens) — left to planner.
- 0-match output: show `"Keyword match: 0/N"` with no keyword list line (confirmed in CONTEXT.md edge cases).
- Caller (`cli.py`) guards with `if analysis is not None:` before calling — no special handling inside the module.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MATCH-01 | After tailoring, tool displays which keywords from pass-1 analysis appear in the tailored resume | `show_keyword_match()` prints "Keyword match: N/M" header + comma-separated matched keywords; keywords pooled from all three analysis dict fields |
| MATCH-02 | Keyword matching uses whole-word regex with stop word filtering to prevent substring false positives | `re.search(r'\b' + re.escape(kw.lower()) + r'\b', tailored_lower, re.IGNORECASE)` verified working; `STOP_WORDS` frozenset filters noise words before matching |
| MATCH-03 | Match summary displayed to stdout only when running interactively (TTY guard, same as diff) | `sys.stdout.isatty()` predicate identical to `diff_view.py` — verified pattern in codebase |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Keyword extraction source | API / Backend (jd_analyzer.py) | — | Already implemented in Phase 6; analysis dict is the output |
| Keyword matching logic | CLI tool module (keyword_matcher.py) | — | Pure string matching, no external service; belongs in new single-concern module |
| TTY detection | CLI tool module (keyword_matcher.py) | — | `sys.stdout.isatty()` is a process-level check, belongs in display module |
| Integration wiring | CLI entry point (cli.py) | — | `main()` already owns the call sequence; three-line addition |

## Standard Stack

### Core

No new packages. All implementation uses Python stdlib.

| Module | Source | Purpose | Why |
|--------|--------|---------|-----|
| `re` | stdlib | Whole-word keyword matching | `re.search()` with `\b` anchors and `re.IGNORECASE`; already imported in `jd_analyzer.py` and `guards.py` |
| `sys` | stdlib | TTY detection | `sys.stdout.isatty()` — identical to `diff_view.py` |
| `frozenset` | stdlib built-in | STOP_WORDS constant | O(1) membership test; immutable; named constant pattern |

### No New Dependencies

Phase constraint: stdlib + `requests` only. This phase uses zero external packages beyond what is already installed. [VERIFIED: codebase inspection — `pyproject.toml` dependencies section]

## Package Legitimacy Audit

No new packages installed in this phase. Audit section not applicable.

## Architecture Patterns

### System Architecture Diagram

```
cli.py main()
    |
    |-- analyze_job_description() --> analysis dict | None   [jd_analyzer.py]
    |
    |-- generate_tailored_resume() --> TailorResult          [llm_client.py]
    |
    |-- run_guards()                                          [guards.py]
    |
    |-- write_resume()                                        [resume_writer.py]
    |
    |-- show_diff(resume_text, result.content)                [diff_view.py]
    |
    |-- if analysis is not None:
    |       show_keyword_match(analysis, result.content)      [keyword_matcher.py] <-- NEW
    |
    `-- print("Tailored resume written to: ...")
```

### Recommended Project Structure

```
src/
├── cli.py                  # integration point: 3-line addition
├── keyword_matcher.py      # NEW: single public entry point show_keyword_match()
├── keyword_matcher_test.py # NEW: unittest.TestCase style, mirrors diff_view_test.py
├── diff_view.py            # pattern reference for TTY-gate and never-raises
├── guards.py               # pattern reference for non-fatal module
├── jd_analyzer.py          # source of analysis dict structure
└── ...                     # other existing modules unchanged
```

### Pattern 1: Single-Concern Display Module (TTY-Gated, Never Raises)

**What:** A module with one public entry point that (1) checks the TTY before doing any work, (2) wraps the entire body in `try/except Exception`, (3) imports only stdlib.

**When to use:** Any post-processing display operation that should not abort the main pipeline.

**Example — diff_view.py as the canonical template:** [VERIFIED: codebase read]
```python
# Source: src/diff_view.py (codebase)
def show_diff(original: str, tailored: str) -> None:
    if not sys.stdout.isatty():
        return
    # ... all logic here ...
    # No try/except at top level (diff_view doesn't need it — no external calls)
```

**keyword_matcher.py adaptation:** [ASSUMED — planner produces final code]
```python
# Illustrative structure only; planner writes the authoritative implementation
import re
import sys

STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "to", "for",
    "with", "is", "are", "be", "on", "at",
})

def show_keyword_match(analysis: dict, tailored_text: str) -> None:
    if not sys.stdout.isatty():
        return
    try:
        keywords = _collect_keywords(analysis)
        matched = _match_keywords(keywords, tailored_text)
        _print_summary(matched, len(keywords))
    except Exception:
        return

def _collect_keywords(analysis: dict) -> list[str]:
    raw: list[str] = []
    for field in ("technologies", "requirements", "emphasis_areas"):
        raw.extend(analysis.get(field, []))
    return [kw for kw in raw if kw.lower() not in STOP_WORDS]

def _match_keywords(keywords: list[str], tailored_text: str) -> list[str]:
    tailored_lower = tailored_text.lower()
    matched = []
    for kw in keywords:
        pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b", re.IGNORECASE)
        if pattern.search(tailored_lower):
            matched.append(kw)
    return matched

def _print_summary(matched: list[str], total: int) -> None:
    print(f"Keyword match: {len(matched)}/{total}")
    if matched:
        print(f"  {', '.join(matched)}")
```

### Pattern 2: Test Style — `unittest.TestCase` in `src/`

**What:** In-src test files using `unittest.TestCase` with `patch("sys.stdout")` for TTY simulation.

**When to use:** All new test files in `src/` follow this pattern (see `diff_view_test.py`, `guards_test.py`).

**Example — TTY gate test:** [VERIFIED: codebase read of `diff_view_test.py`]
```python
# Source: src/diff_view_test.py
def test_suppressed_when_not_tty(self):
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = False
        with patch("builtins.print") as mock_print:
            show_diff("original", "tailored changed")
            mock_print.assert_not_called()
```

### Anti-Patterns to Avoid

- **Grouping output by category:** D-01 is explicit — flat list, no category headers. Do not loop over `technologies`, `requirements`, `emphasis_areas` and print a header for each.
- **Raising on TTY=False:** The function must return silently, not raise `RuntimeError` or `ValueError`.
- **Modifying `run_guards()` or `show_diff()`:** This phase adds new behavior; existing modules are not changed.
- **Adding the call inside `show_diff()`:** Integration is in `cli.py main()`, not inside another display module.
- **Recompiling the regex inside the loop without `re.compile()`:** Acceptable either way in Python, but compiling once per keyword is consistent with the codebase's explicitness value.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTY detection | Custom file descriptor check | `sys.stdout.isatty()` | Already the established pattern in `diff_view.py`; stdlib, no gotchas |
| Word-boundary matching | Manual token split | `re.search(r'\b...\b', ...)` | Handles punctuation-adjacent words correctly; established pattern |
| Stop word lookup | Sequential list scan | `frozenset` membership | O(1) vs O(n); already decided in D-04 |
| Keyword deduplication | Custom set tracking | `list` is fine — LLM output is small; order matters for display | Don't over-engineer; dedup only if planner identifies real risk |

**Key insight:** Every problem in this phase has a stdlib solution that matches existing codebase idioms. No new library evaluation is needed.

## Common Pitfalls

### Pitfall 1: `\b` Does Not Match Around Non-Word Characters

**What goes wrong:** `re.search(r'\b' + re.escape('C++') + r'\b', text)` never matches, because `+` is a non-word character and `\b` requires a word/non-word boundary. `re.escape('C++')` produces `C\+\+`; since `+` is already `\W`, there is no word boundary after it.

**Why it happens:** `\b` is the zero-width assertion between `\w` ([a-zA-Z0-9_]) and `\W` (everything else). If the keyword starts or ends with a `\W` character, no boundary exists. [VERIFIED: Python `re` module behavior, confirmed via live test in this session]

**How to avoid:** The CONTEXT.md-specified pattern is correct for alphanumeric keywords (the vast majority). Accept C++ as a known limitation and document it in a comment in the module. Do not introduce lookahead/lookbehind alternatives — they add complexity not justified by the edge case frequency.

**Warning signs:** Zero matches for a keyword you know exists in the text; keyword contains `+`, `.`, `#`, or other non-word characters.

### Pitfall 2: Stop Word Comparison Case Sensitivity

**What goes wrong:** `kw.lower() not in STOP_WORDS` works correctly only if `STOP_WORDS` contains lowercased strings. If the analysis dict returns `"And"` and `STOP_WORDS` contains `"and"`, the comparison works — but only because `.lower()` is applied to `kw`.

**Why it happens:** The `STOP_WORDS` frozenset uses lowercase strings; comparison must always use `kw.lower()`, not `kw`.

**How to avoid:** Always apply `.lower()` to the keyword before the `in STOP_WORDS` check. The illustrative code above does this correctly.

**Warning signs:** Stop words appearing in matched keyword list.

### Pitfall 3: Missing `if analysis is not None:` Guard in `cli.py`

**What goes wrong:** Calling `show_keyword_match(None, result.content)` — the function receives `None` for `analysis`, and `analysis.get(...)` raises `AttributeError`. Even though `show_keyword_match` wraps in `try/except Exception`, this silently swallows a logic error.

**Why it happens:** The caller (`cli.py`) is responsible for the None guard per D-07 (CONTEXT.md). The function has no internal None check.

**How to avoid:** The integration code in `cli.py` must follow the exact pattern from CONTEXT.md:
```python
if analysis is not None:
    show_keyword_match(analysis, result.content)
```

**Warning signs:** `cli_test.py` tests that pass `analyze_job_description` returning `None` — verify `show_keyword_match` is not called in that path.

### Pitfall 4: `cli_test.py` Tests Fail Because `show_keyword_match` Is Not Patched

**What goes wrong:** Existing `cli_test.py` tests mock `show_diff` but will not mock `show_keyword_match` after integration. Tests that patch `builtins.print` may see unexpected output from the new call.

**Why it happens:** When `analysis` is not None and the test does not patch `show_keyword_match`, the function runs. If `sys.stdout.isatty()` returns `False` (typical in test environments), the function returns immediately — so this may not cause failures in practice. But tests that mock `analyze_job_description` to return a dict (not None) need to verify behavior.

**How to avoid:** Check each existing `cli_test.py` test. Tests that mock `analyze_job_description` returning a dict (currently only `test_generate_called_with_analysis_dict_when_analysis_succeeds`) may need `@patch("cli.show_keyword_match")` added. Verify by running the full test suite after integration.

**Warning signs:** Previously passing `cli_test.py` tests fail after integration; output assertions fail due to unexpected printed lines.

## Code Examples

Verified patterns from codebase:

### TTY Gate (from `diff_view.py`)
```python
# Source: src/diff_view.py (codebase read, verified)
def show_diff(original: str, tailored: str) -> None:
    if not sys.stdout.isatty():
        return
```

### Analysis Dict Structure (from `jd_analyzer.py`)
```python
# Source: src/jd_analyzer.py (codebase read, verified)
# Return value of analyze_job_description() when successful:
{
    "technologies": [...],    # list[str]
    "requirements": [...],    # list[str]
    "emphasis_areas": [...],  # list[str]
}
```

### CLI Integration Point (from `cli.py`, current state)
```python
# Source: src/cli.py (codebase read, verified)
# Current sequence in main() try block:
run_guards(resume_text, result.content, result.fences_stripped)
output_path = write_resume(result.content, output_dir)
show_diff(resume_text, result.content)
print(f"Tailored resume written to: {output_path.resolve()}")
# NEW lines slot in after show_diff():
# if analysis is not None:
#     show_keyword_match(analysis, result.content)
```

### Non-Fatal Pattern (from `guards_test.py`)
```python
# Source: src/guards_test.py (codebase read, verified)
# Test pattern for "never raises":
def test_run_guards_malformed_input_no_exception(self):
    run_guards(None, None)
```

### Test TTY Simulation (from `diff_view_test.py`)
```python
# Source: src/diff_view_test.py (codebase read, verified)
with patch("sys.stdout") as mock_stdout:
    mock_stdout.isatty.return_value = False
    with patch("builtins.print") as mock_print:
        show_diff("original", "tailored changed")
        mock_print.assert_not_called()
```

## State of the Art

No state-of-art research needed — this phase uses only Python stdlib `re` module behavior, which has been stable since Python 2. The `\b` word boundary behavior is documented and unchanged. [VERIFIED: live test in this session]

## Runtime State Inventory

Not applicable — this is a greenfield module addition, not a rename/refactor/migration phase.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (via `.venv`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q` |
| Full suite command | `/workspace/.venv/bin/pytest -x -q` |

Note: Python runtime in `.venv` is 3.14.5; project requires `>=3.13`. [VERIFIED: `.venv/bin/python --version`]

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MATCH-01 | `show_keyword_match` prints "Keyword match: N/M" header and comma-separated matched list | unit | `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q` | No — Wave 0 |
| MATCH-01 | When 0 keywords match, shows "Keyword match: 0/N" with no list line | unit | same | No — Wave 0 |
| MATCH-01 | Keywords pooled from all three analysis dict fields | unit | same | No — Wave 0 |
| MATCH-02 | `\b` regex matches whole words (not substrings) | unit | same | No — Wave 0 |
| MATCH-02 | Stop words are excluded from keyword pool | unit | same | No — Wave 0 |
| MATCH-03 | Output suppressed when `sys.stdout.isatty()` returns False | unit | same | No — Wave 0 |
| MATCH-03 | Output appears when `sys.stdout.isatty()` returns True | unit | same | No — Wave 0 |
| MATCH-01/03 | `show_keyword_match` never raises (not tty, empty analysis fields, malformed text) | unit | same | No — Wave 0 |
| Integration | `cli.py` calls `show_keyword_match` when analysis is not None | unit (cli_test) | `/workspace/.venv/bin/pytest src/cli_test.py -x -q` | Exists — needs new test |

### Sampling Rate

- **Per task commit:** `/workspace/.venv/bin/pytest src/keyword_matcher_test.py -x -q`
- **Per wave merge:** `/workspace/.venv/bin/pytest -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `src/keyword_matcher_test.py` — covers MATCH-01, MATCH-02, MATCH-03 (entire new test file)
- [ ] `src/cli_test.py` — add test: `show_keyword_match` called when analysis is not None (new test case in existing file)
- [ ] `src/cli_test.py` — verify existing test `test_generate_called_with_analysis_dict_when_analysis_succeeds` still passes after integration (may need `@patch("cli.show_keyword_match")`)

## Security Domain

This phase performs no network calls, file I/O, authentication, or user-controlled external inputs beyond the already-analyzed `analysis` dict (produced in Phase 6 from LLM output). No ASVS categories apply.

The analysis dict comes from a trusted internal call (`analyze_job_description()`) — not from direct user input. The tailored text comes from the LLM response, already processed by Phase 6. No injection vectors exist in the keyword matching logic.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Minimum keyword length cutoff implementation details | Architecture Patterns | Low — left to planner's discretion per CONTEXT.md |
| A2 | Single-char tokens (e.g., "C") will match frequently and produce noise | Common Pitfalls (implied) | Low — planner decides whether to add `len(kw) > 1` filter |

**All other claims in this research were verified via codebase inspection or live Python testing.**

## Open Questions

1. **Minimum keyword length cutoff**
   - What we know: CONTEXT.md says "left to the planner." Single-char keywords like "C" will match everywhere due to `\b` (e.g., "C" matches in "machine" — wait, no: `\bC\b` does NOT match "machine" because `\b` requires word boundary. It WOULD match "C programming" or standalone "C".)
   - What's unclear: Whether the LLM extraction ever returns single-char tokens in practice. The illustrative stop_words list doesn't include "C".
   - Recommendation: Add `len(kw.strip()) > 1` filter in `_collect_keywords()` to avoid noise without cluttering the stop words list. Planner's call.

2. **Whether `test_generate_called_with_analysis_dict_when_analysis_succeeds` needs `show_keyword_match` patching**
   - What we know: That test mocks `analyze_job_description` to return a dict. After integration, `show_keyword_match` will be called. The TTY check (`sys.stdout.isatty()`) in a test environment typically returns False, so the function exits immediately — likely safe without patching.
   - What's unclear: Whether any print-capturing test assertions will break.
   - Recommendation: Run the suite after integration and add `@patch("cli.show_keyword_match")` only if a test fails.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (venv) | All implementation | Yes | 3.14.5 | — |
| pytest | Test execution | Yes | 9.0.3 | — |
| `re` module | Keyword matching | Yes | stdlib | — |
| `sys` module | TTY detection | Yes | stdlib | — |

No missing dependencies. Step 2.6: all dependencies confirmed available.

## Sources

### Primary (HIGH confidence)

- `src/diff_view.py` — canonical TTY-gate + single-entry-point pattern [VERIFIED: codebase read]
- `src/guards.py` — canonical non-fatal module pattern [VERIFIED: codebase read]
- `src/jd_analyzer.py` — analysis dict structure (`technologies`, `requirements`, `emphasis_areas`) [VERIFIED: codebase read]
- `src/cli.py` — integration point and current call sequence [VERIFIED: codebase read]
- `src/diff_view_test.py` — test style and TTY simulation pattern [VERIFIED: codebase read]
- `pyproject.toml` — pytest config, test paths, pythonpath, markers [VERIFIED: codebase read]
- Python `re` module `\b` behavior — verified via live test in this session [VERIFIED: live execution]

### Secondary (MEDIUM confidence)

None required — all research grounded in direct codebase inspection and live testing.

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; everything is stdlib verified in codebase
- Architecture: HIGH — locked decisions from CONTEXT.md, structural pattern directly readable from diff_view.py
- Pitfalls: HIGH — verified via live Python testing (regex behavior) and codebase analysis (cli_test.py mock patterns)

**Research date:** 2026-06-08
**Valid until:** Stable — stdlib `re` module behavior has not changed in years; codebase patterns verified at research time. Valid until codebase is substantially refactored.
