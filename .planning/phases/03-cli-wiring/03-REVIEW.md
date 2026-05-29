---
phase: 03-cli-wiring
reviewed: 2026-05-29T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/cli.py
  - src/cli_test.py
  - pyproject.toml
findings:
  critical: 3
  warning: 4
  info: 2
  total: 9
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-05-29
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

The three reviewed files implement a CLI entry point (`cli.py`), its unit tests (`cli_test.py`), and package metadata (`pyproject.toml`). The CLI logic itself is concise and mostly correct for the happy path. However there are three critical defects: a broken error-handling contract between `resume_reader` and `cli.py` that silently bypasses the intended error handler; two modules required at runtime (`llm_client`, `log_manager`) that are entirely absent from the wheel include list and will cause an `ImportError` on any installed run; and an inconsistency between the declared entry point module path and the actual package structure. Four warnings cover uncaught I/O exceptions from `write_resume`, dead `argparse` setup, missing CLI flag implementation documented in `CLAUDE.md`, and a split dev-dependency declaration that hides `pytest` from standard tooling. Two info items cover the case-sensitive sentinel and a test that does not assert on the job description text passed to the LLM.

---

## Critical Issues

### CR-01: `read_resume` calls `sys.exit(1)` directly — bypasses `cli.py` error handler

**File:** `src/resume_reader.py:12` (called from `src/cli.py:41`)

**Issue:** `resume_reader.read_resume` catches `FileNotFoundError` and calls `sys.exit(1)` directly instead of raising. The `try/except (RuntimeError, ValueError)` block in `cli.py` at line 44 therefore never runs for the missing-file case. The consequence is twofold: (1) the error message printed is the bare `"ERROR: Base resume not found at …"` from `log_manager`, not the CLI's formatted `"Error: …"` to `stderr`; (2) any future caller of `read_resume` that wraps it in a try/except will be silently bypassed by the `sys.exit` inside. The test suite mocks `read_resume` entirely, so this defect is invisible in tests.

**Fix:** Remove `sys.exit` from `resume_reader` and raise instead so callers control exit behavior:

```python
# src/resume_reader.py
def read_resume(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Base resume not found at {path}") from exc
```

Then in `cli.py`, add `FileNotFoundError` to the caught exceptions:

```python
# src/cli.py line 44
except (RuntimeError, ValueError, FileNotFoundError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

---

### CR-02: `llm_client.py` and `log_manager.py` are missing from the wheel include list — installed package crashes on import

**File:** `pyproject.toml:21`

**Issue:** The `[tool.hatch.build.targets.wheel] include` list at line 21 enumerates only four files:
```
["src/cli.py", "src/config.py", "src/resume_reader.py", "src/resume_writer.py"]
```
`src/llm_client.py` and `src/log_manager.py` are absent. `cli.py` imports `generate_tailored_resume` from `llm_client` (line 5), and both `llm_client` and `resume_reader` import `logger` from `log_manager`. Any user who installs the wheel with `pip install resume-tailor.whl` and runs `resume-tailor` will immediately get:
```
ModuleNotFoundError: No module named 'llm_client'
```
The tool is non-functional when installed as a package.

**Fix:**

```toml
# pyproject.toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
include = [
    "src/cli.py",
    "src/config.py",
    "src/llm_client.py",
    "src/log_manager.py",
    "src/resume_reader.py",
    "src/resume_writer.py",
]
```

---

### CR-03: Entry point module path `"cli:main"` is wrong for the declared wheel layout

**File:** `pyproject.toml:10`

**Issue:** The `[project.scripts]` entry point is declared as `resume-tailor = "cli:main"`. The wheel's `sources = ["src"]` setting (line 20) means hatchling roots the package at `src/`, so modules install as top-level names (`cli`, `config`, etc.). However, the `include` list uses full `src/`-prefixed paths (`"src/cli.py"`). When both `sources` and explicit `include` paths prefixed with `src/` are combined in hatchling, the effective install name depends on hatchling version behavior — this is fragile. If the sources rewrite is applied, `"cli:main"` is correct; if it is not, the entry point would need to be `"src.cli:main"`. The combination has been observed to silently install broken entry points in some hatchling versions. The safe fix is to use the package-style entry point and ensure the `src` layout is unambiguous.

**Fix:** Either drop the explicit `include` (let hatchling pick up all `.py` files under `src/`) and keep `"cli:main"`, or switch to a proper package structure. The minimal safe fix:

```toml
[tool.hatch.build.targets.wheel]
sources = ["src"]
# Remove explicit include; hatchling will include all .py files under src/
```

This also resolves CR-02 automatically by including all modules.

---

## Warnings

### WR-01: `write_resume` can raise `OSError`/`PermissionError` — not caught by `cli.py`

**File:** `src/cli.py:43` (calls `src/resume_writer.py:6-9`)

**Issue:** `write_resume` calls `output_dir.mkdir(parents=True, exist_ok=True)` and `output_path.write_text(...)`. Both can raise `OSError` (e.g., permission denied, read-only filesystem, disk full). The `except (RuntimeError, ValueError)` on line 44 of `cli.py` does not catch `OSError`, so a filesystem failure produces an unhandled traceback rather than a clean error message and exit code 1. This is a user-facing quality failure for a CLI tool.

**Fix:**

```python
# src/cli.py line 44
except (RuntimeError, ValueError, FileNotFoundError, OSError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

---

### WR-02: `argparse` is set up but `parse_args()` result is discarded — flags described in CLAUDE.md are never wired

**File:** `src/cli.py:11-15`

**Issue:** `parser.parse_args()` is called at line 15 but its return value is never captured. The `CLAUDE.md` specification explicitly lists `--model`, `--resume`, and `--output-dir` as flags that `argparse` should handle. None of them are declared with `add_argument`. The `argparse` setup today provides only the auto-generated `--help` flag, while `BASE_RESUME_PATH`, `OUTPUT_DIR`, and `OLLAMA_MODEL` are hardcoded from `config.py`. A user cannot redirect to a different resume file or output directory without editing source.

**Fix:** Either implement the three flags and use their values, or remove the dead `argparse` setup entirely if flags are out of scope for this phase. Dead setup misleads future readers:

```python
# If deferring flags — remove the dead setup:
# parser = argparse.ArgumentParser(...)
# parser.parse_args()
```

---

### WR-03: Dev dependencies split across two incompatible sections — `pytest` is invisible to `pip install -e ".[dev]"`

**File:** `pyproject.toml:12-14` and `pyproject.toml:23-25`

**Issue:** `ruff` and `mypy` are declared in `[project.optional-dependencies] dev`, while `pytest` is declared in `[dependency-groups] dev` (the PEP 735 format, supported by `uv` but not by `pip`). Running `pip install -e ".[dev]"` installs `ruff` and `mypy` but silently omits `pytest`. Conversely, `uv sync --group dev` installs `pytest` but does not pick up optional dependencies unless explicitly requested. The split means no single standard install command produces a complete dev environment.

**Fix:** Choose one mechanism. For a `uv`-first project, consolidate into `[dependency-groups]`:

```toml
[dependency-groups]
dev = ["ruff", "mypy", "pytest>=9.0.3"]
```

And remove `[project.optional-dependencies]`.

---

### WR-04: `log_manager` violates the project's stated architecture constraint

**File:** `src/llm_client.py:6`, `src/resume_reader.py:4`

**Issue:** `CLAUDE.md` explicitly prohibits the `logging` module and states: "Direct `print(..., file=sys.stderr)` is cleaner for a CLI." The codebase introduces a custom `log_manager` module that wraps `print` to `stderr`. This is a thin abstraction over exactly what the convention forbids. The module itself is harmless, but it (a) creates an extra import dependency in every module, (b) was omitted from the wheel include list (CR-02), and (c) contradicts the documented convention. Additionally, the `logger.info(...)` calls in `llm_client.py` emit informational noise to `stderr` during normal operation (e.g., "Checking Ollama health...", "Calling Ollama /api/chat with model …", "LLM response validated successfully.") which pollutes `stderr` for users who redirect it.

**Fix:** Remove `log_manager.py`. Replace `logger.error(...)` calls with direct `print(..., file=sys.stderr)` at the call site, or let the raised exceptions propagate to `cli.py` for unified error printing. Remove informational `logger.info(...)` calls or gate them behind a `--verbose` flag.

---

## Info

### IN-01: `END` sentinel is case-sensitive with no user-visible indication

**File:** `src/cli.py:28`

**Issue:** The sentinel check `line.strip() == "END"` is case-sensitive. A user typing `end` or `End` will have that text appended to the job description instead of terminating input. The prompt on line 18 says `Type END on a new line`, which is explicit, but the behavior on mismatch is silent accumulation rather than a helpful error. For a personal tool this is a minor annoyance; for a portfolio piece it is a rough edge.

**Fix:** Either accept any case (`line.strip().upper() == "END"`) or leave it as-is but document the strictness in the prompt string.

---

### IN-02: `test_end_sentinel_breaks_loop` does not assert that "END" is excluded from the job description

**File:** `src/cli_test.py:26-28`

**Issue:** The test verifies that "line one" and "line two" are present in the job description argument, but does not assert that "END" is absent. If the sentinel stripping logic were accidentally removed (the `if line.strip() == "END": break` becoming `if line.strip() == "END": pass`), the test would still pass because `assertIn` only checks presence, not exact content.

**Fix:** Add a negative assertion:

```python
self.assertNotIn("END", call_args[0][1])
```

---

_Reviewed: 2026-05-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
