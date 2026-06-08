# Phase 4: Output Reliability Guards - Research

**Researched:** 2026-06-02
**Domain:** Python string analysis, regex-based LaTeX content guards, stderr warning pipeline
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Guard logic lives in a new `src/guards.py` module, not inside `llm_client.py`.
- **D-02:** `guards.py` exports a `run_guards(original_text, tailored_text)` function that `cli.py` calls.
- **D-03:** `run_guards()` is called in `cli.py` **before** `write_resume()`. Guards fire on the content first; then the file is written regardless of how many warnings fired.
- **D-04:** `_validate_latex()` in `llm_client.py` stays as-is — hard errors for missing `\documentclass` or `\end{document}` remain fatal (blocking). These are not converted to warnings.
- **D-05:** GUARD-02 is a separate, non-blocking soft check with two sub-checks: (1) stripped fences warning — warn if `_strip_fences()` actually modified the text; (2) inline markdown in body — warn if the tailored content contains markdown markers embedded inside the document body.
- **D-06:** To enable the stripped-fences check, `_strip_fences()` must be callable from outside `llm_client.py`, or the planner must expose a way to compare before/after. Planner should implement this cleanly (e.g., pass raw content through guard before stripping, or have `generate_tailored_resume()` return fences-were-stripped metadata).
- **D-07:** Extract employer names and date strings from `\employer{name}{dates}{title}` LaTeX commands in the original resume using regex. Verify each appears in the tailored output.
- **D-08:** Scope is `\employer{}` entries only. Education section (`\schoolwithcourses{}`, `\school{}`) is excluded.
- **D-09:** Warnings use `WARNING:` prefix. No guard IDs, no color, no emoji. Examples: `WARNING: Section "Skills" missing from tailored output.` / `WARNING: LLM returned markdown fences that were stripped from output.` / `WARNING: Employer "Acme Corp" from original resume not found in tailored output.`
- **D-10:** Warnings print inline as each guard fires (no buffering/collect-then-print). Each guard function prints to `sys.stderr` directly when it detects an issue.
- **D-11:** Sections are detected via `\header{...}` custom commands (not standard `\section{}`). Extract all `\header{...}` values from original, verify each appears in tailored.

### Claude's Discretion
None specified.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GUARD-01 | Tool warns when a section present in the original resume is missing from the tailored output | `re.findall(r'\\header\{([^}]+)\}', text)` extracts sections; set-difference finds missing ones. Verified against `english.tex` — 5 sections detected. |
| GUARD-02 | Tool warns when tailored output contains markdown prose or other format violations (LaTeX-only rule broken) | Two sub-checks: (1) fences-were-stripped flag (requires architecture change — see Critical Finding below); (2) inline markdown patterns in body after stripping. |
| GUARD-03 | Tool warns when structured fields (employer names, dates) appear in output but were not in original resume | `re.findall(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}', text)` — but current `english.tex` has 0 `\employer{}` usages (see Critical Finding). Guard is correctly implemented per spec but produces no warnings on current resume. |
| GUARD-04 | Guards degrade gracefully — any guard failure prints a warning to stderr but does not block the output write | Enforced by calling `run_guards()` before `write_resume()` in `cli.py`, with `run_guards()` never raising exceptions — only printing to stderr. |
</phase_requirements>

---

## Summary

Phase 4 adds a `src/guards.py` module with three non-fatal checks that compare the original LaTeX resume against the LLM-tailored output. All guards use Python stdlib `re` to extract structural markers from the LaTeX, compare them between original and tailored, and print `WARNING:` messages to `sys.stderr` via the existing `log_manager.logger.warning()` function already in the codebase.

The implementation is pure Python, no new dependencies. The biggest architectural decision is how `cli.py` threads pre-strip raw content through to the guards so GUARD-02's fences-were-stripped sub-check can fire. The simplest clean option is to refactor `generate_tailored_resume()` to return a `NamedTuple` with `.content` and `.fences_stripped` fields rather than a plain `str`, which requires updating `cli.py` and the mock return values in `cli_test.py`.

One critical finding: the current `resumes/english.tex` defines the `\employer{name}{dates}{title}` command in the preamble but never invokes it in the document body — the single employer (SERPRO) is formatted with inline `\textbf{}` commands. GUARD-03 as specified (D-07/D-08) will produce zero warnings for any tailored output based on this resume. The guard implementation is still correct per spec and is forward-compatible when the resume is updated to use the macro, but the planner should note that GUARD-03 is effectively dormant under the current resume.

