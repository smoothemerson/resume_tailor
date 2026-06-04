---
phase: 04-output-reliability-guards
reviewed: 2026-06-02T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/guards.py
  - src/guards_test.py
  - src/llm_client.py
  - src/llm_client_test.py
  - src/cli.py
  - src/cli_test.py
findings:
  critical: 3
  warning: 5
  info: 2
  total: 10
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-06-02T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Six files were reviewed covering the output-reliability-guards implementation: the guards module, LLM client, CLI entry point, and their respective test suites. The guards logic has two correctness inversions — one in section detection (substring vs structural match) and one in employer hallucination detection (checks the wrong direction entirely). The LLM output validator does not enforce that `\end{document}` is the terminal token, allowing corrupt outputs to pass and be written to disk. These three issues directly undermine the stated purpose of the phase: catching bad LLM output before it reaches the user.

---

## Critical Issues

### CR-01: `_check_hallucinated_employers` detects the wrong condition — actual hallucinations pass undetected

**File:** `src/guards.py:37-39`
**Issue:** The function iterates over `original_employers` and warns when one is *absent* from `tailored`. This detects *dropped* employers, not *hallucinated* ones. A brand-new employer fabricated by the LLM (present in `tailored` but absent from `original`) is never checked and passes silently. The function name `_check_hallucinated_employers` is therefore a misnomer for the direction that matters most: preventing invented content from reaching the output file.

```python
# Current — detects missing employers (deletion), not hallucinated ones (addition)
for name, dates, title in original_employers:
    if (name, dates, title) not in tailored_employers:
        logger.warning(f'Employer "{name}" from original resume not found in tailored output.')
```

**Fix:** Add a second loop to check the reverse direction — employers in `tailored` not present in `original`:

```python
# Detect dropped employers (existing logic, kept)
for name, dates, title in original_employers:
    if (name, dates, title) not in tailored_employers:
        logger.warning(f'Employer "{name}" from original resume not found in tailored output.')

# Detect hallucinated employers (new logic, the actual guard)
for name, dates, title in tailored_employers:
    if (name, dates, title) not in original_employers:
        logger.warning(f'Employer "{name}" in tailored output was not in original resume — possible hallucination.')
```

---

### CR-02: `_validate_latex` does not verify `\end{document}` is terminal — trailing prose passes validation

**File:** `src/llm_client.py:116-125`
**Issue:** `_validate_latex` checks `"\\end{document}" in text` (substring), so any text appearing *after* `\end{document}` is invisible to the check. When an LLM returns a valid LaTeX body followed by an explanation paragraph, or when `_strip_fences` fails to remove a mid-document closing fence (see CR-03), the result passes validation and is written to disk as a corrupt `.tex` file.

Concrete case that passes validation today:
```
\documentclass{article}
...
\end{document}

Here is a summary of the changes I made to your resume...
```

**Fix:** Assert that `\end{document}` appears at or near the end of the string (after stripping trailing whitespace):

```python
def _validate_latex(text: str) -> str:
    stripped = text.rstrip()
    if not stripped.lstrip().startswith("\\documentclass"):
        raise ValueError(
            "LLM response does not start with \\documentclass — output is not valid LaTeX."
        )
    if not stripped.endswith("\\end{document}"):
        raise ValueError(
            "LLM response does not end with \\end{document} — output may be truncated or contain trailing prose."
        )
    return text
```

---

### CR-03: `_strip_fences` only strips outermost fence pair — multi-fence or mid-doc fence responses corrupt output silently

**File:** `src/llm_client.py:109-113`
**Issue:** The regex `r"\n?```$"` anchors to the very end of the string without `re.MULTILINE`. If the LLM response is:

```
```latex
\documentclass{article}
\end{document}
```

Here is what I changed...
```

After stripping, the opening fence is removed but the closing fence in the middle is not, and the trailing explanation remains. The resulting `content` field is:

```
\documentclass{article}
\end{document}
```

Here is what I changed...
```

This contains a stray ` ``` ` and prose, but passes `_validate_latex` because `\documentclass` is at the start and `\end{document}` is present somewhere. The guards in `guards.py` detect the stray fence and log a warning, but they do not halt execution — `write_resume` is called anyway (see `cli.py:51-52`).

**Fix:** Combine with CR-02 (enforce `\end{document}` as terminal). The combined fix in `_validate_latex` rejects any output where `\end{document}` is not the last meaningful token, catching all variants of this failure mode regardless of fence stripping completeness.

---

## Warnings

### WR-01: `_check_missing_sections` uses substring match — section names can produce false negatives

**File:** `src/guards.py:13`
**Issue:** The check `if section not in tailored` is a plain Python substring search. A section named `"AI"` is considered present if the string `"AI"` appears anywhere in `tailored` — including inside `"FAIL"`, `"MAIL"`, `"DETAIL"`, or any content word. Similarly, `"Skills"` is considered present if `"SkillsSection"` or `"professional Skills in Python"` appears in the text. The guard silently misses a structurally absent `\header{Skills}` when the word "Skills" appears in any bullet point.

