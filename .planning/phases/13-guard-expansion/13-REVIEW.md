---
phase: 13-guard-expansion
reviewed: 2026-06-11T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - src/guards.py
  - tests/unit/test_guards.py
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-06-11
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `src/guards.py` (five guard functions checking LLM output integrity) and `tests/unit/test_guards.py` (pytest-style unit tests for two of those guards). The guard logic is largely sound — regex patterns are correct for LaTeX text, the exception-swallowing contract is consistently implemented, and the new tests cover happy-path and error-path cases.

One functional correctness gap was found: if the LLM removes the contact block entirely, no guard fires. One module-level duplication issue produces redundant warnings for the same employer-removal event. Two test-quality issues reduce the diagnostic value of the test suite without affecting test correctness.

---

## Critical Issues

### CR-01: Contact block entirely removed from tailored output produces no warning

**File:** `src/guards.py:82`

**Issue:** `_check_protected_sections` compares the contact block only when both `original_contact_m` and `tailored_contact_m` are non-`None`. When the LLM drops the entire `\begin{center}...\end{center}` block, `tailored_contact_m` is `None`, the condition is `False`, and no warning fires. The contact block holds the candidate's name, email, phone, and profile links — its complete removal would produce an unusable resume with zero user-facing alert.

This gap is not covered by any other guard: `_check_missing_sections` looks for `\header{...}` markers only; the contact block uses `\begin{center}` and has no header marker.

Verified by running `run_guards` with a multiline contact block in `original` and a `tailored` string with no `\begin{center}` block — zero warnings are produced.

**Fix:**

```python
# Replace the 'and' guard (line 82) with separate presence checks:
if original_contact_m is not None:
    if tailored_contact_m is None:
        logger.warning("Contact block was removed from tailored output.")
    elif original_contact_m.group(1).strip() != tailored_contact_m.group(1).strip():
        logger.warning("Contact block was modified in tailored output.")
```

The same logical gap exists for Education (line 87) and Languages (line 92), but those sections carry `\header{...}` markers and therefore ARE caught by `_check_missing_sections` when removed. Fix them with the same pattern for defense-in-depth:

```python
if original_education is not None:
    if tailored_education is None:
        logger.warning("Education section was removed from tailored output.")
    elif original_education.strip() != tailored_education.strip():
        logger.warning("Education section was modified in tailored output.")
```

---

## Warnings

### WR-01: Duplicate employer-removal warnings across two guards

**File:** `src/guards.py:37-38` and `src/guards.py:97-98`

**Issue:** When an employer entry is absent from the tailored output, two separate warnings are emitted:

1. `_check_hallucinated_employers` (line 37–38): `'Employer "Acme Corp" from original resume not found in tailored output.'`
2. `_check_protected_sections` (line 97–98): `'Employer header changed or removed: "Acme Corp"'`

For a single employer modification (different dates or title), three warnings fire: the two above plus a hallucination warning for the new tuple. The duplicate noise makes it harder for the user to identify distinct problems and creates two code paths that must stay synchronized.

The employer check inside `_check_protected_sections` is a strict subset of what `_check_hallucinated_employers` already covers — `_check_protected_sections` only reports removal while `_check_hallucinated_employers` reports both removal and addition.

**Fix:** Remove the employer-header block from `_check_protected_sections` (lines 95–98). The hallucination guard already covers the same condition with a more informative message:

```python
# Delete these four lines from _check_protected_sections:
original_headers = set(_EMPLOYER_PATTERN.findall(original))
tailored_headers = set(_EMPLOYER_PATTERN.findall(tailored))
for header in original_headers - tailored_headers:
    logger.warning(f'Employer header changed or removed: "{header[0]}"')
```

### WR-02: `test_run_guards_new_guards_never_raise` provides no correctness signal

**File:** `tests/unit/test_guards.py:132-133`

**Issue:** The test body is:

```python
def test_run_guards_new_guards_never_raise():
    run_guards(None, None)
```

It passes unconditionally for any implementation of the new guards, because all five guard functions internally catch `Exception` and log a warning. A completely empty guard body would also pass this test. The test name implies it is validating new guard behavior but it exercises only the exception-swallowing contract, which the existing `src/guards_test.py:TestRunGuardsNeverRaises` already covers with identical inputs (`None, None` and empty strings). The test adds no new signal.

**Fix:** Replace or supplement with a test that asserts the new guards produce expected warning messages for known inputs, similar to the other tests in the same file:

```python
@pytest.mark.unit
def test_run_guards_technology_substitution_guard_active():
    original = r"\header{Skills}" + "\nPython, Java\n" + r"\header{Education}"
    tailored = r"\header{Skills}" + "\nPython, Go\n" + r"\header{Education}"
    with patch("guards.logger") as mock_logger:
        run_guards(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Java" in c for c in calls)
        assert any("Go" in c for c in calls)
```

(This duplicates `test_run_guards_calls_technology_substitution` at line 121, but that test already exists — the point is to remove the zero-signal test and either delete it outright or replace it with a meaningful assertion.)

---

## Info

### IN-01: Split test ownership between two files for the same module

**File:** `src/guards_test.py` (all) and `tests/unit/test_guards.py` (all)

**Issue:** Guard tests are divided across two files without a clear boundary:

- `src/guards_test.py` — `unittest.TestCase` style, covers `_check_missing_sections`, `_check_format_violations`, `_check_hallucinated_employers`
- `tests/unit/test_guards.py` — pytest style, covers `_check_technology_substitution`, `_check_protected_sections`

The split makes it non-obvious which file to edit when adding tests for a new guard, and a contributor may duplicate coverage or miss existing cases. Both files are discovered by pytest (via `testpaths = ["src", "tests"]`), so both run, but the style inconsistency adds friction.

**Fix:** Migrate `src/guards_test.py` tests to `tests/unit/test_guards.py` using pytest style, and delete the source-colocated file. The `pyproject.toml` includes `src` in `testpaths` only because of these colocated test files; removing them allows narrowing that setting.

### IN-02: `test_protected_sections_warns_on_contact_diff` only tests single-line contact blocks

**File:** `tests/unit/test_guards.py:62-68`

**Issue:** The test uses:

```python
original = r"\begin{center}Name A\end{center}"
tailored = r"\begin{center}Name B\end{center}"
```

A real LaTeX contact block spans multiple lines. While the code correctly passes `re.DOTALL` to the search call, no test exercises the multi-line case. A future refactor that inadvertently drops the `re.DOTALL` flag (or moves the search to an inner helper without it) would not be caught.

**Fix:** Add a test variant with a multiline contact block:

```python
@pytest.mark.unit
def test_protected_sections_warns_on_contact_diff_multiline():
    original = "\\begin{center}\nName A\nEmail A\n\\end{center}"
    tailored = "\\begin{center}\nName B\nEmail B\n\\end{center}"
    with patch("guards.logger") as mock_logger:
        _check_protected_sections(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("contact" in c.lower() for c in calls)
```

---

_Reviewed: 2026-06-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
