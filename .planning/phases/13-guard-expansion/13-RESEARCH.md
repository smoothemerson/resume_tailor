# Phase 13: Guard Expansion - Research

**Researched:** 2026-06-09
**Domain:** Python guard functions, LaTeX resume parsing, pytest unit testing
**Confidence:** HIGH

## Summary

Phase 13 adds two new guard functions to `src/guards.py` — `_check_technology_substitution` and `_check_protected_sections` — wires both into `run_guards()`, and ships `tests/unit/test_guards.py` covering all new behavior. The existing codebase is well-understood: guard conventions, test patterns, and the `\header{...}` boundary extraction approach are all established and directly reusable.

**Critical finding from `resumes/english.tex`:** The actual resume does NOT use the `\employer{...}` macro in the Experience section body. The experience entry is written as raw LaTeX (`\textbf{SERPRO}\textbf{ | ...} \hfill ...`). The `\employer{...}` macro is defined in the preamble but unused in content. Similarly, projects use an `\href{url}{\textbf{Name}}\text{ | description} \hfill date` pattern, not a custom project macro. This directly affects the implementation of `_check_protected_sections` (GARD-06): the employer-header comparison via `_EMPLOYER_PATTERN` will match zero items in the real resume, so the guard will be silent on employer headers unless the LLM switches to using `\employer{...}`.

**Primary recommendation:** Implement both guards exactly per CONTEXT.md decisions. For `_check_protected_sections`, extract Education and Languages sections using the `\header{}` boundary pattern, and implement employer-header comparison via `_EMPLOYER_PATTERN` as designed — the guard is correct for any resume that uses `\employer{...}`, even though the current production resume doesn't. For project anchors (D-08), parse `\href{...}{...}` tuples from the Projects section, not a custom macro.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use `\header{Skills}` as the section boundary — extract content between `\header{Skills}` and the next `\header{...}` command.
- **D-02:** Tokenize on comma-separated items (split on `,\s*`). Handles multi-word names like "Apache Kafka".
- **D-03:** Strip LaTeX formatting macros (`\textbf{}`, `\emph{}`, etc.) before tokenizing. Ensures `\textbf{Python}` and `Python` are the same token.
- **D-04:** If no `\header{Skills}` in either original or tailored, return silently.
- **D-05:** Contact block extraction strategy: let researcher inspect `resumes/english.tex` (DONE — see Architectural Responsibility Map).
- **D-06:** Education and Languages sections: compare full section content between `\header{Education}` and next `\header{...}`, same for `\header{Languages}`. Warn once per changed section.
- **D-07:** Employer header lines: reuse `_EMPLOYER_PATTERN` regex. Warn if any employer header line differs.
- **D-08:** Project anchor pattern: let researcher find the actual macro in `resumes/english.tex` (DONE — see Architecture Patterns).
- **D-09:** `_check_technology_substitution` issues three distinct `logger.warning()` calls for substitution, removal-only, and addition-only cases.
- **D-10:** `_check_protected_sections` issues one `logger.warning()` per changed element.
- **D-11:** New guard tests go in `tests/unit/test_guards.py` — a new file.
- **D-12:** Use pytest-style function tests (`def test_*`). Each test decorated with `@pytest.mark.unit`.
- **D-13:** Both new guards must follow the never-raise pattern: `try/except Exception as exc` → `logger.warning(f"... check failed: {exc}")`.

### Claude's Discretion

