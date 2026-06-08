---
phase: 04-output-reliability-guards
reviewed: 2026-06-04T14:00:25Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/cli.py
  - src/cli_test.py
  - src/guards.py
  - src/guards_test.py
  - src/llm_client.py
  - src/llm_client_test.py
findings:
  critical: 3
  warning: 5
  info: 2
  total: 10
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-06-04T14:00:25Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Six files were reviewed covering the output-reliability-guards implementation: the guards module, LLM client, CLI entry point, and their respective test suites. Three critical defects were found. The employer hallucination guard iterates in the wrong direction — it catches removed employers but entirely misses newly invented ones, the opposite of its stated purpose. The LaTeX validator uses a substring check for `\end{document}` so LLM output with trailing prose passes silently and is written to disk. The `_strip_fences` implementation only removes outermost fences, leaving mid-document fence residue that passes both validation and the format-violation guard when prose follows the closing `\end{document}`. Together, these three bugs can allow corrupt or LLM-hallucinated content through to the output file, defeating the phase's entire purpose.

---

## Critical Issues

### CR-01: `_check_hallucinated_employers` detects the wrong direction — actual hallucinations pass undetected

**File:** `src/guards.py:37-39`
**Issue:** The function iterates over `original_employers` and warns when one is *absent* from `tailored_employers`. This detects *dropped* employers (truncation), not *hallucinated* ones (LLM invention). A brand-new employer fabricated by the LLM (present in `tailored` but absent from `original`) is never checked and passes silently. The function name `_check_hallucinated_employers` is therefore a misnomer for the direction that matters most. For example, if the original has no employer entries and the tailored output contains `\employer{FakeCompany}{2023}{CTO}`, the guard emits zero warnings.

**Fix:** Add a second loop checking the reverse direction — employers in `tailored` not present in `original`:

```python
def _check_hallucinated_employers(original: str, tailored: str) -> None:
    try:
        original_employers = _EMPLOYER_PATTERN.findall(original)
        tailored_employers = _EMPLOYER_PATTERN.findall(tailored)
        for name, dates, title in original_employers:
            if (name, dates, title) not in tailored_employers:
                logger.warning(f'Employer "{name}" from original resume not found in tailored output.')
        for name, dates, title in tailored_employers:
            if (name, dates, title) not in original_employers:
                logger.warning(f'Employer "{name}" in tailored output was not in original resume — possible hallucination.')
    except Exception as exc:
        logger.warning(f"Employer check failed: {exc}")
```

---

### CR-02: `_validate_latex` uses substring check — trailing prose after `\end{document}` passes validation

**File:** `src/llm_client.py:121`
**Issue:** `_validate_latex` checks `"\\end{document}" in text` (a substring test). Any text appearing *after* `\end{document}` is invisible to the check. When an LLM appends an explanation paragraph after the document, the output passes validation and is written to disk as a corrupt `.tex` file. For example:

```
\documentclass{article}
...
\end{document}

Here is a summary of the changes I made to your resume...
```

This passes `_validate_latex` today and would be saved as the output.

**Fix:** Assert that `\end{document}` appears at the end of the string (after stripping trailing whitespace):

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

### CR-03: `_strip_fences` only removes outermost fence pair — mid-document fence plus trailing prose corrupts output silently

**File:** `src/llm_client.py:109-113`
**Issue:** The trailing fence regex `r"\n?```$"` anchors to the very end of the string without `re.MULTILINE`. If the LLM wraps the LaTeX in fences and then appends an explanation, for example:

```
```latex
\documentclass{article}
\end{document}
```

Here is what I changed...
```

After `_strip_fences` runs: the opening fence is removed but the closing ` ``` ` in the middle is not, and the trailing explanation remains. The resulting `content` contains a stray ` ``` ` and prose. This then passes `_validate_latex` because `\documentclass` is present at the start and `\end{document}` is present as a substring (CR-02). The `_check_format_violations` guard in `guards.py` detects the stray fence and logs a warning, but `cli.py:51-52` does not treat guard warnings as fatal — `write_resume` is called regardless. The corrupt file is written to disk.

**Fix:** Applying the CR-02 fix (enforcing `\end{document}` as terminal) closes this attack surface entirely. `_validate_latex` will reject the trailing prose, regardless of fence stripping completeness.

---

## Warnings

### WR-01: `_check_missing_sections` uses substring match — section names produce false negatives

