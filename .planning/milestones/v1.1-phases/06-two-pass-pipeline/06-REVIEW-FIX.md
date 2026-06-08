---
phase: 06-two-pass-pipeline
fixed_at: 2026-06-07T12:30:00Z
review_path: .planning/phases/06-two-pass-pipeline/06-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-06-07T12:30:00Z
**Source review:** .planning/phases/06-two-pass-pipeline/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (CR-01, CR-02, CR-03, WR-01, WR-02, WR-03, WR-04)
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: Fence-stripping regex silently destroys content on bare fences

**Files modified:** `src/jd_analyzer.py`, `src/llm_client.py`
**Commit:** c5040ac
**Applied fix:** Replaced `^```\s*\w*\s*\n?` with `^```[^\n]*\n?` in both `_parse_analysis_response` (jd_analyzer.py) and `_strip_fences` (llm_client.py). The `[^\n]*` pattern correctly consumes only the optional language tag on the opening fence line without touching content on subsequent lines.

---

### CR-02: `_parse_analysis_response` calls `.keys()` on unguarded `json.loads` result

**Files modified:** `src/jd_analyzer.py`
**Commit:** d689d55
**Applied fix:** Added `if not isinstance(parsed, dict): return None` immediately after `json.loads()` and before `parsed.keys()`, ensuring valid but non-dict JSON (arrays, scalars, booleans) returns `None` rather than raising `AttributeError`.

---

### CR-03: `analyze_job_description` raises `RuntimeError` on truncation — kills entire pipeline

**Files modified:** `src/jd_analyzer.py`, `tests/unit/test_jd_analyzer.py`
**Commit:** fb6f2ad
**Applied fix:** Replaced `raise RuntimeError(...)` and `except RuntimeError: raise` in `analyze_job_description` with `return None` when `done_reason == "length"`, so a truncated best-effort analysis step degrades gracefully to single-pass mode. Updated `test_analyze_job_description_raises_runtime_error_on_truncation` → renamed to `test_analyze_job_description_returns_none_on_truncation` and updated assertion to `assert result is None`.

---

### WR-01: Silent degradation — analysis failure produces no user-visible signal

**Files modified:** `src/cli.py`
**Commit:** b29f5ff
**Applied fix:** Added `if analysis is None: print("Warning: JD analysis failed; proceeding with single-pass tailoring.", file=sys.stderr)` after the `analyze_job_description` call so the user can distinguish a two-pass run from a silent single-pass fallback.

---

### WR-02: `read_resume` called after `analyze_job_description` — expensive LLM call wasted when resume is missing

**Files modified:** `src/cli.py`
**Commit:** 21cc917
**Applied fix:** Moved `resume_text = read_resume(resume_path)` to the first line inside the `try` block, before `analyze_job_description`, and moved `print("Analyzing job description...", flush=True)` to immediately follow it. Resume file validation now fails fast before any LLM call is made.

---

### WR-03: `_parse_analysis_response` accepts non-list values for list-typed fields

**Files modified:** `src/jd_analyzer.py`
**Commit:** 1fc924b
**Applied fix:** Added `if not all(isinstance(parsed[k], list) for k in required_keys): return None` after the required-keys check, so string values passed for list-typed fields are rejected rather than silently forwarded as malformed context.

---

### WR-04: `KeyError` from malformed `analysis` dict propagates unhandled through `cli.py`

**Files modified:** `src/llm_client.py`
**Commit:** 8095781
**Applied fix:** Replaced direct `analysis['technologies']`, `analysis['requirements']`, `analysis['emphasis_areas']` access in `_build_messages` with `.get("key", [])` calls, so a dict missing any of the three expected keys yields an empty list rather than an unhandled `KeyError`.

---

_Fixed: 2026-06-07T12:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
