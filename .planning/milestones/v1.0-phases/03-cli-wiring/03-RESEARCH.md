# Phase 3: CLI Wiring - Research

**Researched:** 2026-05-29
**Domain:** Python CLI orchestration — `argparse`, `sys.stdin` multiline input, `sys.exit`, `pathlib.Path`
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The full flow lives inside `cli.py:main()` directly — no separate `main.py` module
- **D-02:** Exception catching uses a single broad `try/except` block wrapping `read_resume()` + `generate_tailored_resume()` + `write_resume()`. Catches `RuntimeError` and `ValueError` raised by `llm_client.py`
- **D-03:** Error messages at the CLI boundary use `print(..., file=sys.stderr)` — not `log_manager`
- **D-04:** On startup, print a short instructions banner to stdout:
  ```
  Resume Tailor
  Paste the job description below. Type END on a new line to submit.

  >
  ```
  The `>` prompt stays on its own line — user types after it for the first line, then continues on new lines
- **D-05:** Input is collected with a `while True` loop using `input()`, accumulating lines until the user types `END` on a new line. `EOFError` (Ctrl+D) is caught and treated as submission
- **D-06:** Banner and prompt print to stdout. Error messages print to stderr
- **D-07:** No new flags added in Phase 3. `argparse` stays in `cli.py` for `--help` only
- **D-08:** Print a progress message to stdout after job description submission and before the `generate_tailored_resume()` call. Exact wording and `flush=True` are Claude's discretion

### Claude's Discretion

- Exact wording of the progress message (e.g., "Tailoring resume..." or "Calling Ollama — this may take a minute...")
- Whether to flush stdout after the progress message (`print(..., flush=True)`) — recommended since Ollama can take up to 300s
- The exact `except` clause types: `except (RuntimeError, ValueError) as e` is sufficient; whether to also catch `Exception` as a fallback is Claude's call

### Deferred Ideas (OUT OF SCOPE)

- `--dry-run` flag
- `--model` / `--resume` CLI overrides
- Diff output (base vs tailored resume)
- Streaming token output
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-02 | User can input a multiline job description via terminal prompt (type END on a new line to submit); EOFError treated as submission | D-05 `while True` / `input()` / `EOFError` pattern — standard Python idiom, fully verified |
| CORE-03 | User sees a progress message before the LLM call starts so the tool does not appear frozen | D-08 `print(..., flush=True)` before `generate_tailored_resume()` call |
| CORE-06 | Tool prints a success message with the full output file path on completion | `write_resume()` returns `Path`; `str(output_path.resolve())` gives the absolute path |
</phase_requirements>

---

## Summary

Phase 3 is a pure-Python orchestration phase: no new packages, no new modules, no new files beyond filling in `cli.py:main()`. All the hard work — Ollama calls, LaTeX validation, file writing — is already done in Phase 1 and Phase 2 modules. This phase connects those modules in a linear sequence: read resume → collect job description → print progress → call LLM → write output → print success path.

The only non-trivial implementation concern is the multiline input loop (D-05). Python's `input()` blocks on each line; accumulating until a sentinel (`END`) or `EOFError` is a well-established stdlib idiom. The `flush=True` on the progress print (D-08) is critical: without it, the output may be buffered and the terminal appears frozen for up to 300 seconds during Ollama inference.

`resume_reader.py` calls `sys.exit(1)` directly on `FileNotFoundError` — it will never return to the `try` block in `main()`. The `try/except (RuntimeError, ValueError)` in `main()` is therefore only guarding `generate_tailored_resume()` (which raises both) and `write_resume()` (which raises neither in practice, but is included for safety).

**Primary recommendation:** Implement `cli.py:main()` exactly as specified in CONTEXT.md — no architectural judgment calls remain; every decision is locked.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Banner + prompt display | CLI (`cli.py`) | — | Human-facing output at the entry point |
| Multiline JD collection | CLI (`cli.py`) | — | Input loop lives at the human boundary; modules receive clean strings |
| Progress message | CLI (`cli.py`) | — | UX concern at the orchestration layer |
| Resume reading | `resume_reader.py` | — | Already implemented; `cli.py` calls it with `BASE_RESUME_PATH` |
| LLM inference + validation | `llm_client.py` | — | Already implemented; `cli.py` calls `generate_tailored_resume()` |
| File writing | `resume_writer.py` | — | Already implemented; `cli.py` calls `write_resume()` with `OUTPUT_DIR` |
| Error display + exit | CLI (`cli.py`) | — | Human-facing boundary; internal modules use `log_manager`, not `print` |
| Success message + exit | CLI (`cli.py`) | — | CORE-06 output belongs at the CLI boundary |