**File:** `src/guards.py:13`
**Issue:** The check `if section not in tailored` is a plain Python substring search over the entire tailored document. A section named `"Skills"` is considered present if the word `"Skills"` appears *anywhere* — including in a bullet point like `"Python skills include..."` — even if `\header{Skills}` was removed entirely. The guard silently misses a structurally absent section header whenever the section name string coincidentally appears in content text.

**Fix:** Check for the LaTeX structural command, not the bare section name:

```python
for section in original_sections:
    if f'\\header{{{section}}}' not in tailored:
        logger.warning(f'Section "{section}" missing from tailored output.')
```

---

### WR-02: `_check_ollama_health` does not call `raise_for_status` — HTTP error responses are treated as healthy

**File:** `src/llm_client.py:14-20`
**Issue:** `_check_ollama_health` calls `requests.get(...)` but never inspects the response status code. If Ollama is running but returns HTTP 500 (e.g., model load failure), the health check passes. The subsequent POST to `/api/chat` will likely also fail, but with a less informative error than the health check was designed to surface. Additionally, if any `requests.HTTPError` were raised (e.g., by a proxy), it propagates through `generate_tailored_resume` uncaught and reaches `cli.py` line 53, which only catches `(RuntimeError, ValueError, FileNotFoundError, OSError)` — producing a raw Python traceback instead of a clean error message.

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
**Issue:** The pattern `r'\*\*\S[^*]*\S\*\*'` requires at least two non-`*` characters between the `**` delimiters (`\S` anchor, then `[^*]*` zero-or-more, then `\S` anchor). A single-character bold like `**X**` or `**I**` is not detected. While uncommon, single-character bold markers are valid Markdown syntax and invalid LaTeX prose — they should trigger the warning.

**Fix:**

```python
if re.search(r'\*\*[^*]+\*\*', tailored):
    logger.warning("Tailored output contains markdown bold markers.")
```

---

### WR-04: `cli_test.py` patches `run_guards` but never asserts it was called

**File:** `src/cli_test.py:16, 35, 97, 120`
**Issue:** All four success-path and happy-path tests accept `mock_guards` as a parameter (from `@patch("cli.run_guards")`) but no test asserts `mock_guards.assert_called_once()` or `mock_guards.assert_called_once_with(...)`. The tests would pass even if the `run_guards(...)` call at `cli.py:51` were deleted entirely. Guard integration on the happy path is completely unverified.

**Fix:** Add at minimum one assertion in a success-path test:

```python
mock_guards.assert_called_once_with(
    "resume text",
    "\\documentclass{article}\n\\end{document}",
    False,
)
```

---

### WR-05: `cli_test.py` error-path tests do not patch `cli.run_guards` — fragile implicit ordering

**File:** `src/cli_test.py:59-72`
**Issue:** `test_runtime_error_from_llm_exits_1` and `test_value_error_from_llm_exits_1` mock `cli.read_resume` and `cli.generate_tailored_resume` but not `cli.run_guards`. Since `generate_tailored_resume` raises before `run_guards` is reached, the tests pass today. However, if call order changes (e.g., guards moved to run before or alongside generation), real guard logic would execute against mock strings, potentially causing test pollution or intermittent failures. The lack of `@patch("cli.run_guards")` is an implicit ordering assumption in the test.

**Fix:** Add `@patch("cli.run_guards")` to both tests for explicit, order-independent isolation, consistent with all other tests in the file.

---

## Info

### IN-01: `guards.py` — `import sys` is unused

**File:** `src/guards.py:2`
**Issue:** `sys` is imported at line 2 but never referenced anywhere in `guards.py`. All logging goes through `log_manager.logger`, not `sys.stderr` directly.

**Fix:** Remove the line:
```python
import sys  # remove this
```

---

### IN-02: `guards_test.py` has a redundant `sys.path.insert` not present in sibling test files

**File:** `src/guards_test.py:6`
**Issue:** `sys.path.insert(0, str(Path(__file__).parent))` is present in `guards_test.py` but absent from `cli_test.py` and `llm_client_test.py`. `pyproject.toml` already sets `pythonpath = ["src"]` for pytest, making this manual path insertion redundant. The inconsistency is confusing and the `Path` import it requires adds noise unused elsewhere in the test file.

**Fix:** Remove lines 1-6 from `guards_test.py` (`import sys`, `from pathlib import Path`, and `sys.path.insert(...)`). The `Path` import is only there for the path manipulation; removing both is safe.

---

_Reviewed: 2026-06-04T14:00:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