**Fix:** Check for the LaTeX command structure, not the bare section name:

```python
for section in original_sections:
    pattern = re.escape(section)
    if not re.search(rf'\\header\{{{pattern}\}}', tailored):
        logger.warning(f'Section "{section}" missing from tailored output.')
```

---

### WR-02: `_check_ollama_health` does not call `raise_for_status` — HTTP error responses are silently ignored

**File:** `src/llm_client.py:14-20`
**Issue:** `_check_ollama_health` calls `requests.get(...)` but never checks the response status code. If Ollama is running but returns an HTTP 500 (e.g., model load failure), the health check reports success. The subsequent `requests.post` to `/api/chat` will then also likely fail, but with a less informative `RuntimeError` than the health check was designed to provide.

**Fix:**

```python
def _check_ollama_health() -> None:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=TIMEOUT[0])
        response.raise_for_status()
    except requests.ConnectionError as exc:
        raise RuntimeError(f"Ollama is not reachable at {OLLAMA_BASE_URL}") from exc
    except requests.Timeout as exc:
        raise RuntimeError("Ollama health check timed out") from exc
    except requests.HTTPError as exc:
        raise RuntimeError(f"Ollama health check failed with HTTP error: {exc}") from exc
```

---

### WR-03: `_check_format_violations` bold regex misses single-character bold markers

**File:** `src/guards.py:27`
**Issue:** The pattern `r'\*\*\S[^*]*\S\*\*'` requires at least two non-`*` characters between the `**` delimiters (`\S` then `[^*]*` then `\S`). A single-character bold like `**X**` or `**I**` is not detected. While uncommon, a one-character bold marker (`**I**`) is still valid Markdown syntax and invalid LaTeX prose.

**Fix:**

```python
if re.search(r'\*\*[^*]+\*\*', tailored):
    logger.warning("Tailored output contains markdown bold markers.")
```

---

### WR-04: `guards_test.py` — `test_run_guards_malformed_input_no_exception` does not assert guard behavior on None inputs

**File:** `src/guards_test.py:107`
**Issue:** The test passes `None, None` to `run_guards` and asserts only that no exception is raised. This is underspecified: passing `None` hits the `except Exception` handlers in every sub-check, which silently swallow `TypeError`. The test does not verify that warnings were emitted, so future refactoring could accidentally re-raise and the test would still pass (it already expects no exception). The test gives false confidence that `None` is handled gracefully rather than just caught and discarded.

**Fix:** Assert that warnings were generated (guards detected the failure) rather than just asserting no exception:

```python
def test_run_guards_malformed_input_no_exception(self):
    with patch("guards.logger") as mock_logger:
        run_guards(None, None)
        self.assertGreater(mock_logger.warning.call_count, 0,
            "Expected warnings on malformed input, got none — error handling may be silently dropping exceptions")
```

---

### WR-05: `cli_test.py` — `test_runtime_error_from_llm_exits_1` does not patch `cli.run_guards`, leaving real guard execution in error path

**File:** `src/cli_test.py:59-72`
**Issue:** In `test_runtime_error_from_llm_exits_1` and `test_value_error_from_llm_exits_1`, `cli.read_resume` is mocked but `cli.run_guards` is not. Since `generate_tailored_resume` raises before `run_guards` is reached, the tests pass today. However, if the call order changes (e.g., guards called before `generate_tailored_resume`), the test would invoke real guard logic against the mock resume text string, potentially causing test pollution or flaky behavior. The tests are fragile due to implicit ordering assumptions.

**Fix:** Add `@patch("cli.run_guards")` to both tests consistent with the other tests in the file, even if the mock is never called — it makes the isolation explicit and order-independent.

---

## Info

### IN-01: `guards.py` — `import sys` is unused

**File:** `src/guards.py:2`
**Issue:** `sys` is imported but never referenced in `guards.py`. Logging is performed via `log_manager.logger`, not `sys.stderr` directly.

**Fix:** Remove the unused import:

```python
# Remove line 2: import sys
```

---

### IN-02: `_check_hallucinated_employers` function name is misleading given its current (inverted) behavior

**File:** `src/guards.py:33`
**Issue:** Even after fixing CR-01 to add the reverse check, the existing loop detects *dropped* employers (a different concern — resume truncation). Consider naming the two concerns clearly or splitting into `_check_dropped_employers` and `_check_hallucinated_employers`.

**Fix:** After applying CR-01's fix, rename for clarity:

```python
def _check_employer_integrity(original: str, tailored: str) -> None:
    # checks both dropped and hallucinated employers
```

Or split into two focused functions with accurate names.

---

_Reviewed: 2026-06-02T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
