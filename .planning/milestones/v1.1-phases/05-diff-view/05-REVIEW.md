---
phase: 05-diff-view
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/diff_view.py
  - src/diff_view_test.py
  - src/cli.py
  - src/cli_test.py
  - pyproject.toml
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-06-04T00:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

This phase introduced `diff_view.py` (TTY-gated colorized diff output) and integrated it into `cli.py`. The core `show_diff` logic is correct and the test coverage is reasonable. One deployment-breaking omission was found in `pyproject.toml`, one robustness gap in `cli.py` error handling, and two test quality defects in `diff_view_test.py`.

---

## Critical Issues

### CR-01: `guards.py` omitted from wheel include list — `ImportError` at install time

**File:** `pyproject.toml:18-26`
**Issue:** `cli.py` imports `from guards import run_guards` (line 7). `guards.py` is present in `src/` and the runtime depends on it, but it is absent from the explicit `[tool.hatch.build.targets.wheel] include` list. Every other module that `cli.py` imports is listed (`cli.py`, `config.py`, `diff_view.py`, `llm_client.py`, `log_manager.py`, `resume_reader.py`, `resume_writer.py`). When the package is built and installed via `pip install .`, `guards.py` is excluded from the wheel. Any invocation of `resume-tailor` after installation fails immediately with `ModuleNotFoundError: No module named 'guards'`.

**Fix:** Add `src/guards.py` to the `include` list:
```toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/diff_view.py",
    "src/guards.py",
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

---

## Warnings

### WR-01: `show_diff` and success-message `print` are outside the error-handling `try` block in `cli.py`

**File:** `src/cli.py:58-59`
**Issue:** The `try/except` in `cli.main()` spans lines 49–56. Lines 58–59 (`show_diff(...)` and `print(f"Tailored resume written to: ...")`) execute outside that block. If either raises an unhandled exception the user sees a raw Python traceback rather than a clean error message. The `show_diff` TTY guard (`sys.stdout.isatty()`) means this risk is low in piped scenarios, but `print()` can still raise `BrokenPipeError` or `OSError` on a live TTY when the terminal is closed mid-output. The final success message on line 59 has no such mitigation.

**Fix:** Extend the try block to cover both calls, or add a narrow `except OSError` around each:
```python
    try:
        resume_text = read_resume(resume_path)
        result = generate_tailored_resume(resume_text, job_description, model=args.model)
        run_guards(resume_text, result.content, result.fences_stripped)
        output_path = write_resume(result.content, output_dir)
        show_diff(resume_text, result.content)
        print(f"Tailored resume written to: {output_path.resolve()}")
    except (RuntimeError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### WR-02: `test_blank_line_collapse_not_shown_as_diff` is a tautological test — the normalization path is never exercised

**File:** `src/diff_view_test.py:33-38`
**Issue:** The test passes the identical string `'a\n\n\n\nb'` as both `original` and `tailored`. Identical inputs always produce an empty diff regardless of normalization, so the test passes whether or not `_normalize` is implemented at all. The test name claims to verify that blank-line collapse prevents spurious diffs between documents that differ only in blank-run length, but it never constructs two distinct inputs that collapse to the same normalized form. The collapse logic (`blank_count <= 2`) is untested by any test in the suite.

**Fix:** Replace the body with a test that presents two strings with differing blank-run lengths that should normalize to the same output:
```python
def test_blank_line_collapse_not_shown_as_diff(self):
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        with patch("builtins.print") as mock_print:
            # original has 4 blank lines; tailored has 1; both collapse to ≤2
            show_diff("a\n\n\n\n\nb", "a\n\nb")
            mock_print.assert_not_called()
```

---

## Info

### IN-01: `FileNotFoundError` is a redundant entry in the exception tuple in `cli.py`

**File:** `src/cli.py:54`
**Issue:** `FileNotFoundError` is a direct subclass of `OSError`. Listing both in the same `except` clause is redundant; `OSError` already catches `FileNotFoundError`.

**Fix:**
```python
    except (RuntimeError, ValueError, OSError) as e:
```

### IN-02: Test `test_empty_jd_exits_1` patches `read_resume` unnecessarily

**File:** `src/cli_test.py:55-65`
**Issue:** `cli.main()` exits at line 44–45 (the empty-JD guard) before ever calling `read_resume`. The `@patch("cli.read_resume")` decorator on this test patches a function that is never reached, adding noise without adding value.

**Fix:** Remove the `@patch("cli.read_resume")` decorator and its corresponding parameter from the test signature.

---

_Reviewed: 2026-06-04T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