---

## Standard Stack

### Core

All components are Python stdlib — no installation needed. [VERIFIED: Python 3.13 stdlib]

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `argparse` | stdlib | `--help` flag handling | Already present in `cli.py` stub; project constraint (no Click/Typer) |
| `sys` | stdlib | `sys.stderr`, `sys.exit(1)` | Project convention — `print(..., file=sys.stderr)` for errors |
| `pathlib.Path` | stdlib | Absolute path resolution via `.resolve()` | Project convention — `pathlib` over `os.path` everywhere |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `resume_reader` | local | `read_resume(path) -> str` | Called first with `BASE_RESUME_PATH` |
| `llm_client` | local | `generate_tailored_resume(resume_text, jd) -> str` | Called after JD collected |
| `resume_writer` | local | `write_resume(content, output_dir) -> Path` | Called after LLM returns |
| `config` | local | `BASE_RESUME_PATH`, `OUTPUT_DIR` constants | Imported into `cli.py`; no hardcoded paths |

### Alternatives Considered

None — all choices are locked by CONTEXT.md decisions or project constraints.

---

## Package Legitimacy Audit

No external packages are installed in this phase. Phase 3 uses only Python stdlib and existing project-local modules.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
  User terminal
       |
       v
  cli.py:main()
       |
       +--[1]--> print banner + ">" prompt (stdout)
       |
       +--[2]--> while True loop: input() -> accumulate lines
       |              EOFError / "END" sentinel -> break
       |
       +--[3]--> read_resume(BASE_RESUME_PATH)
       |              sys.exit(1) on FileNotFoundError (does not return)
       |
       +--[4]--> print progress message (stdout, flush=True)
       |
       +--[5]--> generate_tailored_resume(resume_text, jd)
       |              raises RuntimeError or ValueError on failure
       |
       +--[6]--> write_resume(content, OUTPUT_DIR)
       |              returns Path
       |
       +--[7]--> print success message with absolute path (stdout)
       |
       v
     exit 0
```

Error path: `except (RuntimeError, ValueError) as e` catches steps 5-6, prints to stderr, calls `sys.exit(1)`.

### Recommended Project Structure

No structural changes. Phase 3 only modifies `src/cli.py`. All other files remain unchanged.

```
src/
├── cli.py          # MODIFIED — main() fully implemented
├── config.py       # unchanged
├── llm_client.py   # unchanged
├── log_manager.py  # unchanged
├── resume_reader.py# unchanged
└── resume_writer.py# unchanged
```

### Pattern 1: Multiline Input Collection with Sentinel (D-05)

**What:** Accumulate `input()` lines into a list until the user types `END` or sends EOF (Ctrl+D)
**When to use:** Whenever a CLI needs multi-paragraph text from a user without a file argument

```python
# Source: [VERIFIED: Python 3 docs — built-in functions: input()]
lines: list[str] = []
while True:
    try:
        line = input()
    except EOFError:
        break
    if line.strip() == "END":
        break
    lines.append(line)