**Primary recommendation:** Implement `guards.py` as three private `_check_*` functions called by `run_guards(original_text, tailored_text, fences_stripped=False)`. Refactor `generate_tailored_resume()` to return a `NamedTuple` with `content` and `fences_stripped` fields. Use `logger.warning()` from the existing `log_manager.py` module for all warning output.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Section presence check (GUARD-01) | `guards.py` module | — | Pure string analysis on two text inputs; no I/O, no HTTP |
| Format violation check (GUARD-02) | `guards.py` module | `llm_client.py` (provides fences_stripped metadata) | Guard logic in guards.py; metadata must be threaded from where stripping occurs |
| Employer hallucination check (GUARD-03) | `guards.py` module | — | Pure regex over LaTeX content |
| Warning output | `log_manager.logger` | — | Existing `log_manager.py` produces the exact `WARNING: {msg}` format to stderr |
| Guard invocation | `cli.py` `main()` | — | Orchestration layer; calls guards before write, never inside guards.py |

---

## Standard Stack

### Core

No new dependencies. This phase is entirely stdlib + existing project modules.

| Module | Source | Purpose |
|--------|--------|---------|
| `re` | stdlib | Regex extraction of `\header{}` and `\employer{}` patterns |
| `sys.stderr` | stdlib | Warning output channel (via log_manager) |
| `log_manager.logger` | existing `src/log_manager.py` | Produces `WARNING: {message}` format exactly matching D-09 |

### Package Legitimacy Audit

Not applicable — no new packages installed in this phase.

---

## Architecture Patterns

### System Architecture Diagram

```
cli.py main()
  |
  +-- read_resume() -> original_text
  |
  +-- generate_tailored_resume(original_text, job_desc)
  |     |
  |     +-- _check_ollama_health()
  |     +-- _build_messages()
  |     +-- POST /api/chat
  |     +-- _strip_fences(raw)  <-- records if fences were present
  |     +-- _validate_latex()   <-- FATAL if \documentclass or \end{document} missing
  |     returns TailorResult(content=str, fences_stripped=bool)
  |
  +-- run_guards(original_text, result.content, result.fences_stripped)
  |     |
  |     +-- _check_missing_sections()   -> WARNING to stderr (GUARD-01)
  |     +-- _check_format_violations()  -> WARNING to stderr (GUARD-02)
  |     +-- _check_hallucinated_employers() -> WARNING to stderr (GUARD-03)
  |     returns None  [GUARD-04: never raises]
  |
  +-- write_resume(result.content, output_dir)  <-- always runs
```

### Recommended Project Structure

```
src/
├── guards.py          # new: run_guards() + three _check_* functions
├── guards_test.py     # new: unit tests for all guards
├── cli.py             # modified: import run_guards, update generate_tailored_resume call
├── llm_client.py      # modified: generate_tailored_resume returns TailorResult NamedTuple
├── log_manager.py     # unchanged: already provides logger.warning()
├── config.py          # unchanged
├── resume_reader.py   # unchanged
└── resume_writer.py   # unchanged
```

### Pattern 1: Non-fatal Guard Functions

**What:** Each guard is a private function that takes string inputs, performs regex analysis, and calls `logger.warning()` for each violation found. No return value. No exceptions raised.

**When to use:** Any check that must never block the pipeline regardless of outcome.

```python
# Source: established from codebase raise-not-exit pattern + D-04/D-10

def _check_missing_sections(original: str, tailored: str) -> None:
    original_sections = re.findall(r'\\header\{([^}]+)\}', original)
    tailored_sections = re.findall(r'\\header\{([^}]+)\}', tailored)
    for section in original_sections:
        if section not in tailored_sections:
            logger.warning(f'Section "{section}" missing from tailored output.')
```

### Pattern 2: TailorResult NamedTuple Return

**What:** Refactor `generate_tailored_resume()` to return a `NamedTuple` instead of a plain `str`, carrying both the cleaned content and a `fences_stripped` boolean.

**When to use:** When a function needs to return a primary value plus lightweight metadata without changing call sites substantially.

```python
# Source: Python stdlib typing.NamedTuple pattern

from typing import NamedTuple

class TailorResult(NamedTuple):
    content: str
    fences_stripped: bool
```