None specified.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GARD-05 | `_check_technology_substitution(original, tailored)` extracts Skills section from each text and warns when technologies are substituted, only removed, or only added | Section extraction pattern from `_check_missing_sections`; tokenization using comma-split after LaTeX macro stripping |
| GARD-06 | `_check_protected_sections(original, tailored)` warns when contact block, education section, languages section, employer header lines, or project anchors differ | LaTeX structure of `english.tex` fully mapped; contact block is raw `\begin{center}` block; project anchors are `\href{url}{\textbf{Name}}` tuples |
| GARD-07 | Both new guards are called from `run_guards()` and never raise — all exceptions caught and logged as warnings | Pattern established by all three existing guards; two new lines added to `run_guards()` |
| TEST-12 | Unit tests cover `_check_technology_substitution`: substitution, removal-only, addition-only, identical, no-skills-section, malformed input | pytest `@pytest.mark.unit`, `patch("guards.logger")` pattern from `src/guards_test.py` |
| TEST-13 | Unit tests cover `_check_protected_sections`: contact block diff, education diff, languages diff, employer header changed, unchanged, empty strings passed | Same test infrastructure; inline LaTeX strings as test fixtures |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LaTeX section extraction | Guard layer (src/guards.py) | — | Text parsing belongs in guard functions, not CLI or LLM client |
| Technology tokenization | Guard layer (src/guards.py) | — | Inline helper logic within `_check_technology_substitution` |
| Protected element comparison | Guard layer (src/guards.py) | — | All comparison logic is self-contained in the guard |
| Warning emission | logger (log_manager.py) | — | `logger.warning()` is the single output channel for guards |
| Test execution | pytest (tests/unit/) | — | New test file added alongside existing unit tests |

## Standard Stack

No new packages are installed in this phase. All implementation uses:

| Component | Version | Purpose | Source |
|-----------|---------|---------|--------|
| `re` (stdlib) | stdlib | Regex for LaTeX section boundary and token extraction | Already used in `guards.py` |
| `pytest` | >=9.0.3 (already in dev deps) | Test runner and `@pytest.mark.unit` decorator | Already in `pyproject.toml` `[dependency-groups].dev` |
| `unittest.mock.patch` | stdlib | Patch `guards.logger` in tests | Pattern from `src/guards_test.py` |

**Installation:** No new packages needed. [VERIFIED: pyproject.toml read directly]

## Package Legitimacy Audit

No external packages are introduced in this phase. This section is not applicable.

**Packages removed due to slopcheck:** none
**Packages flagged as suspicious:** none

## Architecture Patterns

### System Architecture Diagram

```
original_text ──────────────────────────────────────────────────────────┐
                                                                         ▼
tailored_text ──────────────────────────────────────────────────────► run_guards()
                                                                         │
                        ┌────────────────────────────────────────────────┤
                        │                    │                           │
                        ▼                    ▼                           ▼
          _check_missing_sections  _check_technology_substitution  _check_protected_sections
          (existing)               (NEW: GARD-05)                  (NEW: GARD-06)
                        │                    │                           │
                        │         ┌──────────┤                  ┌────────┤
                        │         │          │                  │        │
                        │    extract       extract           compare    compare
                        │    Skills        Skills          Education   contact
                        │    section       section         Languages   block
                        │    (original)    (tailored)      employer    \href
                        │         │          │             headers     anchors
                        │         └────┬─────┘                  └────────┤
                        │              │                                  │
                        │         set diff                         string diff
                        │         (removed, added)                per element
                        │              │                                  │
                        └──────────────┴──────────────────────────────► logger.warning()
                                                               (one call per issue found)
```

### Recommended Project Structure

No structural change. New file added:
```
tests/
└── unit/
    ├── test_jd_analyzer.py       # existing
    ├── test_llm_client.py        # existing
    ├── test_resume_reader.py     # existing
    ├── test_resume_writer.py     # existing
    └── test_guards.py            # NEW — Phase 13
src/
└── guards.py                     # modified — add 2 functions, update run_guards()
```

### Pattern 1: Section Content Extraction

**What:** Extract the body of a LaTeX section using `\header{Name}` as delimiter.
**When to use:** Needed for both `_check_technology_substitution` (Skills) and `_check_protected_sections` (Education, Languages).

```python
# Source: derived from _check_missing_sections in src/guards.py [VERIFIED: read directly]
def _extract_section(text: str, section_name: str) -> str | None:
    pattern = rf'\\header\{{{re.escape(section_name)}\}}(.*?)(?=\\header\{{|$)'
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1) if m else None
```

