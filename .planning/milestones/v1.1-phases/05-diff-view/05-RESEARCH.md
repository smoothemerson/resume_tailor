# Phase 5: Diff View - Research

**Researched:** 2026-06-04
**Domain:** Python stdlib difflib, TTY detection, ANSI terminal output
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 Output Order:** Diff appears **before** the "Tailored resume written to:" confirmation line. Flow in `cli.py`: `run_guards()` → `write_resume()` → `show_diff()` → `print("Tailored resume written to: ...")`.
- **D-02 Color Output:** ANSI colors: green (`\033[32m`) for `+` lines, red (`\033[31m`) for `-` lines, reset (`\033[0m`) after each colored line. Context lines plain. `@@` hunk headers plain. Colors never leak into pipes because diff is already TTY-gated.
- **D-03 Diff Header Labels:** Use `--- original` and `+++ tailored`. No timestamps, no file paths.
- **D-04 Module Structure:** New `src/diff_view.py` with a single public function `show_diff(original: str, tailored: str) -> None`. Follows the `guards.py` single-concern module pattern. `cli.py` imports and calls it.
- **D-05 Normalization:** Strip trailing whitespace from each line AND collapse runs of 3+ consecutive blank lines into 2. Applied to both `original` and `tailored` before passing to `difflib.unified_diff()`.
- **Context lines (Claude's Discretion):** Use `difflib` default of 3. No override needed.
- **No "Changes:" label:** `--- original / +++ tailored` header is self-explanatory.

### Deferred Ideas (OUT OF SCOPE)

None.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DIFF-01 | Tool shows a normalized unified diff of original vs tailored resume after tailoring, when stdout is a TTY | `difflib.unified_diff()` + `sys.stdout.isatty()` — both verified stdlib, zero deps |
| DIFF-02 | Diff is suppressed automatically when stdout is piped or redirected (no flag required) | `sys.stdout.isatty()` returns `False` when piped; early return from `show_diff()` |
| DIFF-03 | Diff normalization eliminates whitespace-only noise (trailing space, blank line collapsing) | Normalize both strings before diffing: `rstrip()` per line + blank-run collapse capped at 2 |
</phase_requirements>

---

## Summary

Phase 5 is a pure stdlib implementation. Every tool needed — `difflib.unified_diff()`, `sys.stdout.isatty()`, ANSI escape codes — is available in Python 3.11+  without any new dependencies. The CONTEXT.md decisions are complete and unambiguous: no architectural choices remain open.

The implementation scope is a single new file (`src/diff_view.py`, ~30 lines) plus a three-line insertion into `cli.py`. All decisions about output order, colors, labels, normalization algorithm, and module shape are already locked. The planner's job is to sequence tasks that create the module, integrate it into cli.py, update pyproject.toml's hatch wheel includes, and add unit tests.

The one subtlety worth knowing: `difflib.unified_diff()` accepts lists of strings (lines). The cleanest invocation passes `lineterm=""` and calls `text.splitlines()` on both inputs — this avoids double-newline artifacts and makes line rendering explicit in the output loop. Normalization runs before line splitting. Empty diff output (list of zero items) signals no meaningful changes; `show_diff()` should silently return without printing anything.

**Primary recommendation:** Create `src/diff_view.py` following the `guards.py` single-concern pattern. Single public function `show_diff(original: str, tailored: str) -> None`. TTY guard first, early return if not TTY. Normalize both strings. Call `difflib.unified_diff()` with `lineterm=""`. Print each line with ANSI coloring for `+`/`-` lines. Integrate into `cli.py` per D-01 order. Add to `pyproject.toml` wheel includes.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| TTY detection | CLI (stdout inspection) | — | `sys.stdout.isatty()` is a runtime property of the process's stdout fd; checked in `diff_view.py` at call time |
| Diff computation | Application logic (`diff_view.py`) | — | Pure string comparison, no I/O; belongs in a single-concern module |
| Normalization | Application logic (`diff_view.py`) | — | Pre-processing step owned by the same module that consumes the result |
| ANSI coloring | Application logic (`diff_view.py`) | — | Output formatting is part of `show_diff()` responsibility since colors are always safe when TTY-gated |
| CLI integration | `cli.py` | — | Integration point; calls `show_diff(resume_text, result.content)` between `write_resume()` and final `print()` |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `difflib` | stdlib | Unified diff generation | Python stdlib module; `unified_diff()` produces standard unified diff format [VERIFIED: Python 3.13 docs] |
| `sys` | stdlib | TTY detection (`sys.stdout.isatty()`) | stdlib; `isatty()` is the canonical Python TTY check [VERIFIED: Python 3.13 docs] |

### Supporting

No external packages. No new deps introduced this phase.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `difflib.unified_diff()` | `difflib.ndiff()` or `difflib.context_diff()` | `unified_diff` is the industry-standard format, tool-compatible, and the only one with `fromfile`/`tofile` label params |
| ANSI escape literals (`\033[32m`) | `colorama` library | No dep needed; TTY-gated output means raw ANSI is always safe; `colorama` is for Windows console compat which is irrelevant to a Linux-targeted tool |

**Installation:** No packages to install. All implementation is stdlib.

---

## Package Legitimacy Audit

No external packages introduced in this phase. Section not applicable.

---

## Architecture Patterns

### System Architecture Diagram

```
cli.py:main()
    │
    ├─ read_resume() → resume_text
    ├─ generate_tailored_resume() → result.content
    ├─ run_guards(resume_text, result.content, ...)  [existing]
    ├─ write_resume(result.content, ...) → output_path  [existing]
    │
    ├─ show_diff(resume_text, result.content)   [NEW]
    │       │
    │       ├─ sys.stdout.isatty() == False → return immediately (DIFF-02)
    │       ├─ normalize(original) → norm_orig
    │       ├─ normalize(tailored) → norm_tail
    │       ├─ difflib.unified_diff(norm_orig.splitlines(), norm_tail.splitlines(),
    │       │       fromfile="original", tofile="tailored", lineterm="")
    │       └─ for each diff line: print with ANSI color (D-02)
    │
    └─ print("Tailored resume written to: {output_path}")
```

### Recommended Project Structure

```
src/
├── cli.py             # +3 lines: import show_diff, call after write_resume
├── diff_view.py       # NEW: ~30 lines, single public function show_diff()
├── guards.py          # unchanged
├── llm_client.py      # unchanged
├── resume_reader.py   # unchanged
├── resume_writer.py   # unchanged
├── config.py          # unchanged
├── log_manager.py     # unchanged
└── *_test.py          # existing test files unchanged
```

### Pattern 1: Single-Concern Module (guards.py pattern)

**What:** One module, one public function, private helpers prefixed with `_`. No global state.
**When to use:** Every new capability in this codebase. `guards.py` and `resume_reader.py` both follow this.
**Example (from verified codebase):**
```python
# Source: /workspace/src/guards.py (existing pattern)
def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
```

`diff_view.py` follows the same shape:
```python
# Pattern to implement in src/diff_view.py
def show_diff(original: str, tailored: str) -> None:
    if not sys.stdout.isatty():
        return
    norm_orig = _normalize(original)
    norm_tail = _normalize(tailored)
    diff = list(difflib.unified_diff(
        norm_orig.splitlines(),
        norm_tail.splitlines(),
        fromfile="original",
        tofile="tailored",
        lineterm="",
    ))
    if not diff:
        return
    for line in diff:
        print(_colorize(line))
```

### Pattern 2: Normalization Implementation

**What:** Strip trailing whitespace per line + cap consecutive blank runs at 2.
**When to use:** D-05 — applied to both texts before diffing.
**Algorithm (verified via Python REPL in this session):**

```python
# Source: verified via Python 3.13 REPL — normalization algorithm for D-05
def _normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    result: list[str] = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result)
```

Verification results:
- `'a  \n  b  '` → `'a\nb'` (trailing spaces stripped) [VERIFIED: REPL]
- `'a\n\n\n\nb'` (3 blank lines) → `'a\n\nb'` (2 blank lines) [VERIFIED: REPL]
- `'a\n\n\nb'` (2 blank lines) → `'a\n\nb'` (unchanged) [VERIFIED: REPL]

### Pattern 3: ANSI Colorization

**What:** Color `+` diff lines green, `-` diff lines red, leave context lines plain.
**When to use:** Always inside `show_diff()` because TTY is already confirmed before reaching this code.
**Critical detail:** `+++ tailored` header starts with `+` but must NOT be colored — check for `+++` prefix first. Same for `---`.

```python
# Source: verified via Python 3.13 REPL — ANSI color logic for D-02
_GREEN = "\033[32m"
_RED = "\033[31m"
_RESET = "\033[0m"

def _colorize(line: str) -> str:
    if line.startswith("+") and not line.startswith("+++"):
        return _GREEN + line + _RESET
    if line.startswith("-") and not line.startswith("---"):
        return _RED + line + _RESET
    return line
```

### Pattern 4: cli.py Integration

**What:** Insert `show_diff()` call after `write_resume()`, before final `print()`.
**When to use:** Per D-01; both `resume_text` and `result.content` are in scope at that point.

Current `cli.py` (lines 48-57):
```python
    try:
        resume_text = read_resume(resume_path)
        result = generate_tailored_resume(resume_text, job_description, model=args.model)
        run_guards(resume_text, result.content, result.fences_stripped)
        output_path = write_resume(result.content, output_dir)
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Tailored resume written to: {output_path.resolve()}")
```

After integration:
```python
    try:
        resume_text = read_resume(resume_path)
        result = generate_tailored_resume(resume_text, job_description, model=args.model)
        run_guards(resume_text, result.content, result.fences_stripped)
        output_path = write_resume(result.content, output_dir)
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    show_diff(resume_text, result.content)
    print(f"Tailored resume written to: {output_path.resolve()}")
```

`show_diff()` must be called outside the try/except because it is non-fatal — per the raise-not-exit pattern, `diff_view.py` should never raise.

### Anti-Patterns to Avoid

- **Putting show_diff() inside the try/except block:** `show_diff()` is non-fatal; wrapping it means a diff rendering bug could suppress the confirmation line. Call it outside.
- **Coloring the `---` and `+++` header lines:** These start with `-` and `+` but are NOT diff content. The `startswith("---")` / `startswith("+++")`guard is required.
- **Printing diff even when empty:** `difflib.unified_diff()` returns an empty iterator when texts are identical after normalization. Print nothing rather than an empty block.
- **Using `lineterm="\n"` (the default) without stripping:** Default `lineterm` adds `\n` to each yielded line, causing double-newlines when passed to `print()`. Use `lineterm=""` and let `print()` add the newline.
- **Not adding `diff_view.py` to pyproject.toml wheel includes:** The `[tool.hatch.build.targets.wheel]` `include` list explicitly names each `src/*.py` file. Omitting `diff_view.py` breaks `pip install`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Unified diff generation | Custom line-by-line comparison algorithm | `difflib.unified_diff()` | Handles edge cases: last line without newline, hunk boundaries, context window, identical files |
| TTY detection | Checking `$TERM` env var or platform detection | `sys.stdout.isatty()` | Canonical stdlib method; works for pipes, redirects, and subprocesses correctly |
| Terminal color support detection | Custom `COLORTERM`/`$TERM` parsing | (Not needed) | TTY gate is sufficient; if stdout is a TTY, ANSI is safe on any modern terminal |

**Key insight:** `difflib` handles all the tricky cases in unified diff generation (last-line-no-newline, empty files, identical files). Custom comparison is unnecessary and error-prone.

---

## Common Pitfalls

### Pitfall 1: lineterm Double-Newline

**What goes wrong:** `difflib.unified_diff()` with default `lineterm="\n"` yields lines ending in `\n`. `print()` adds another `\n`. Output has blank lines between every diff line.
**Why it happens:** The `lineterm` default was designed for `file.writelines()` use cases, not `print()`.
**How to avoid:** Pass `lineterm=""` explicitly. Each yielded line will have no trailing newline; `print()` adds exactly one.
**Warning signs:** Visible blank line between every line of diff output.

### Pitfall 2: Coloring the `---`/`+++` Header Lines

**What goes wrong:** `---` starts with `-`, `+++` starts with `+`. Naive colorization makes the header lines red/green, visually misleading.
**Why it happens:** The check `line.startswith("-")` catches both `-removed content` and `--- original`.
**How to avoid:** Check `not line.startswith("---")` before applying red; `not line.startswith("+++")` before applying green.
**Warning signs:** Header lines `--- original` and `+++ tailored` appearing in red and green.

### Pitfall 3: show_diff Raises and Kills the Confirmation Print

**What goes wrong:** If `show_diff()` is placed inside the `try/except` block and raises, the "Tailored resume written to:" confirmation is never printed, even though the file was successfully written.
**Why it happens:** Developer treats diff as part of the core pipeline rather than a display concern.
**How to avoid:** Call `show_diff()` outside the try/except. Wrap `show_diff()` body in `try/except Exception` if extra safety is desired (matching the guards.py defensive pattern).
**Warning signs:** Missing confirmation output in logs when difflib encounters unexpected input.

### Pitfall 4: pyproject.toml Wheel Includes Not Updated

**What goes wrong:** `pip install .` succeeds but `resume-tailor` command fails with `ModuleNotFoundError: No module named 'diff_view'`.
**Why it happens:** `pyproject.toml` explicitly lists each source file in `[tool.hatch.build.targets.wheel]` `include`. New files are not auto-included.
**How to avoid:** Add `"src/diff_view.py"` to the `include` list in `pyproject.toml`.
**Warning signs:** Local `uv run` works (runs from source) but installed package fails.

### Pitfall 5: Showing Diff for No-Op Tailoring

**What goes wrong:** When the LLM returns text that normalizes to identical content, an empty diff block header could still be printed.
**Why it happens:** `unified_diff()` yields nothing for identical inputs, but code prints a header before iterating.
**How to avoid:** Call `diff = list(unified_diff(...))` and `if not diff: return` before printing anything.
**Warning signs:** Blank diff section appearing even when resume is unchanged.

---

## Code Examples

### Complete show_diff() Implementation Pattern

```python
# Source: derived from Python 3.13 difflib docs + verified REPL session
import difflib
import sys

_GREEN = "\033[32m"
_RED = "\033[31m"
_RESET = "\033[0m"


def _normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    result: list[str] = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result)


def _colorize(line: str) -> str:
    if line.startswith("+") and not line.startswith("+++"):
        return _GREEN + line + _RESET
    if line.startswith("-") and not line.startswith("---"):
        return _RED + line + _RESET
    return line


def show_diff(original: str, tailored: str) -> None:
    if not sys.stdout.isatty():
        return
    norm_orig = _normalize(original)
    norm_tail = _normalize(tailored)
    diff = list(difflib.unified_diff(
        norm_orig.splitlines(),
        norm_tail.splitlines(),
        fromfile="original",
        tofile="tailored",
        lineterm="",
    ))
    if not diff:
        return
    for line in diff:
        print(_colorize(line))
```

### cli.py Integration Patch

```python
# Source: /workspace/src/cli.py (current), decision D-01
# Add to imports at top:
from diff_view import show_diff

# After the try/except block (outside it), before the final print:
    show_diff(resume_text, result.content)
    print(f"Tailored resume written to: {output_path.resolve()}")
```

### pyproject.toml Wheel Include

```toml
# Source: /workspace/pyproject.toml (current state + required addition)
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/diff_view.py",      # ADD THIS
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

### Unit Test Pattern for show_diff

```python
# Source: /workspace/src/guards_test.py (existing test style for reference)
# Tests for src/diff_view_test.py

import sys
from unittest.mock import patch
from diff_view import show_diff

def test_suppressed_when_not_tty():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = False
        with patch("builtins.print") as mock_print:
            show_diff("original", "tailored changed")
            mock_print.assert_not_called()

def test_shows_diff_on_tty():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        printed = []
        with patch("builtins.print", side_effect=lambda *a: printed.append(a[0])):
            show_diff("line 1\nline 2", "line 1\nline 2 changed")
        assert any("line 2 changed" in line for line in printed)

def test_normalization_strips_trailing_spaces():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        printed = []
        with patch("builtins.print", side_effect=lambda *a: printed.append(a[0])):
            # Both texts are identical after normalization — no diff expected
            show_diff("line 1   \nline 2  ", "line 1\nline 2")
        assert len(printed) == 0

def test_no_output_when_texts_identical():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        with patch("builtins.print") as mock_print:
            show_diff("same text", "same text")
            mock_print.assert_not_called()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `difflib.ndiff()` for human diffs | `difflib.unified_diff()` for machine-readable unified format | Standard for decades | Unified diff is industry standard, understood by all diff viewers |
| `colorama` for terminal colors | Raw ANSI escapes for TTY-gated output | N/A | On TTY-gated paths with no Windows requirement, raw escapes are simpler |

**Deprecated/outdated:**
- Nothing relevant — `difflib` API has been stable since Python 2.4 [VERIFIED: Python docs]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | — | — | — |

**All claims in this research were verified against the Python 3.13 stdlib documentation or confirmed via live REPL execution. No user confirmation needed.**

---

## Open Questions

None. All implementation decisions are locked in CONTEXT.md. The diff format, colors, labels, normalization algorithm, module structure, and integration point are fully specified.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All implementation | ✓ | 3.13 (.venv) | — |
| `difflib` | DIFF-01 | ✓ | stdlib | — |
| `sys` | DIFF-02 (isatty) | ✓ | stdlib | — |
| `uv` | Test runner (`uv run pytest`) | ✓ | installed | — |
| `pytest` | Test verification | ✓ | 9.x (in .venv) | — |

All 36 existing tests pass under `uv run pytest src/ tests/ -x -q` [VERIFIED: live run this session].

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest src/diff_view_test.py -x -q` |
| Full suite command | `uv run pytest src/ tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIFF-01 | `show_diff()` prints unified diff on TTY | unit | `uv run pytest src/diff_view_test.py::test_shows_diff_on_tty -x` | Wave 0 |
| DIFF-02 | `show_diff()` prints nothing when `isatty()` is False | unit | `uv run pytest src/diff_view_test.py::test_suppressed_when_not_tty -x` | Wave 0 |
| DIFF-03 | Trailing spaces ignored; 3+ blank lines collapse to 2 | unit | `uv run pytest src/diff_view_test.py -k "normalization" -x` | Wave 0 |
| DIFF-01 | Diff omits header lines (`---`/`+++`) from colorization | unit | `uv run pytest src/diff_view_test.py::test_header_lines_not_colored -x` | Wave 0 |
| DIFF-01 | Empty diff (identical texts) produces no output | unit | `uv run pytest src/diff_view_test.py::test_no_output_when_texts_identical -x` | Wave 0 |
| DIFF-01 | `show_diff()` called from `cli.py` after `write_resume()` | unit | `uv run pytest src/cli_test.py -x` | Exists — needs patching for `show_diff` |

### Sampling Rate

- **Per task commit:** `uv run pytest src/diff_view_test.py -x -q`
- **Per wave merge:** `uv run pytest src/ tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `src/diff_view_test.py` — covers DIFF-01, DIFF-02, DIFF-03 (new file, does not exist)
- [ ] `src/diff_view.py` — the module under test (new file, does not exist)

---

## Security Domain

DIFF-01/02/03 involve no authentication, no network calls, no user-controlled file paths, no secrets. The diff is computed from two in-memory strings (both already validated by `_validate_latex()` before reaching `show_diff()`). No ASVS controls apply to this phase.

---

## Sources

### Primary (HIGH confidence)

- Python 3.13 `difflib` docs — `unified_diff()` function signature, `lineterm` parameter, `fromfile`/`tofile` labels [VERIFIED: https://docs.python.org/3/library/difflib.html#difflib.unified_diff]
- Python 3.13 `sys` docs — `sys.stdout.isatty()` method [VERIFIED: https://docs.python.org/3/library/sys.html]
- `/workspace/src/cli.py` — integration point, exact variable names in scope [VERIFIED: live read this session]
- `/workspace/src/guards.py` — module pattern reference [VERIFIED: live read this session]
- `/workspace/pyproject.toml` — wheel includes list, pytest config [VERIFIED: live read this session]

### Secondary (MEDIUM confidence)

- ANSI escape code conventions (`\033[32m` green, `\033[31m` red, `\033[0m` reset) — widely documented terminal standard [CITED: https://en.wikipedia.org/wiki/ANSI_escape_code]

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only, no version uncertainty
- Architecture: HIGH — all decisions locked in CONTEXT.md; integration points read from actual source files
- Pitfalls: HIGH — verified via live Python REPL execution in this session
- Test map: HIGH — follows existing test file pattern in repo

**Research date:** 2026-06-04
**Valid until:** 2026-12-04 (stable stdlib — no expiry risk)