job_description = "\n".join(lines)
```

Key detail: `input()` returns the line without the trailing newline. The `"\n".join(lines)` correctly reconstructs the original multiline text. [VERIFIED: Python 3 docs]

### Pattern 2: Flushed Progress Print Before Blocking Call (D-08)

**What:** Print a message to stdout and force it to the terminal before a long-blocking operation
**When to use:** Any time a blocking call (network, subprocess, file I/O) follows a user-visible message

```python
# Source: [VERIFIED: Python 3 docs — print() built-in, flush parameter]
print("Tailoring resume — this may take a minute...", flush=True)
```

Without `flush=True`, Python's stdout buffering may hold the message in memory until after `generate_tailored_resume()` returns. Since Ollama inference can take up to 300 seconds, the terminal would appear frozen. `flush=True` forces the write immediately. [VERIFIED: Python 3 docs]

### Pattern 3: Absolute Path for Success Message (CORE-06)

**What:** Convert the `Path` returned by `write_resume()` to a guaranteed absolute path string
**When to use:** Any time a CLI prints a file path that the user will reference directly

```python
# Source: [VERIFIED: Python 3 docs — pathlib.Path.resolve()]
output_path = write_resume(content, OUTPUT_DIR)
print(f"Tailored resume written to: {output_path.resolve()}")
```

`Path.resolve()` resolves symlinks and makes the path absolute even if `OUTPUT_DIR` was constructed with a relative component. Since `config.py` anchors paths to `Path(__file__).parent.parent`, `output_path` is already absolute in practice, but `.resolve()` is idiomatic and safe. [VERIFIED: Python 3 docs]

### Pattern 4: Single try/except at the CLI Boundary (D-02)

**What:** One broad exception block around the full 3-step flow; individual modules do not catch at the CLI level
**When to use:** Linear flows where errors in any step should abort the whole operation

```python
# Source: [ASSUMED — Python error-handling idiom]
try:
    resume_text = read_resume(BASE_RESUME_PATH)
    content = generate_tailored_resume(resume_text, job_description)
    output_path = write_resume(content, OUTPUT_DIR)