This matches `\header{Skills}` then captures everything until the next `\header{...}` or end of string. The `re.DOTALL` flag is required so `.` matches newlines.

### Pattern 2: LaTeX Macro Stripping + Tokenization

**What:** Remove `\textbf{...}`, `\emph{...}`, etc. then split on commas.
**When to use:** Inside `_check_technology_substitution` after extracting the Skills section body.

```python
# Source: CONTEXT.md D-02, D-03 [VERIFIED: read directly]
def _extract_technologies(section_text: str) -> set[str]:
    cleaned = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', section_text)
    return {t.strip() for t in cleaned.split(',') if t.strip()}
```

**Skills section structure from `resumes/english.tex`:**
```latex
\textbf{AI:} LangChain, ChromaDB, Scikit-learn, RAG, MCP\\
\textbf{LLM Providers:} OpenAI, Claude, Mistral, Ollama\\
```

After stripping `\textbf{AI:}` becomes `AI:`, and items after `:` need trimming. The tokenizer produces tokens like `AI:`, `LangChain`, `ChromaDB`, etc. The `:` attached to category labels (`AI:`, `Backend:`) will be kept as distinct tokens — that is correct behavior since both original and tailored will have them, so they cancel out in the diff. [VERIFIED: english.tex read directly]

### Pattern 3: Three-Way Warning Logic

**What:** Emit different warnings for substitution vs. removal-only vs. addition-only.
```python
# Source: CONTEXT.md §Specific Ideas [VERIFIED: read directly]
removed = original_techs - tailored_techs
added = tailored_techs - original_techs
if removed and added:
    logger.warning(f"Technology substitution in Skills: removed {sorted(removed)}, added {sorted(added)}")
elif removed:
    logger.warning(f"Technologies removed from Skills: {sorted(removed)}")
elif added:
    logger.warning(f"Technologies added to Skills not in original: {sorted(added)}")
```

### Pattern 4: Contact Block Extraction

**What:** The contact block in `resumes/english.tex` is a raw `\begin{center}...\end{center}` block at the top of the document body (NOT using the `\contact{...}` macro, which is defined but unused). [VERIFIED: english.tex read directly]

```latex
% Actual structure in english.tex (lines 75-85):
\begin{center}
    {\Huge \scshape {Emerson Rocha Faria}}\\
    \vspace*{2pt}
    \ {AI Engineer}\\
    ...email, phone, city...
    \textbf{\href{...}{LinkedIn}}\ $\cdot$\
    \textbf{\href{...}{GitHub}}\\
\end{center}
```

**Extraction regex:**
```python
# Source: derived from english.tex structure [VERIFIED: read directly]
pattern = r'\\begin\{center\}(.*?)\\end\{center\}'
m = re.search(pattern, text, re.DOTALL)
contact = m.group(1).strip() if m else None
```

If content differs between original and tailored: `logger.warning("Contact block was modified in tailored output.")`

### Pattern 5: Project Anchor Extraction

**What:** Projects use `\href{url}{\textbf{Name}}` as their anchor — there is NO custom project macro. [VERIFIED: english.tex read directly]

```latex
% Actual structure (line 115-119):
\href{https://github.com/smoothemerson/ragscope}{\textbf{RAGScope}}\text{ | description} \hfill Mar 2026\\
```

**Extraction regex for project anchors (URL + name tuples):**
```python
# Source: derived from english.tex structure [VERIFIED: read directly]
pattern = r'\\href\{([^}]+)\}\{\\textbf\{([^}]+)\}\}'
original_projects = set(re.findall(pattern, original))
tailored_projects = set(re.findall(pattern, tailored))
for url, name in original_projects - tailored_projects:
    logger.warning(f'Project anchor changed or removed: "{name}" ({url})')
```

This extracts `(url, name)` tuples. If a project's URL or name changes, the tuple changes and triggers a warning.