In `generate_tailored_resume()`:
```python
raw = data["message"]["content"]
fences_stripped = raw.strip() != _strip_fences(raw)  # detect before stripping
content = _strip_fences(raw)
_validate_latex(content)
return TailorResult(content=content, fences_stripped=fences_stripped)
```

In `cli.py`:
```python
result = generate_tailored_resume(resume_text, job_description, model=args.model)
run_guards(resume_text, result.content, result.fences_stripped)
output_path = write_resume(result.content, output_dir)
```

**Impact on existing tests:** `cli_test.py` mocks `generate_tailored_resume` to return `"\\documentclass{article}\n\\end{document}"`. These mocks must be updated to return `TailorResult(content="...", fences_stripped=False)` — or the mock return value wrapped in a `TailorResult`.

### Pattern 3: GUARD-02 Inline Markdown Detection

**What:** After the outer fences are stripped, check if markdown syntax leaked into the document body.

**Patterns to check:**
- Triple backticks anywhere in body: `"```" in tailored`
- Markdown headings (lines starting with `#`): `re.search(r'(?m)^#{1,6} ', tailored)`
- Markdown bold not preceded by backslash: `re.search(r'\*\*\S[^*]*\S\*\*', tailored)`

```python
# [VERIFIED: codebase testing] against english.tex - no false positives on clean LaTeX
def _check_format_violations(tailored: str, fences_stripped: bool) -> None:
    if fences_stripped:
        logger.warning("LLM returned markdown fences that were stripped from output.")
    if "```" in tailored:
        logger.warning("Tailored output contains inline code fences.")
    if re.search(r'(?m)^#{1,6} ', tailored):
        logger.warning("Tailored output contains markdown heading markers.")
    if re.search(r'\*\*\S[^*]*\S\*\*', tailored):
        logger.warning("Tailored output contains markdown bold markers.")
```

### Pattern 4: GUARD-03 Employer Extraction

**What:** Extract all `\employer{name}{dates}{title}` occurrences from original and verify each appears in tailored.

```python
# [VERIFIED: codebase testing] regex confirmed against english.tex
_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')

def _check_hallucinated_employers(original: str, tailored: str) -> None:
    original_employers = _EMPLOYER_PATTERN.findall(original)
    tailored_employers = _EMPLOYER_PATTERN.findall(tailored)
    for name, dates, title in original_employers:
        if (name, dates, title) not in tailored_employers:
            logger.warning(f'Employer "{name}" from original resume not found in tailored output.')
