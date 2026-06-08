---
phase: 07-jd-keyword-match-summary
reviewed: 2026-06-08T18:20:39Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - src/keyword_matcher.py
  - src/keyword_matcher_test.py
  - src/cli.py
  - src/cli_test.py
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-06-08T18:20:39Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed `keyword_matcher.py` (new module), `cli.py` (updated to call `show_keyword_match`), and their respective test files. The overall architecture is clean and the TTY gate, error suppression, and stop-word filtering are all correctly implemented. However, `_match_keywords` contains a word-boundary regex bug that causes common tech keywords ending or beginning with non-word characters (`C++`, `.NET`, `C#`) to silently return no match in every case. Additionally, the keyword pool does not deduplicate across the three analysis fields, inflating the reported total when the LLM repeats a keyword across fields.

---

## Critical Issues

### CR-01: `\b` word-boundary assertion silently fails for keywords containing non-word characters

**File:** `src/keyword_matcher.py:36`

**Issue:** The pattern is built as `r"\b" + re.escape(kw.lower()) + r"\b"`. The regex `\b` assertion requires a transition between a word character (`[A-Za-z0-9_]`) and a non-word character. When a keyword ends with a non-word character (e.g., `+` in `C++`, `#` in `C#`) or begins with one (e.g., `.` in `.NET`), the trailing `\b` (or leading `\b`) can never match because there is no word/non-word boundary adjacent to another non-word character. Confirmed via runtime test: `C++`, `.NET`, and `C#` return `None` for every possible surrounding context. These keywords are silently counted as unmatched, giving the user a misleading score with no indication of the failure.

```python
# Current (broken for C++, .NET, C#, etc.)
pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b", re.IGNORECASE)
if pattern.search(tailored_text.lower()):

# Fix: use lookahead/lookbehind to assert a non-word or string boundary
# without requiring the adjacent character itself to be a word character.
def _make_pattern(kw: str) -> re.Pattern:
    escaped = re.escape(kw.lower())
    # Use \b only on word-char sides; use (?<!\w) / (?!\w) on non-word-char sides.
    left = r"\b" if kw[0].isalnum() or kw[0] == "_" else r"(?<!\w)"
    right = r"\b" if kw[-1].isalnum() or kw[-1] == "_" else r"(?!\w)"
    return re.compile(left + escaped + right, re.IGNORECASE)
```

---

## Warnings

### WR-01: Duplicate keywords across analysis fields inflate the reported total

**File:** `src/keyword_matcher.py:21-30`

**Issue:** `_collect_keywords` iterates all three fields (`technologies`, `requirements`, `emphasis_areas`) and appends each keyword to the pool unconditionally. When the LLM repeats the same keyword across fields (e.g., `"Python"` in both `technologies` and `requirements`), it is added twice. Both copies then independently match the tailored text, producing output like `Keyword match: 4/4` for what is really 2 unique matched keywords out of 2 unique total. The inflated denominator misleads the user about actual coverage.

```python
# Fix: deduplicate the pool while preserving insertion order
def _collect_keywords(analysis: dict) -> list[str]:
    seen: set[str] = set()
    pool: list[str] = []
    for field in ("technologies", "requirements", "emphasis_areas"):
        for kw in analysis.get(field, []):
            if kw.lower() in STOP_WORDS:
                continue
            if len(kw.strip()) <= 1:
                continue
            key = kw.lower()
            if key not in seen:
                seen.add(key)
                pool.append(kw)
    return pool
```

### WR-02: Single-character filter silently excludes the `C` programming language

**File:** `src/keyword_matcher.py:27`

**Issue:** The guard `if len(kw.strip()) <= 1: continue` correctly removes noise tokens but also unconditionally drops `"C"` (the C programming language), a keyword that appears frequently in systems-engineering job descriptions. When `"C"` appears in the JD analysis, it is silently excluded from the pool and the reported total. The user sees a total that does not account for a keyword that was extracted, with no indication it was dropped. The test `test_single_char_excluded` documents this behavior as deliberate, but the design trades correctness for a blanket heuristic with no escape hatch.

The safest fix without over-engineering is to document it as a known limitation in a constant or comment, or apply a curated allow-list for known single-char language names:

```python
_SINGLE_CHAR_ALLOWLIST: frozenset[str] = frozenset({"c", "r"})  # programming languages

# In _collect_keywords:
key = kw.strip()
if len(key) <= 1 and key.lower() not in _SINGLE_CHAR_ALLOWLIST:
    continue
```

---

## Info

### IN-01: Redundant double-lowercasing in `_match_keywords`

**File:** `src/keyword_matcher.py:36-38`

**Issue:** The pattern already uses `re.escape(kw.lower())` (an explicitly lowercase pattern) AND has the `re.IGNORECASE` flag set. Additionally, `tailored_text.lower()` is passed to `pattern.search()`. These three operations are mutually redundant: a case-insensitive pattern searching lowercase text produces the same result as a case-sensitive lowercase pattern searching lowercase text. No bug results, but the redundancy obscures intent — a reader cannot tell whether `re.IGNORECASE` or `.lower()` is the intended mechanism. Pick one:

```python
# Option A: use IGNORECASE, drop explicit lowercasing
pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
if pattern.search(tailored_text):

# Option B: lowercase both sides, drop IGNORECASE
pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
if pattern.search(tailored_text.lower()):
```

### IN-02: Unnecessary mocks in several `cli_test.py` tests

**File:** `src/cli_test.py:63-71, 82-90, 100-109`

**Issue:** `test_empty_jd_exits_1` mocks `cli.read_resume` but the empty-JD check at `cli.py:45-47` runs before `read_resume` is called (line 50), so the mock is never invoked. Similarly, `test_runtime_error_from_llm_exits_1` and `test_value_error_from_llm_exits_1` mock `cli.run_guards`, but `generate_tailored_resume` raises before `run_guards` is reached, so those mocks are also dead. These phantom mocks add noise to the test's stated dependencies without providing coverage value.

---

_Reviewed: 2026-06-08T18:20:39Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