### Pattern 6: Employer Header Pattern (existing — reused)

```python
# Source: src/guards.py line 6 [VERIFIED: read directly]
_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
original_headers = set(_EMPLOYER_PATTERN.findall(original))
tailored_headers = set(_EMPLOYER_PATTERN.findall(tailored))
for header in original_headers - tailored_headers:
    logger.warning(f'Employer header changed or removed: "{header[0]}"')
```

**Note:** `english.tex` does not use `\employer{...}` in its content (the macro is defined but the experience section uses raw bold text + hfill). The guard is still correct to implement — it will fire if an LLM introduces or modifies `\employer{...}` calls. It is simply silent on the current production resume, which is safe behavior. [VERIFIED: english.tex read directly]

### Pattern 7: Never-Raise Wrapper

Both new guards MUST follow this pattern exactly: [VERIFIED: guards.py read directly]

```python
def _check_technology_substitution(original: str, tailored: str) -> None:
    try:
        # ... all logic here ...
    except Exception as exc:
        logger.warning(f"Technology substitution check failed: {exc}")


def _check_protected_sections(original: str, tailored: str) -> None:
    try:
        # ... all logic here ...
    except Exception as exc:
        logger.warning(f"Protected sections check failed: {exc}")
```

### Pattern 8: Test File Style

From `tests/unit/test_resume_writer.py` and `tests/unit/test_jd_analyzer.py`: [VERIFIED: read directly]

```python
import pytest
from unittest.mock import patch

from guards import _check_technology_substitution, _check_protected_sections


@pytest.mark.unit
def test_technology_substitution_warns_on_substitution():
    original = r"\header{Skills}" + "\nPython, Java\n\\header{Education}"
    tailored = r"\header{Skills}" + "\nPython, Go\n\\header{Education}"
    with patch("guards.logger") as mock_logger:
        _check_technology_substitution(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Java" in c for c in calls)
        assert any("Go" in c for c in calls)
```

- Import functions directly (not through `run_guards`)
- Use `patch("guards.logger")` as the mock target — this is the module-level logger in `guards.py` [VERIFIED: guards_test.py pattern]
- Use `@pytest.mark.unit` on every test function
- No `__init__.py` in `tests/unit/` [VERIFIED: directory listing]
- `pythonpath = ["src"]` in `pyproject.toml` means `from guards import ...` resolves correctly [VERIFIED: pyproject.toml]

### Anti-Patterns to Avoid

- **Importing `run_guards` to test new guards individually:** The test suite should import and call `_check_technology_substitution` and `_check_protected_sections` directly. Calling through `run_guards()` makes it impossible to isolate which guard's warning is being asserted without overly complex call-count matching.
- **Using `assert_called_once_with` when multiple warnings are expected:** Use `call_args_list` with `any(...)` checks, as shown in existing `guards_test.py`.
- **Using `re.DOTALL` without it:** Section extraction across newlines fails silently without this flag.
- **Forgetting to handle `None` from `_extract_section`:** If either section is `None`, skip the comparison per D-04 (for Skills) and D-10 (for protected sections).
- **Splitting on `,` without stripping:** Items like `" Python"` and `"Python"` differ. Always strip after split.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LaTeX macro stripping | Custom tokenizer | `re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)` | One-liner handles all `\cmd{arg}` forms |
| Section boundary detection | State machine | `re.search(..., re.DOTALL)` with lookahead | Pattern already established in `_check_missing_sections` |
| Set difference for tokens | Loop comparison | `set_a - set_b` | Python built-in; correct and O(n) |

**Key insight:** All guard problems are solvable with the regex patterns already in `guards.py`. No new algorithms needed.

## Common Pitfalls

### Pitfall 1: `re.DOTALL` Omission
**What goes wrong:** Section content spanning multiple lines is not captured; `_extract_section` returns only the first line.
**Why it happens:** The default `.` in Python regex does not match `\n`. LaTeX sections span multiple lines.
**How to avoid:** Always pass `re.DOTALL` to `re.search()` when extracting section content.
**Warning signs:** Tests with multi-line Skills content fail to find any technologies.

