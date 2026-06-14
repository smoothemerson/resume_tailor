---
phase: 12-prompt-precision
reviewed: 2026-06-13T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/llm_client.py
  - src/guards.py
  - src/cli.py
  - src/guards_test.py
  - tests/unit/test_llm_client.py
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-06-13T00:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Five files were reviewed covering the LLM client, output guards, CLI entry point, and their unit tests. The prompt engineering work in `llm_client.py` is solid — the structured XML prompt, `<ALLOWED>` / `<CONSTRAINTS>` separation, fence-stripping logic, and truncation detection are all correct. The critical finding is in `guards.py`: the employer-hallucination guard is permanently non-functional because its regex targets a LaTeX command (`\employer{}{}{}`) that does not exist in this project's resume template format. The remaining findings are quality and reliability issues in the guard checks, CLI, and test infrastructure.

## Critical Issues

### CR-01: Employer Hallucination Guard Is Permanently Non-Functional — Wrong LaTeX Command

**File:** `src/guards.py:6`

**Issue:** `_EMPLOYER_PATTERN` is compiled as:

```python
_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
```

This matches a custom LaTeX command of the form `\employer{name}{dates}{title}`. However, the actual resume template (described authoritatively in the `llm_client.py` system prompt at line 80) uses:

```
\textbf{EMPLOYER}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES\\
```

No `\employer` command exists in this template. As a result, `_EMPLOYER_PATTERN.findall()` always returns an empty list for both `original` and `tailored`, the inner loops in `_check_hallucinated_employers` never execute, and the function silently passes with zero detections on every invocation. The guard provides false confidence: it appears to check that employers were not hallucinated but actually checks nothing.

The tests in `guards_test.py` (lines 84-99) also use `\employer{Acme Corp}{2022}{Engineer}` as fixtures, meaning those tests validate only that the fictional pattern matches fictional fixture data — not any behavior that occurs with a real resume.

**Fix:** Replace the pattern with one that matches the actual template employer line format. The employer block is identified by `\textbf{COMPANY}\textbf{ | ROLE}`:

```python
_EMPLOYER_PATTERN = re.compile(
    r'\\textbf\{([^}]+)\}\\textbf\{\s*\|\s*([^}]+)\}'
)
```

Update `_check_hallucinated_employers` to unpack two-tuples `(company, role)`. Update `guards_test.py` fixtures to use the real format:

```python
original = r"\textbf{Acme Corp}\textbf{ | Engineer}"
tailored = r"\documentclass{article}\n\end{document}"
```

## Warnings

### WR-01: System Prompt Sent to LLM Contains 8-Space Indentation on Every Interior Line

**File:** `src/llm_client.py:27-116`

**Issue:** The `system_prompt` triple-quoted raw string is indented inside the function body (8 spaces per line). The `.strip()` call at line 116 removes only the leading newline and trailing whitespace from the whole string; it does not dedent interior lines. Every line between the opening `<PERSONA>` and closing `</OUTPUT_FORMAT>` tag (except the very first, which `.strip()` un-indents) is prefixed with 8 spaces in the actual HTTP payload delivered to Ollama.

While modern LLMs generally tolerate this, it means the content received by the model differs significantly from the source — a maintainability and prompt hygiene issue. The `<ALLOWED>` and `<CONSTRAINTS>` sections run to roughly 80 lines; all of that content has spurious leading whitespace that was never intended.

**Fix:** Use `textwrap.dedent` (stdlib, no new dependency):

```python
import textwrap

system_prompt = textwrap.dedent(r"""
    <PERSONA>
    You are Alexandra, a senior technical recruiter...
    </PERSONA>
    ...
""").strip()
```

This produces a clean prompt where every line starts without artificial indentation.

### WR-02: `_validate_latex` Return Type Is Misleading — Return Value Always Discarded

**File:** `src/llm_client.py:152-162, 212`

**Issue:** `_validate_latex` is declared `-> str` and returns the input `text` unchanged (line 162). At line 212 the call is `_validate_latex(content)` with the return value discarded. The function is used solely for its side effect (raising `ValueError` on invalid LaTeX). The `-> str` return annotation implies the function is a transformation step, when it is a pure validator. A future maintainer who writes `content = _validate_latex(content)` expecting normalization would silently get back the pre-`rstrip` version — the internal `rstrip()` is used only for the check, not returned.

**Fix:** Change the return type to `None` and remove the return statement:

