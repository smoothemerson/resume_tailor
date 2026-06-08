---
phase: 05-diff-view
fixed_at: 2026-06-05T00:00:00Z
review_path: .planning/phases/05-diff-view/05-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 05: Code Review Fix Report

**Fixed at:** 2026-06-05T00:00:00Z
**Source review:** .planning/phases/05-diff-view/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01: `guards.py` omitted from wheel include list — `ImportError` at install time

**Files modified:** `pyproject.toml`
**Commit:** 849a77c
**Applied fix:** Added `"src/guards.py"` to the `[tool.hatch.build.targets.wheel] include` list between `diff_view.py` and `llm_client.py`, alphabetically ordered.

### WR-01: `show_diff` and success-message `print` are outside the error-handling `try` block in `cli.py`

**Files modified:** `src/cli.py`
**Commit:** 8b7061a
**Applied fix:** Moved `show_diff(resume_text, result.content)` and `print(f"Tailored resume written to: ...")` inside the `try` block so `BrokenPipeError` and `OSError` from those calls are handled cleanly. Also removed the redundant `FileNotFoundError` from the except tuple (it is a subclass of `OSError` and was already caught). The except clause is now `except (RuntimeError, ValueError, OSError)`.

### WR-02: `test_blank_line_collapse_not_shown_as_diff` is a tautological test — the normalization path is never exercised

**Files modified:** `src/diff_view_test.py`
**Commit:** 2a86ecf
**Applied fix:** Replaced identical-input strings `("a\n\n\n\nb", "a\n\n\n\nb")` with two distinct strings that differ in blank-run length but both collapse to the same normalized form: `("a\n\n\n\n\nb", "a\n\nb")`. The original has 4 blank lines, the tailored has 1; both collapse to at most 2 blank lines. A comment was added explaining the intent. The test now actually exercises the blank-line collapse logic in `_normalize`.

---

_Fixed: 2026-06-05T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