```

### Anti-Patterns to Avoid

- **Raising exceptions in guards:** Guards must NEVER raise. Any exception from a guard would propagate to `cli.py`'s `except (RuntimeError, ValueError, ...)` block and exit 1, violating GUARD-04. Use try/except inside each guard if regex operations could fail.
- **Modifying `_validate_latex()` to be non-fatal:** D-04 is locked — hard errors stay fatal. GUARD-02 is a separate soft layer on top.
- **Buffering all warnings and printing them at the end:** D-10 says warnings print inline as they fire. No list accumulation.
- **Importing `_strip_fences` from `llm_client` in `guards.py`:** The fence detection check belongs in `llm_client.py` at the point where stripping occurs. Guards receives the `fences_stripped` bool as a parameter — it does not need to call `_strip_fences`.
- **Printing directly with `print("WARNING: ...", file=sys.stderr)` in guards.py:** Use `logger.warning()` from `log_manager` — it already produces the exact format. Direct print would duplicate logic.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LaTeX section extraction | Custom parser | `re.findall(r'\\header\{([^}]+)\}', text)` | Resume uses a single predictable macro; full LaTeX parsing is massive overkill |
| Warning output formatting | Custom formatter | `logger.warning()` from `log_manager.py` | Already in codebase, already produces `WARNING: {msg}` format |
| Fence detection in guards.py | Re-implement regex | Pass `fences_stripped: bool` from `llm_client.py` | Detection happens at the right layer (where stripping occurs); don't duplicate |

**Key insight:** Every problem in this phase is solved by Python stdlib `re` plus the existing `log_manager`. No library is needed.

---

## Critical Findings

### Finding 1: `\employer{}` Macro Is Never Used in Current Resume

[VERIFIED: codebase grep] The `\employer{name}{dates}{title}` command is defined in `english.tex`'s preamble (line 40) but has **zero invocations** in the document body. SERPRO's entry uses inline `\textbf{SERPRO}` formatting:

```latex
\textbf{SERPRO}\textbf{ | AI Engineering Intern} \hfill Feb 2024 -- Feb 2026\\
```

**Impact on GUARD-03:** With 0 `\employer{}` entries in the original, `_check_hallucinated_employers()` will always find 0 entries to verify and produce 0 warnings — for any tailored output. The guard implementation is correct per D-07/D-08 and is forward-compatible, but it is **effectively dormant** for the current resume.

**Planner action:** Implement exactly as specified (D-07). Add a comment in `guards.py` noting the guard fires only when `\employer{}` macro is used in the source resume. No spec change needed — GUARD-03 will activate if/when the resume is updated to use the macro.

### Finding 2: `log_manager.py` Already Exists and Is Unused

[VERIFIED: codebase read] `src/log_manager.py` provides `logger.warning(message)` which outputs `WARNING: {message}` to `sys.stderr`. This is exactly the format required by D-09. The module is included in the wheel build (`pyproject.toml` line 22) but nothing in `src/` currently imports it.

**Planner action:** `guards.py` should `from log_manager import logger` and use `logger.warning()`. This activates the existing module and ensures consistent warning format without duplicating the `print(..., file=sys.stderr)` pattern.

### Finding 3: `fences_stripped` Metadata Requires `generate_tailored_resume()` Refactor

[VERIFIED: codebase analysis] `generate_tailored_resume()` currently returns a plain `str` (post-stripped, post-validated). By the time `cli.py` receives the return value, the raw pre-strip content is gone. GUARD-02's first sub-check (D-05) needs to know whether `_strip_fences()` modified the text.

The detection is simple: `fences_stripped = raw.strip() != _strip_fences(raw)` — but it must be computed at the point of stripping inside `generate_tailored_resume()`.

**Recommended solution:** Change `generate_tailored_resume()` to return a `TailorResult` NamedTuple with `.content: str` and `.fences_stripped: bool`. This is the cleanest option per D-06.

**Required test updates:** `cli_test.py` mocks `generate_tailored_resume` returning a plain string in 5 tests. Each mock must be updated to return `TailorResult(content="...", fences_stripped=False)`.

### Finding 4: No `[tool.pytest.ini_options]` in `pyproject.toml`

[VERIFIED: codebase read] `pyproject.toml` has no `[tool.pytest.ini_options]` section — pytest finds the file and uses it as `configfile` but no test paths, pythonpath, or markers are configured. The pytest configuration work is Phase 8 (TEST-01). Phase 4 tests follow the existing pattern: `src/guards_test.py` using `unittest.TestCase`, with `sys.path.insert(0, str(Path(__file__).parent))` for imports.

---

## Common Pitfalls

### Pitfall 1: Guards Raising Exceptions Breaks GUARD-04

**What goes wrong:** If a guard function raises an unhandled exception (e.g., from a malformed regex match), `cli.py`'s `except (RuntimeError, ValueError, ...)` block catches it and calls `sys.exit(1)` — the output file never gets written.

**Why it happens:** The `run_guards()` call is inside the same `try` block as `generate_tailored_resume()` in `cli.py`.

**How to avoid:** Either wrap `run_guards()` in its own `try/except` in `cli.py`, OR ensure every `_check_*` function is internally exception-safe (wraps any regex/string op in try/except and logs a warning rather than propagating).

**Warning signs:** Test shows `sys.exit(1)` called when guards are given malformed input.

### Pitfall 2: `cli_test.py` Mocks Must Be Updated

**What goes wrong:** Five tests in `cli_test.py` mock `generate_tailored_resume` to return a plain `str`. After the `TailorResult` refactor, `cli.py` does `result.content` — calling `.content` on a plain `str` raises `AttributeError`, failing all CLI tests.

**Why it happens:** Mock return type mismatch after return type change.

**How to avoid:** Update all 5 mock return values in `cli_test.py` from `"\\documentclass{article}\n\\end{document}"` to `TailorResult(content="\\documentclass{article}\n\\end{document}", fences_stripped=False)`.

**Warning signs:** `cli_test.py` fails with `AttributeError: 'str' object has no attribute 'content'`.

### Pitfall 3: GUARD-02 Markdown `#` Pattern False Positives