```python
def _validate_latex(text: str) -> None:
    stripped = text.rstrip()
    if not stripped.lstrip().startswith("\\documentclass"):
        raise ValueError(
            "LLM response does not start with \\documentclass — output is not valid LaTeX."
        )
    if not stripped.endswith("\\end{document}"):
        raise ValueError(
            "LLM response does not end with \\end{document} — output may be truncated or contain trailing prose."
        )
```

The call site at line 212 requires no change.

### WR-03: `guards_test.py` Uses `sys.path.insert` Under `importlib` Test Mode — Risks Mock Targeting Failures

**File:** `src/guards_test.py:1-6`

**Issue:** Lines 1-6 of `guards_test.py` manually insert the file's own parent directory (`src/`) into `sys.path`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

The project's `pyproject.toml` already sets `pythonpath = ["src"]` and `--import-mode=importlib`. Under `importlib` mode, pytest resolves module imports through Python's import machinery directly, not through `sys.path` manipulation. The manual `sys.path.insert` causes the `guards` module to be importable through two separate mechanisms in the same test session.

This creates a double-import risk: when `patch("guards.logger")` is applied, it patches the `guards` module object that was resolved via `sys.path` — which may differ from the `guards` module object that `importlib` mode loaded for pytest's discovery. If the two are distinct objects in `sys.modules`, the mock patches a different `logger` than the one the production code calls, and `mock_logger.warning.assert_called_once_with(...)` passes trivially while the actual warning was sent to a different logger instance.

**Fix:** Remove lines 1-6 from `guards_test.py`. The `pythonpath = ["src"]` configuration in `pyproject.toml` already makes `import guards` work under `importlib` mode:

```python
# Remove these three lines:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### WR-04: `_jd_analysis` Block Sends Python `list.__repr__` to the LLM Instead of Structured Text

**File:** `src/llm_client.py:132-137`

**Issue:** The `<jd_analysis>` block formats the parsed analysis lists using Python's default `list.__repr__`:

```python
analysis_block = (
    "<jd_analysis>\n"
    f"technologies: {techs}\n"
    f"requirements: {reqs}\n"
    f"emphasis_areas: {areas}\n"
    "</jd_analysis>\n\n"
)
```

This sends the LLM text like `technologies: ['Python', 'FastAPI', 'C++']` — Python syntax with square brackets, single quotes, and comma-space separators that are meaningless in this context. The LLM is expected to treat these as relevance-ranking signals, not to parse Python syntax, but the format introduces noise that could cause subtle misreadings of technology names that contain special characters (e.g., `'C++'` surrounded by quotes and brackets).

**Fix:** Format as a bulleted list or clean comma-separated values:

```python
def _format_list(items: list) -> str:
    return ", ".join(str(i) for i in items) if items else "(none)"

analysis_block = (
    "<jd_analysis>\n"
    f"technologies: {_format_list(techs)}\n"
    f"requirements: {_format_list(reqs)}\n"
    f"emphasis_areas: {_format_list(areas)}\n"
    "</jd_analysis>\n\n"
)
```

## Info

### IN-01: `_strip_fences` Called Twice for Each LLM Response

**File:** `src/llm_client.py:210-211`

**Issue:**

```python
fences_stripped = raw.strip() != _strip_fences(raw)
content = _strip_fences(raw)
```

`_strip_fences` runs the same two `re.sub` calls twice on the same immutable input. The second call always produces an identical result to the first.

**Fix:**

```python
content = _strip_fences(raw)
fences_stripped = raw.strip() != content
```

### IN-02: `TestCheckHallucinatedEmployers` Tests Pass Against Fictional Fixtures — Will Not Survive CR-01 Fix

**File:** `src/guards_test.py:84-99`

**Issue:** The three tests in `TestCheckHallucinatedEmployers` use `\employer{Acme Corp}{2022}{Engineer}` as fixtures. These tests pass today not because they validate meaningful behavior but because the fictional `_EMPLOYER_PATTERN` matches the fictional fixture data. When CR-01 is fixed, these tests must be rewritten with real template fixtures before the test suite will pass. Leaving them as-is while fixing CR-01 will cause immediate test failures, which may mislead a reviewer into thinking the CR-01 fix itself is wrong.

**Fix:** Rewrite fixtures in `TestCheckHallucinatedEmployers` alongside the CR-01 fix:

```python
def test_employer_in_original_missing_from_tailored_triggers_warning(self):
    original = r"\textbf{Acme Corp}\textbf{ | Engineer}"
    tailored = r"\documentclass{article}\n\end{document}"
    with patch("guards.logger") as mock_logger:
        run_guards(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        self.assertTrue(any("Acme Corp" in c for c in calls))
```

---

_Reviewed: 2026-06-13T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