### Pitfall 2: Macro Stripping Misses Nested Braces
**What goes wrong:** `\textbf{AI:}` is stripped correctly but `\textbf{\href{...}{Python}}` is not.
**Why it happens:** The regex `\\[a-zA-Z]+\{([^}]*)\}` uses `[^}]*` which stops at the first `}`, so nested braces are not handled.
**How to avoid:** The current Skills section in `english.tex` does not have nested macros in tech names. The simple regex is sufficient. If nested macros appear, strip iteratively (run `re.sub` until stable). For Phase 13 scope, simple stripping is adequate.
**Warning signs:** A technology like `\href{...}{\textbf{Python}}` leaks through as `\href{...` in the token set.

### Pitfall 3: Empty String Input Causes AttributeError
**What goes wrong:** `_extract_section(None, "Skills")` raises `AttributeError: 'NoneType' has no attribute 'search'` or similar.
**Why it happens:** `run_guards(None, None)` is tested in the existing suite (malformed input test). The new guards receive `original` and `tailored` as passed by `run_guards()`.
**How to avoid:** The `try/except Exception as exc` never-raise wrapper catches this. The guard logs a warning and returns. No extra None-guard needed, but test coverage for `None` input is required (TEST-12 spec: "malformed input"; TEST-13 spec: "empty strings passed").
**Warning signs:** `test_run_guards_malformed_input_no_exception` fails after adding new guards.

### Pitfall 4: Test Imports Fail Due to `pythonpath` Misunderstanding
**What goes wrong:** `from guards import _check_technology_substitution` raises `ModuleNotFoundError`.
**Why it happens:** The file is `src/guards.py` but the test is in `tests/unit/`. pytest needs `src/` on the path.
**How to avoid:** `pyproject.toml` already has `pythonpath = ["src"]` and `--import-mode=importlib`. No `sys.path.insert()` needed in new test files. [VERIFIED: pyproject.toml read directly]
**Warning signs:** `ModuleNotFoundError: No module named 'guards'` during test collection.

### Pitfall 5: Using `\employer{}` Pattern on Current Resume Yields False Negatives
**What goes wrong:** Planner expects `_check_protected_sections` to warn on employer changes for the current `english.tex`, but the current resume uses raw bold text not the `\employer{...}` macro.
**Why it happens:** The `\employer{...}` custom command is defined in the preamble but not used in the document body. [VERIFIED: english.tex lines 39-41 vs lines 100-110]
**How to avoid:** Understand that the guard is forward-compatible (catches if LLM starts using `\employer{...}`). Document this in test comments. Tests should use synthetic LaTeX that DOES use `\employer{...}` to verify the pattern works.
**Warning signs:** Test using `english.tex` content for employer check never fires a warning.

### Pitfall 6: Contact Block — `\begin{center}` Appears Once Per Section in General
**What goes wrong:** If the resume has multiple `\begin{center}...\end{center}` blocks, extracting only the first may miss the actual contact block, or non-contact center blocks may be compared.
**Why it happens:** Greedy/non-greedy regex choice matters.
**How to avoid:** Use `re.DOTALL` with non-greedy `.*?`. The contact block is the FIRST center block after `\begin{document}`. In `english.tex`, there is only one `\begin{center}` block at document top. [VERIFIED: english.tex]
**Warning signs:** Contact block extraction captures content from a different section.

## Code Examples

Verified patterns from direct source inspection:

### Reusable: `_EMPLOYER_PATTERN` (already in guards.py)
```python
# Source: src/guards.py line 6 [VERIFIED: read directly]
_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
```

### Reusable: `\header{}` section discovery
```python
# Source: _check_missing_sections in src/guards.py [VERIFIED: read directly]
original_sections = re.findall(r'\\header\{([^}]+)\}', original)
```

