---
phase: 07-jd-keyword-match-summary
reviewed: 2026-06-08T00:00:00Z
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
  info: 3
  total: 6
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-06-08
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

This phase adds `keyword_matcher.py` (a TTY-gated keyword match summary display) and integrates it into `cli.py`. The TTY gate, bare-except resilience pattern, stop-word filtering, and CLI integration are all well-structured. The test suite is broad. However, a critical correctness defect in the regex boundary logic causes false negatives for an entire class of technology keywords central to the tool's purpose (`C++`, `C#`, `.NET`). Two additional warnings flag a stop-word filter ordering bug and redundant lowercasing. Three info items note test coverage gaps and dead mocks.

---

## Critical Issues

### CR-01: `\b` word-boundary anchors silently fail for tech keywords ending in non-word characters

**File:** `src/keyword_matcher.py:36`

**Issue:** `_match_keywords` builds each pattern as `r"\b" + re.escape(kw.lower()) + r"\b"`. The `\b` assertion requires a transition between a word character (`[A-Za-z0-9_]`) and a non-word character at the match boundary. When a keyword ends with a non-word character — `+` in `C++`, `#` in `C#` — or begins with one — `.` in `.NET` — the trailing (or leading) `\b` can never be satisfied: there is no word/non-word boundary between two adjacent non-word characters. These patterns silently return no match for every possible resume text.

Confirmed by runtime test:

```python
import re
for kw in ["C++", "C#", ".NET"]:
    pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b", re.IGNORECASE)
    print(kw, bool(pattern.search(f"experience with {kw} and Python")))
# C++   False
# C#    False
# .NET  False
```

These are high-frequency keywords for the stated use case (AI/ML and software engineering job descriptions). The defect produces a misleading match count with no error or warning to the user.

**Fix:** Replace `\b` with negative lookaround assertions that do not depend on the character class of the keyword's terminal characters:

```python
def _match_keywords(keywords: list[str], tailored_text: str) -> list[str]:
    matched: list[str] = []
    for kw in keywords:
        pattern = re.compile(
            r"(?<!\w)" + re.escape(kw) + r"(?!\w)",
            re.IGNORECASE,
        )
        if pattern.search(tailored_text):
            matched.append(kw)
    return matched
```

`(?<!\w)` asserts that the character before the keyword is not a word character (or the match is at the start of the string). `(?!\w)` asserts the same for the character after. This correctly handles `C++`, `C#`, `.NET`, `Node.js`, and conventional alphanumeric keywords alike.

---

## Warnings

### WR-01: Stop-word filter does not strip whitespace before membership test

**File:** `src/keyword_matcher.py:25`

**Issue:** The stop-word check at line 25 is `if kw.lower() in STOP_WORDS`. It does not call `.strip()` before the lookup. If the LLM returns a keyword with surrounding whitespace (e.g., `" and "`), `kw.lower()` evaluates to `" and "`, which is not a member of `STOP_WORDS` (which contains `"and"` without spaces). The keyword passes the stop-word filter.

It then reaches the length check at line 27: `len(kw.strip()) <= 1`. `len(" and ".strip()) == 3`, so it also passes this guard and is appended to the pool. This inflates the `total` count reported in the summary output without the keyword ever being matchable in the resume text (the whitespace-padded escaped pattern cannot match clean prose). The user sees, for example, `Keyword match: 2/5` when the true denominator should be smaller.

**Fix:** Strip whitespace from `kw` once before all filter checks, reusing the stripped form throughout:

```python
def _collect_keywords(analysis: dict) -> list[str]:
    pool: list[str] = []
    for field in ("technologies", "requirements", "emphasis_areas"):
        for kw in analysis.get(field, []):
            kw = kw.strip()
            if kw.lower() in STOP_WORDS:
                continue
            if len(kw) <= 1:
                continue
            pool.append(kw)
    return pool
```

### WR-02: Redundant double-lowercasing in `_match_keywords`

**File:** `src/keyword_matcher.py:36-37`

**Issue:** The pattern is built using `re.escape(kw.lower())` (explicitly lowercase) and compiled with the `re.IGNORECASE` flag. The search at line 37 then additionally lowercases the search text: `pattern.search(tailored_text.lower())`. All three steps together are mutually redundant. `re.IGNORECASE` alone makes both the explicit `.lower()` on the pattern and the `.lower()` on the search text unnecessary. The redundancy obscures which mechanism is intended to provide case-insensitivity and signals uncertainty to future maintainers. No functional bug, but a maintainability defect.

**Fix:** Use `re.IGNORECASE` as the single case-folding mechanism and drop both explicit `.lower()` calls in this function (the stop-word lookup in `_collect_keywords` should keep its `.lower()`):

```python
def _match_keywords(keywords: list[str], tailored_text: str) -> list[str]:
    matched: list[str] = []
    for kw in keywords:
        pattern = re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE)
        if pattern.search(tailored_text):
            matched.append(kw)
    return matched
```

---

## Info

### IN-01: No test coverage for special-character technology keywords

**File:** `src/keyword_matcher_test.py`

**Issue:** The `TestShowKeywordMatchWholeWord` class tests that substrings are not matched and that punctuation-adjacent words are matched, but it contains no test exercising keywords whose names include non-word characters (`C++`, `C#`, `.NET`). Because of CR-01, these return zero matches in every case. A targeted test case would have caught the defect before shipping.

**Fix:** Add a test to `TestShowKeywordMatchWholeWord`:

```python
def test_special_char_tech_keywords_matched(self):
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        printed = []
        with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
            show_keyword_match(
                {"technologies": ["C++", "C#", ".NET"], "requirements": [], "emphasis_areas": []},
                "Experience with C++ and C# in the .NET ecosystem",
            )
        self.assertEqual(printed[0], "Keyword match: 3/3")
```

### IN-02: `test_shows_output_when_tty` uses an overly weak assertion

**File:** `src/keyword_matcher_test.py:22`

**Issue:** The assertion `self.assertTrue(len(printed) > 0)` only confirms that at least one `print` call was made. It does not verify format, count, or that the keyword name appears in the output. The test would pass even if `_print_summary` printed a single blank line, providing little protection against regressions.

**Fix:** Assert the header format explicitly:

```python
self.assertIn("Keyword match:", printed[0])
self.assertIn("Python", " ".join(printed))
```

### IN-03: `test_empty_jd_exits_1` and two error tests carry dead mocks

**File:** `src/cli_test.py:62-71, 82-90, 100-109`

**Issue:** `test_empty_jd_exits_1` applies `@patch("cli.read_resume")` and sets `mock_read.return_value = "resume text"`. In `cli.py`, the empty-JD guard (`sys.exit(1)` at line 47) fires before `read_resume` is called (line 50), so the mock is never invoked. Similarly, `test_runtime_error_from_llm_exits_1` and `test_value_error_from_llm_exits_1` apply `@patch("cli.run_guards")`; `generate_tailored_resume` raises before `run_guards` is reached (line 57), so those mocks are also dead. These phantom patches add noise to the test's stated dependency surface without contributing coverage.

**Fix:** Remove the unused `@patch("cli.read_resume")` decorator (and `mock_read` parameter) from `test_empty_jd_exits_1`, and remove the unused `@patch("cli.run_guards")` decorators (and `mock_guards` parameters) from the two LLM error tests.

---

_Reviewed: 2026-06-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