**What goes wrong:** LaTeX uses `%` for comments, but some LaTeX environments or user content could theoretically contain lines starting with `#`. The markdown heading check `re.search(r'(?m)^#{1,6} ', tailored)` could fire if there's any `#` at line start.

**Why it happens:** The `#` character in LaTeX is a special character (used for argument references in `\newcommand`), but it can appear in document body content.

**How to avoid:** The check is intentional — `#` at line start in document body is a strong signal of markdown leakage, not valid LaTeX. Accept occasional false positives; the guard is advisory. Verified against `english.tex`: 0 false positives on clean LaTeX.

**Warning signs:** Users seeing unexpected `WARNING: Tailored output contains markdown heading markers.` on valid tailored output.

### Pitfall 4: GUARD-01 Section Comparison Is Case-Sensitive

**What goes wrong:** If the LLM changes `\header{Skills}` to `\header{skills}` or `\header{SKILLS}`, the set-difference check misses it as "present" even though the content might be structurally altered.

**Why it happens:** Python string equality is case-sensitive.

**How to avoid:** Implement the comparison as case-sensitive to match the actual LaTeX (which is case-sensitive). A case change in `\header{}` content is itself a structural alteration worth warning about. No change needed — this is correct behavior.

---

## Code Examples

Verified patterns from codebase analysis:

### GUARD-01: Extract Headers from `english.tex`

```python
# [VERIFIED: codebase testing] — correctly finds 5 sections
import re

headers = re.findall(r'\\header\{([^}]+)\}', resume_text)
# Result: ['Experience', 'Projects', 'Skills', 'Education', 'Languages']
```

### GUARD-02: Inline Markdown Check (tested against english.tex)

```python
# [VERIFIED: codebase testing] — 0 false positives on clean english.tex
import re

def has_inline_markdown(text: str) -> list[str]:
    issues = []
    if "```" in text:
        issues.append("inline code fence")
    if re.search(r'(?m)^#{1,6} ', text):
        issues.append("markdown heading")
    if re.search(r'\*\*\S[^*]*\S\*\*', text):
        issues.append("markdown bold markers")
    return issues
```

### GUARD-03: Employer Extraction

```python
# [VERIFIED: codebase testing] — returns [] for current english.tex (no \employer{} calls)
import re

_EMPLOYER_RE = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')
employers = _EMPLOYER_RE.findall(resume_text)
# Each match is (name, dates, title) tuple
```

### TailorResult NamedTuple (GUARD-02 sub-check enabler)

```python
# [ASSUMED] — design pattern; naming follows Python NamedTuple conventions
from typing import NamedTuple

class TailorResult(NamedTuple):
    content: str
    fences_stripped: bool
```

### Fences Stripped Detection (inside llm_client.py)

```python
# [VERIFIED: codebase testing] — correctly detects fence presence
raw = data["message"]["content"]
fences_stripped = raw.strip() != _strip_fences(raw)
content = _strip_fences(raw)  # no-op if already stripped
```

### `run_guards()` Signature (per decisions D-02, D-06)

```python
# [ASSUMED] — signature design; consistent with D-02 + D-06 + Finding 3

def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
```

### `cli.py` Integration (after refactor)

```python
# [ASSUMED] — integration design; follows raise-not-exit pattern from codebase
from guards import run_guards

try:
    resume_text = read_resume(resume_path)
    result = generate_tailored_resume(resume_text, job_description, model=args.model)
    run_guards(resume_text, result.content, result.fences_stripped)
    output_path = write_resume(result.content, output_dir)
except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (installed in `.venv`) |
| Config file | `pyproject.toml` (no `[tool.pytest.ini_options]` yet — Phase 8) |
| Quick run command | `.venv/bin/pytest src/ -q` |
| Full suite command | `.venv/bin/pytest src/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GUARD-01 | Missing section in tailored output triggers WARNING | unit | `.venv/bin/pytest src/guards_test.py -k section -x` | No — Wave 0 |
| GUARD-01 | No missing sections produces no warnings | unit | `.venv/bin/pytest src/guards_test.py -k section -x` | No — Wave 0 |
| GUARD-02 | fences_stripped=True triggers WARNING | unit | `.venv/bin/pytest src/guards_test.py -k fences -x` | No — Wave 0 |
| GUARD-02 | Inline ``` in body triggers WARNING | unit | `.venv/bin/pytest src/guards_test.py -k inline -x` | No — Wave 0 |
| GUARD-02 | Clean LaTeX body produces no warnings | unit | `.venv/bin/pytest src/guards_test.py -k format -x` | No — Wave 0 |
| GUARD-03 | 0 employer entries in original = 0 warnings | unit | `.venv/bin/pytest src/guards_test.py -k employer -x` | No — Wave 0 |
| GUARD-04 | run_guards never raises, write_resume still called | unit | `.venv/bin/pytest src/cli_test.py -x` | Yes (needs update) |