### New: `\href` project anchor extraction
```python
# Source: derived from english.tex lines 115, 121 [VERIFIED: read directly]
pattern = r'\\href\{([^}]+)\}\{\\textbf\{([^}]+)\}\}'
projects = set(re.findall(pattern, text))
# yields {('https://github.com/smoothemerson/ragscope', 'RAGScope'), ...}
```

### New: contact block extraction
```python
# Source: derived from english.tex lines 75-85 [VERIFIED: read directly]
m = re.search(r'\\begin\{center\}(.*?)\\end\{center\}', text, re.DOTALL)
contact = m.group(1).strip() if m else None
```

## State of the Art

No third-party library upgrades needed for this phase. All patterns are stdlib regex.

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Test in `src/*_test.py` | Unit tests in `tests/unit/test_*.py` | Phase 9 | New guard tests go in `tests/unit/`, not `src/` |

**Deprecated/outdated:**
- `src/guards_test.py`: The existing test file uses `unittest.TestCase` style. New `tests/unit/test_guards.py` uses pytest function style — both coexist. Do not add new tests to `src/guards_test.py`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The `\begin{center}` block is the contact block pattern that `_check_protected_sections` should compare | Architecture Patterns §Pattern 4 | If the contact block structure differs in other resumes (e.g., uses `\contact{...}` macro), guard may miss comparisons — LOW risk since the guard is defensive and only warns | 
| A2 | `\href{url}{\textbf{Name}}` tuples are the correct project anchor pattern for GARD-06 | Architecture Patterns §Pattern 5 | If D-08 intended a different scope (e.g., entire project entry content), the warning threshold would differ — LOW risk, discuss with user if needed |

**All other claims in this research were verified by direct file reads.** The two assumptions above reflect design interpretation questions raised by D-05 and D-08 in CONTEXT.md directing the researcher to inspect `english.tex`.

## Open Questions (RESOLVED)

1. **Contact block scope for D-05**
   - What we know: The contact block in `english.tex` is a raw `\begin{center}...\end{center}` block at document top (lines 75-85). There is no use of the `\contact{...}` macro despite it being defined.
   - What's unclear: Should the guard extract only the first `\begin{center}` block, or compare the entire pre-`\header{}` document header?
   - RESOLVED: Use first `\begin{center}...\end{center}` match via `re.search(r'\\begin\{center\}(.*?)\\end\{center\}', text, re.DOTALL)`. Implemented in Plan 02 Task 2.

2. **Project anchor granularity for D-08**
   - What we know: Projects use `\href{url}{\textbf{Name}}\text{ | subtitle} \hfill date`. The `\href{url}{\textbf{Name}}` part is the stable anchor.
   - What's unclear: Should the guard compare the full project line (including date and subtitle) or only the URL+name tuple?
   - RESOLVED: Compare URL+name tuples only via `re.findall(r'\\href\{([^}]+)\}\{\\textbf\{([^}]+)\}\}', text)`. Dates and subtitles can legitimately be tailored; the anchor (project identity) should not change. Implemented in Plan 02 Task 2.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All source | ✓ (workspace has python3) | 3.x | — |
| pytest >=9.0.3 | Test execution | [ASSUMED] in venv | >=9.0.3 | Install via `uv add --dev pytest` |
| `re` module | Guard logic | ✓ (stdlib) | stdlib | — |
| `unittest.mock` | Test mocking | ✓ (stdlib) | stdlib | — |

**Note:** `uv` was not found in the sandbox environment (`uv not available`). Tests must be run in the project's virtual environment. The `pyproject.toml` dev dependencies include pytest.