except (RuntimeError, ValueError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

Note: `read_resume()` calls `sys.exit(1)` directly — it will never raise into this `except` block. The block guards `generate_tailored_resume()` (raises `RuntimeError` and `ValueError`) and `write_resume()` (no documented raises, but included for safety).

### Anti-Patterns to Avoid

- **Importing `log_manager` in `cli.py`:** D-03 is explicit — `cli.py` is the human-facing boundary; use `print(..., file=sys.stderr)` directly. `log_manager` stays inside domain modules.
- **Adding `--model` or `--resume` flags:** D-07 is explicit — no new flags in Phase 3. `argparse` is present only for `--help`.
- **Catching `Exception` as a broad fallback without deliberate intent:** If added, it must print the exception message and still call `sys.exit(1)`. Bare `except Exception: pass` would swallow errors silently.
- **Printing the relative path in the success message:** Use `output_path.resolve()` not `str(output_path)` — the user needs to `cd` to the file or use an absolute path in their editor.
- **Not flushing stdout before the LLM call:** Without `flush=True`, the progress message may not appear until after inference completes, defeating its purpose.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Absolute path resolution | Custom join/normalization | `Path.resolve()` | Handles symlinks, `..` components, and CWD-relative paths correctly |
| Multiline terminal input | readline wrapper or curses | `input()` in `while True` | Correct Python idiom for sentinel-terminated input; handles TTY and pipe input uniformly |
| Stdout flushing | Manual `sys.stdout.flush()` call | `print(..., flush=True)` | Single parameter; no separate call needed; idiomatic |

**Key insight:** Phase 3 has no complex problems — the entire value is in wiring together modules that already exist.

---

## Common Pitfalls

### Pitfall 1: Unflushed Progress Message

**What goes wrong:** The user types the job description and hits `END`, then the terminal appears frozen for 60-300 seconds with no visible output — they do not know if the tool received their input.
**Why it happens:** Python buffers stdout by default when output is not a TTY (e.g., piped) and sometimes even in TTY mode depending on the system. Without `flush=True`, the buffer may not flush until `generate_tailored_resume()` returns.
**How to avoid:** Always use `print("Tailoring resume...", flush=True)` before the LLM call.
**Warning signs:** Inconsistent behavior — message appears on some terminals but not others; appears at end of run rather than before LLM call.

### Pitfall 2: Relative Path in Success Message

**What goes wrong:** Success message shows `resumes/output/tailored_resume_20260529_143022.tex` — the user cannot use it in another terminal or editor without knowing the project root.
**Why it happens:** `write_resume()` returns the `Path` as-constructed, which is absolute because `config.py` uses `Path(__file__).parent.parent`. But relying on this silently breaks if `OUTPUT_DIR` is ever changed to a relative path.
**How to avoid:** Always print `str(output_path.resolve())` — it is correct in all cases.
**Warning signs:** Path starts with a directory name rather than `/`.

### Pitfall 3: EOFError Not Caught in Input Loop

**What goes wrong:** User pipes a job description file (`cat jd.txt | resume-tailor`) or hits Ctrl+D. Python raises `EOFError` from `input()`, which propagates through `main()` uncaught and prints a raw traceback.
**Why it happens:** `input()` raises `EOFError` when stdin is exhausted or closed. D-05 requires it be treated as normal submission.
**How to avoid:** The `while True` loop must catch `EOFError` and `break` — same as typed `END`.
**Warning signs:** `EOFError` in traceback when testing with piped input.

### Pitfall 4: Empty Job Description Submitted

**What goes wrong:** User types `END` immediately without entering any text. `job_description` is an empty string. `generate_tailored_resume()` sends an empty `<job_description>` tag to Ollama, which returns a response (possibly nonsensical). The tool writes a file rather than informing the user.
**Why it happens:** The input loop does not validate that at least one line was collected.
**How to avoid:** After the loop, check `if not job_description.strip()` and print an error to stderr + `sys.exit(1)`.
**Warning signs:** Output file is generated even when no job description was entered.

### Pitfall 5: `read_resume` Error Behavior Misunderstood

**What goes wrong:** Developer wraps `read_resume()` in its own `try/except FileNotFoundError` expecting to catch it in `main()` — but `resume_reader.py` calls `sys.exit(1)` directly. The custom catch never fires, or the developer adds redundant error handling.
**Why it happens:** Inconsistency between Phase 1 design (`sys.exit` directly) and Phase 2 design (raise exceptions to the CLI boundary).
**How to avoid:** Do NOT add a `try/except FileNotFoundError` around `read_resume()` in `main()`. The call to `sys.exit(1)` inside `read_resume()` terminates the process before control returns to `main()`. The `try/except (RuntimeError, ValueError)` block should start at `read_resume()` (for completeness / future-proofing) but know that reader errors are handled inside the module.
**Warning signs:** Dead `except FileNotFoundError` block in `main()` that is never executed.

---

## Code Examples

Verified patterns from official sources:

### Complete `main()` skeleton

```python
# Source: Synthesized from Python 3 docs + CONTEXT.md decisions
import argparse
import sys

from config import BASE_RESUME_PATH, OUTPUT_DIR
from generate_tailored_resume import generate_tailored_resume
from resume_reader import read_resume
from resume_writer import write_resume


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-tailor",
        description="Tailor a LaTeX resume to a job description using a local Ollama LLM.",
    )
    parser.parse_args()

    print("Resume Tailor")
    print("Paste the job description below. Type END on a new line to submit.")
    print()
    print(">")

    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)

    job_description = "\n".join(lines)
    if not job_description.strip():
        print("Error: No job description provided.", file=sys.stderr)
        sys.exit(1)

    print("Tailoring resume — this may take a minute...", flush=True)

    try:
        resume_text = read_resume(BASE_RESUME_PATH)
        content = generate_tailored_resume(resume_text, job_description)
        output_path = write_resume(content, OUTPUT_DIR)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Tailored resume written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
```

Note: The empty job description guard (Pitfall 4) is included as a recommended addition — it is within Claude's discretion per D-02.

### Import paths (flat `src/` layout)

```python
# Source: [VERIFIED: existing codebase — llm_client.py imports config directly]
from config import BASE_RESUME_PATH, OUTPUT_DIR
from resume_reader import read_resume
from llm_client import generate_tailored_resume
from resume_writer import write_resume
```

The `pyproject.toml` uses `sources = ["src"]` with `hatchling`, so all `src/` modules are importable at the top level (no `resume_tailor.` prefix). [VERIFIED: /workspace/pyproject.toml lines 16-19]

### `print()` with `end=""` for the `>` prompt on its own line

The `>` in D-04 appears on its own line. Standard `print(">")` produces `>\n` — the user starts typing on the next line. This is correct behavior and requires no `end=""` manipulation.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `sys.stdin.readline()` loop | `input()` in `while True` | Python 3.0 | `input()` is cleaner, handles EOF via exception, no manual strip of `\n` |
| `os.path.abspath()` | `Path.resolve()` | Python 3.4 (PEP 428) | Returns `Path` object, handles symlinks, chainable |

**Deprecated/outdated:**
- `raw_input()`: Python 2 only. Python 3 `input()` is the equivalent.
- `sys.stdout.write()` for progress messages: `print(..., flush=True)` is idiomatic Python 3.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Single broad `except (RuntimeError, ValueError)` is sufficient — `write_resume()` does not raise in practice | Pattern 4, Pitfall 5 | `write_resume()` could raise `OSError`/`PermissionError` on disk-full or read-only directory; would propagate as uncaught exception with traceback. Low risk for personal-use tool. |
| A2 | Empty job description guard (`if not job_description.strip()`) is an appropriate addition under "Claude's Discretion" | Code Examples | If user disagrees, guard should be removed — it is not required by CORE-02. |

**Note:** All other claims in this research are VERIFIED against the existing codebase, Python 3 docs, or CONTEXT.md.

---

## Open Questions

1. **Should `except Exception` be added as a final fallback?**
   - What we know: D-02 says `except (RuntimeError, ValueError)` is sufficient; fallback is "Claude's call"
   - What's unclear: `write_resume()` could raise `OSError` on disk-full or permission errors — currently uncaught
   - Recommendation: Add `except Exception as e` as a final fallback after `(RuntimeError, ValueError)` to prevent any raw traceback reaching the user. Print error message + `sys.exit(1)`.

2. **Should the `>` prompt use `print(">", end=" ")` or `print(">")`?**
   - What we know: D-04 says "The `>` prompt stays on the same line — user types after it for the first line"
   - What's unclear: "same line" could mean `> ` with a trailing space using `input("> ")`, but D-05 says "while True loop using `input()`" without a prompt argument
   - Recommendation: Use `print(">")` (no `input()` prompt argument) per the D-04 banner specification — the prompt is a visual separator, not an interactive prompt character. The banner is printed by `print()` calls; `input()` collects lines silently.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | Runtime | Verified in pyproject.toml | >=3.13 | — |
| `requests` | `llm_client.py` (Phase 2) | Already installed | >=2.32.0 | — |
| Ollama | `generate_tailored_resume()` | Not checked (runtime dep) | — | Tool fails fast with ERR-03 message |

**Missing dependencies with no fallback:** None for Phase 3 itself. Ollama must be running at runtime but `llm_client.py` already handles its absence with a health check (ERR-03).

**Missing dependencies with fallback:** None.

---

## Validation Architecture

`nyquist_validation` is `false` in `.planning/config.json`. This section is skipped per config.

---

## Security Domain

This phase handles only local stdin input and local file paths. There is no network input at the CLI boundary, no authentication, no session management, and no access control. ASVS categories V2, V3, V4 do not apply.

**V5 Input Validation:** The job description collected from stdin is passed to `generate_tailored_resume()` which wraps it in `<job_description>...</job_description>` XML delimiters (QUAL-04, already implemented). No additional CLI-layer sanitization is needed.

**V6 Cryptography:** Not applicable.

No security actions required in Phase 3.

---

## Sources

### Primary (HIGH confidence)

- Python 3 docs `input()` — https://docs.python.org/3/library/functions.html#input — EOFError behavior, return value (no trailing newline)
- Python 3 docs `print()` — https://docs.python.org/3/library/functions.html#print — `flush` parameter
- Python 3 docs `pathlib.Path.resolve()` — https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve
- `/workspace/src/cli.py` — current stub (argparse parser, `main()` shell)
- `/workspace/src/config.py` — `BASE_RESUME_PATH`, `OUTPUT_DIR`, `OLLAMA_MODEL` constants
- `/workspace/src/resume_reader.py` — `read_resume()` calls `sys.exit(1)` directly
- `/workspace/src/llm_client.py` — raises `RuntimeError` and `ValueError`
- `/workspace/src/resume_writer.py` — `write_resume()` returns `Path`
- `/workspace/pyproject.toml` — flat `src/` layout, import path structure
- `/workspace/.planning/phases/03-cli-wiring/03-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)

- Codebase patterns — `from config import ...`, `from resume_reader import ...` (flat imports, no package prefix) confirmed by reading existing source files

### Tertiary (LOW confidence)

- None — all claims in this research are verified against the codebase or Python docs.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only; no new packages; all verified in Python 3 docs and existing codebase
- Architecture: HIGH — all decisions locked in CONTEXT.md; flow is linear and fully specified
- Pitfalls: HIGH — all pitfalls derived from verified code behavior (e.g., `resume_reader.py` calling `sys.exit(1)`) or well-known Python stdout buffering behavior

**Research date:** 2026-05-29
**Valid until:** 2026-06-28 (30 days — stdlib is stable; no ecosystem churn risk)