### Sampling Rate

- **Per task commit:** `.venv/bin/pytest src/ -q`
- **Per wave merge:** `.venv/bin/pytest src/ -v`
- **Phase gate:** All 18 existing tests + new guards tests pass before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `src/guards_test.py` — covers GUARD-01, GUARD-02, GUARD-03, GUARD-04
- [ ] Update `src/cli_test.py` — 5 mock return values need `TailorResult` wrapping
- [ ] Update `src/llm_client_test.py` — `test_invalid_llm_output_raises_value_error` mock may need update if `generate_tailored_resume` return type changes

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | Yes | 3.14.5 (.venv) / 3.11.2 (system) | — |
| `re` module | regex patterns | Yes | stdlib | — |
| `log_manager.py` | warning output | Yes | existing src/ | `print(..., file=sys.stderr)` |
| pytest | tests | Yes | 9.0.3 (.venv) | unittest (existing pattern) |

**Missing dependencies with no fallback:** None.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `TailorResult` NamedTuple is the cleanest solution for D-06 fences metadata | Architecture Patterns | Alternative (separate helper function, module-level bool) could be chosen; any approach works as long as guards sees the flag |
| A2 | `run_guards` signature includes `fences_stripped: bool = False` as third parameter | Code Examples | Planner may choose different threading (e.g., dict metadata); signature would need updating in guards.py and cli.py |
| A3 | `guards.py` uses `logger.warning()` from `log_manager` rather than direct `print()` | Architecture Patterns | Both produce identical stderr output; either is correct per D-10 |

---

## Open Questions

1. **GUARD-03 dormancy — should the planner note this for user?**
   - What we know: `\employer{}` macro is defined but never called; guard produces 0 warnings on current resume
   - What's unclear: Whether the user expects GUARD-03 to fire on any test they run
   - Recommendation: Implement exactly as specified; add a comment in `guards.py` so future implementers understand why it's dormant. No user-facing change.

2. **GUARD-04 safety — where does `run_guards()` sit in the try/except?**
   - What we know: Current `cli.py` has one `try` block covering `read_resume`, `generate_tailored_resume`, and `write_resume`
   - What's unclear: Whether `run_guards()` belongs inside that try block or its own
   - Recommendation: Place `run_guards()` inside the existing `try` block (consistent with current structure). Ensure `run_guards()` itself is internally exception-safe so no exception can propagate.

---

## Sources

### Primary (HIGH confidence)
- `src/llm_client.py` — `_strip_fences()` implementation, `generate_tailored_resume()` return type, `_validate_latex()` behavior
- `src/cli.py` — integration point, existing try/except structure, current `content` variable flow
- `src/log_manager.py` — existing `logger.warning()` method and output format
- `resumes/english.tex` — confirmed `\header{...}` sections (5), confirmed zero `\employer{}` body invocations
- `src/cli_test.py` — confirmed 5 tests mock `generate_tailored_resume` returning plain str (need updating)
- `.planning/phases/04-output-reliability-guards/04-CONTEXT.md` — all locked decisions D-01 through D-11

### Secondary (MEDIUM confidence)
- Python stdlib `re` module documentation — `re.findall`, `re.search`, `re.compile` [ASSUMED — stable API, no verification needed for findall/search]

### Tertiary (LOW confidence)
None.

---

## Metadata

**Confidence breakdown:**
- Guard regex patterns: HIGH — tested against actual `english.tex`, confirmed correct results
- Architecture (TailorResult NamedTuple): HIGH — only viable option for GUARD-02 fence detection without larger refactor
- log_manager integration: HIGH — verified in codebase, exact format match to D-09
- GUARD-03 dormancy finding: HIGH — grep-verified zero `\employer{}` invocations in document body
- Test impact on cli_test.py: HIGH — read all 5 affected tests directly

**Research date:** 2026-06-02
**Valid until:** Phase implementation complete (codebase is stable; no time-sensitive external dependencies)