**Missing dependencies with no fallback:** None that block implementation.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest -m unit tests/unit/test_guards.py` |
| Full suite command | `pytest -m unit` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GARD-05 | Technology substitution warn | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_substitution` | ❌ Wave 0 |
| GARD-05 | Removal-only warn | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_removal_only` | ❌ Wave 0 |
| GARD-05 | Addition-only warn | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_warns_on_addition_only` | ❌ Wave 0 |
| GARD-05 | Identical skills silent | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_silent_for_identical` | ❌ Wave 0 |
| GARD-05 | No skills section silent | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_silent_for_no_skills_section` | ❌ Wave 0 |
| TEST-12 | Malformed input no raise | unit | `pytest -m unit tests/unit/test_guards.py::test_technology_substitution_malformed_input_no_raise` | ❌ Wave 0 |
| GARD-06 | Contact block diff warns | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_contact_diff` | ❌ Wave 0 |
| GARD-06 | Education diff warns | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_education_diff` | ❌ Wave 0 |
| GARD-06 | Languages diff warns | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_languages_diff` | ❌ Wave 0 |
| GARD-06 | Employer header changed warns | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_warns_on_employer_header_change` | ❌ Wave 0 |
| GARD-06 | All sections unchanged silent | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_silent_when_unchanged` | ❌ Wave 0 |
| TEST-13 | Empty strings no raise | unit | `pytest -m unit tests/unit/test_guards.py::test_protected_sections_empty_strings_no_raise` | ❌ Wave 0 |
| GARD-07 | run_guards calls both new guards | unit | `pytest -m unit tests/unit/test_guards.py::test_run_guards_calls_technology_substitution` | ❌ Wave 0 |
| GARD-07 | New guards never raise | unit | `pytest -m unit tests/unit/test_guards.py::test_run_guards_new_guards_never_raise` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest -m unit tests/unit/test_guards.py -x`
- **Per wave merge:** `pytest -m unit`
- **Phase gate:** Full unit suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_guards.py` — covers TEST-12 and TEST-13 (all rows above)

*(Existing test infrastructure in `pyproject.toml` is fully adequate — no framework changes needed.)*

## Security Domain

This phase adds pure Python text-comparison guards. No authentication, no I/O to external services, no user-supplied data reaching any sink. ASVS categories V2, V3, V4, V6 are not applicable.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | minimal | Guards receive LLM output strings; the never-raise wrapper ensures malformed input cannot propagate |
| V6 Cryptography | no | — |

**Threat pattern:** Guards process strings that came from an LLM. The only risk is an unexpected input type (e.g., `None`) causing an unhandled exception and preventing the warning from being issued. The never-raise pattern (D-13) fully mitigates this.

## Sources

### Primary (HIGH confidence)
- `src/guards.py` — read directly; all regex patterns, `_EMPLOYER_PATTERN`, `run_guards()` signature, never-raise pattern
- `src/guards_test.py` — read directly; `patch("guards.logger")` convention, assertion patterns
- `resumes/english.tex` — read directly; contact block structure (`\begin{center}`), project anchor pattern (`\href{url}{\textbf{Name}}`), Skills section format
- `pyproject.toml` — read directly; test paths, pythonpath, markers, addopts, dev dependencies
- `tests/unit/test_resume_writer.py` and `test_jd_analyzer.py` — read directly; pytest function style, `@pytest.mark.unit`, `tmp_path` fixture usage
- `.planning/phases/13-guard-expansion/13-CONTEXT.md` — read directly; all locked decisions

### Secondary (MEDIUM confidence)
- `.planning/milestones/v1.1-phases/09-unit-test-gaps/09-CONTEXT.md` — read directly; D-01 to D-11 confirmed test file conventions

### Tertiary (LOW confidence — not applicable)
None — all findings verified by direct file reads.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all existing deps confirmed in pyproject.toml
- Architecture: HIGH — LaTeX structure confirmed in english.tex; all patterns verified against live source files
- Guard implementation patterns: HIGH — established by existing guards.py code
- Test patterns: HIGH — verified against existing tests/unit/ files
- Pitfalls: HIGH — derived from direct inspection of the actual file content

**Research date:** 2026-06-09
**Valid until:** 2026-07-09 (stable domain — stdlib Python + project-specific LaTeX structure)
