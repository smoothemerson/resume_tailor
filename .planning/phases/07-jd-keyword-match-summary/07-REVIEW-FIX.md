---
phase: 07-jd-keyword-match-summary
fixed_at: 2026-06-08T00:00:00Z
review_path: .planning/phases/07-jd-keyword-match-summary/07-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 07: Code Review Fix Report

**Fixed at:** 2026-06-08
**Source review:** .planning/phases/07-jd-keyword-match-summary/07-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3 (CR-01, WR-01, WR-02)
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01 + WR-02: Replace `\b` anchors with lookarounds and drop redundant lowercasing

**Files modified:** `src/keyword_matcher.py`
**Commit:** e247789
**Applied fix:** In `_match_keywords`, replaced `r"\b" + re.escape(kw.lower()) + r"\b"` with `r"(?<!\w)" + re.escape(kw) + r"(?!\w)"` and removed both the `kw.lower()` on the pattern and `tailored_text.lower()` on the search call. `re.IGNORECASE` is now the sole case-folding mechanism. This fixes silent false-negatives for keywords ending or starting with non-word characters (C++, C#, .NET) and eliminates redundant double-lowercasing.

### WR-01: Strip whitespace in `_collect_keywords` before filter checks

**Files modified:** `src/keyword_matcher.py`
**Commit:** bfa4da1
**Applied fix:** Added `kw = kw.strip()` as the first statement inside the inner loop in `_collect_keywords`, before the stop-word membership test and the length check. Also simplified `len(kw.strip()) <= 1` to `len(kw) <= 1` since `kw` is already stripped. Keywords with surrounding whitespace (e.g., `" and "`) are now correctly excluded from the pool.

---

_Fixed: 2026-06-08_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
