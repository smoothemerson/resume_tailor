# Phase 11: E2E Tests - Research

**Researched:** 2026-06-08
**Domain:** pytest subprocess E2E testing, Python CLI testing patterns
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Invoke CLI as `subprocess.run([sys.executable, CLI_PATH, ...])` where `CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"` — absolute path derived from test file location. Works without install, always uses the same Python interpreter as pytest.
- **D-02:** Pass stdin as `input="END\n"` (or `input="<jd text>\nEND\n"`) with `capture_output=True, text=True` — no bytes encoding overhead needed.
- **D-03:** Define a module-level `MINIMAL_RESUME` string constant in `tests/e2e/test_cli.py` — same pattern as Phase 10's integration test. No import from other test files.
- **D-04:** In TEST-11, write `MINIMAL_RESUME` to a `tmp_path / "resume.tex"` file and pass `--resume` pointing to it. Also pass `--output-dir tmp_path` to redirect output away from `resumes/output/`.
- **D-05:** TEST-10 asserts `returncode == 1` and `"Error: Job description cannot be empty." in result.stderr` — exact string match (string is a stable constant in cli.py).
- **D-06:** TEST-11 asserts: `returncode == 0`, `"Tailored resume written to:" in result.stdout`, and one output `.tex` file exists in `tmp_path` with filename matching `tailored_resume_\d{8}_\d{6}\.tex`. No content assertions.
- **D-07:** TEST-10 does NOT use `require_ollama` — it tests the empty-JD error path before any Ollama call is made. Must run even when Ollama is absent.
- **D-08:** TEST-11 uses the `require_ollama` fixture from `tests/conftest.py` to skip when Ollama is unreachable.
- **D-09:** Every test carries `@pytest.mark.e2e` — required by `pyproject.toml` `--strict-markers` and the `pytest -m e2e` success criterion.

### Claude's Discretion

None specified.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-10 | E2E test: CLI subprocess exits 1 and prints an error to stderr when given empty JD input (END sentinel immediately); does not require Ollama running | Verified: `subprocess.run([sys.executable, CLI_PATH], input="END\n", ...)` returns `returncode=1` and `stderr='Error: Job description cannot be empty.\n'` — confirmed live in this session |
| TEST-11 | E2E test: CLI subprocess exits 0 when given a real JD, creates an output file in a temp directory with filename matching the timestamp pattern, and stdout contains `"Tailored resume written to:"`; test is skipped when Ollama is unreachable | Verified: `--resume` and `--output-dir` CLI flags exist and are parsed correctly; `require_ollama` fixture from `tests/conftest.py` is session-scoped and skips when Ollama is down |
</phase_requirements>

## Summary

Phase 11 writes a single new file — `tests/e2e/test_cli.py` — containing two E2E tests that invoke the CLI as a subprocess. The scope is tightly constrained: all architectural decisions were locked in the discuss phase, all patterns are established by Phases 8-10, and the target directory (`tests/e2e/`) already exists and is empty.

TEST-10 (empty JD error path) is the simpler test: it requires no fixtures, no Ollama, and no temporary files. It runs `subprocess.run` with `input="END\n"` and asserts `returncode == 1` and the exact stderr message `"Error: Job description cannot be empty."`. Live verification confirmed this message is exactly what `cli.py` produces (line 45: `print("Error: Job description cannot be empty.", file=sys.stderr)`).

TEST-11 (golden path) writes `MINIMAL_RESUME` to a `tmp_path` fixture directory, passes `--resume` and `--output-dir` to the subprocess, and skips via `require_ollama` when Ollama is absent. The success criteria are structural — exit code, presence of success message in stdout, and a `.tex` file with the timestamp filename pattern in `tmp_path`. No LaTeX content assertions are needed since those are covered by integration tests.

**Primary recommendation:** Write `tests/e2e/test_cli.py` as a single task following the patterns in `tests/integration/test_llm_client.py`. No infrastructure changes are needed — pytest config, markers, directories, and conftest fixtures are all complete.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI subprocess invocation | Test tier | — | Tests own the subprocess.run call; CLI owns the logic being tested |
| Empty JD validation | CLI (`cli.py`) | — | Validated in `cli.py` before any Ollama call; E2E test observes via exit code + stderr |
| Output file creation | CLI (`resume_writer.py`) | — | E2E test only observes result in `tmp_path`; does not call `write_resume` directly |
| Ollama skip gate | `tests/conftest.py` | TEST-11 | Session-scoped `require_ollama` fixture already implemented in Phase 8 |
| Marker enforcement | `pyproject.toml` | `@pytest.mark.e2e` | `--strict-markers` in `addopts` enforces that all declared markers exist |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pytest` | 9.0.3 | Test runner | Already installed; configured in `pyproject.toml` [VERIFIED: uv run pytest --version] |
| `subprocess` | stdlib | Invoke CLI as child process | The correct Python idiom for black-box CLI testing; no external dependency [ASSUMED] |
| `sys` | stdlib | `sys.executable` for subprocess invocation | Ensures subprocess uses the same Python/venv as the test runner [ASSUMED] |
| `re` | stdlib | Filename pattern assertion | `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", name)` — same pattern as Phase 9 writer tests [ASSUMED] |
| `pathlib.Path` | stdlib | `CLI_PATH`, `tmp_path` manipulation, glob for output file | Project-wide standard; `Path(__file__).parents[2]` is the path derivation idiom [ASSUMED] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest.tmp_path` | built-in fixture | Isolated temp directory per test | Used in TEST-11 to write `resume.tex` and receive `--output-dir` output |
| `require_ollama` | `tests/conftest.py` | Skip TEST-11 when Ollama unreachable | Function argument to TEST-11; already implemented in Phase 8 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `subprocess.run` | `subprocess.Popen` | `Popen` is more complex, needed only for streaming I/O; `run` is correct for synchronous CLI testing |
| `sys.executable` | hardcoded `python3` | Hardcoded path breaks in venv environments; `sys.executable` always matches the active interpreter |
| `re.match` | `fnmatch` or glob | Regex is more precise; `re.match` with `\d{8}_\d{6}` validates timestamp format, not just prefix |

**Installation:** No new packages required. All dependencies are stdlib or already installed.

## Package Legitimacy Audit

No new packages are installed in this phase. All dependencies are Python stdlib or packages already installed from prior phases (`pytest`). This section is not applicable.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Test Process (pytest)
        |
        | subprocess.run([sys.executable, CLI_PATH, ...], input=..., capture_output=True)
        v
  ┌─────────────────────────────────────────────────────┐
  │  Child Process: src/cli.py                          │
  │                                                     │
  │  stdin: "END\n"  ─────► empty JD check ─► exit(1)  │  TEST-10 path
  │  stdin: "<jd>\nEND\n" ─► Ollama calls ─► exit(0)   │  TEST-11 path
  │                              │                      │
  │                              ▼                      │
  │                     write_resume(tmp_path)          │
  │                              │                      │
  │  stdout: "Tailored resume written to: <path>"       │
  └─────────────────────────────────────────────────────┘
        |
        | result.returncode, result.stdout, result.stderr
        v
  Test Assertions
  ├── TEST-10: returncode==1, "Error: Job description cannot be empty." in stderr
  └── TEST-11: returncode==0, "Tailored resume written to:" in stdout, 
               1 file matching tailored_resume_\d{8}_\d{6}\.tex in tmp_path
```

### Recommended Project Structure

```
tests/
├── conftest.py              # require_ollama fixture (already exists)
├── e2e/
│   └── test_cli.py          # NEW: TEST-10 and TEST-11
├── integration/
│   └── test_llm_client.py   # existing
└── unit/
    └── *.py                 # existing
```

### Pattern 1: Module-Level Constants

**What:** Define `CLI_PATH` and `MINIMAL_RESUME` as module-level constants at the top of `test_cli.py`, before any test functions.

**When to use:** Always — avoids recomputing path in every test, makes test file self-contained without imports from other test files.

```python
# Source: CONTEXT.md D-01, D-03 (project-specific pattern)
import re
import subprocess
import sys
from pathlib import Path

import pytest

CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)
```

### Pattern 2: subprocess.run for CLI E2E Testing

**What:** Invoke the CLI as a child process; use `input=` for stdin, `capture_output=True, text=True` for clean stdout/stderr capture.

**When to use:** Any test that verifies observable CLI behavior (exit codes, output text, file creation) rather than internal function behavior.

```python
# Source: CONTEXT.md D-01, D-02 (verified live in this research session)
result = subprocess.run(
    [sys.executable, CLI_PATH],
    input="END\n",
    capture_output=True,
    text=True,
)
assert result.returncode == 1
assert "Error: Job description cannot be empty." in result.stderr
```

Key properties:
- `sys.executable` — resolves to `/workspace/.venv/bin/python3` under `uv run pytest`, which has `/workspace/src` on `sys.path` via the editable install `.pth` file
- `capture_output=True` — equivalent to `stdout=subprocess.PIPE, stderr=subprocess.PIPE`
- `text=True` — returns str (not bytes); no need for `.decode()`
- No `cwd=` needed — `/workspace/src` is already on `sys.path` via the venv `.pth` file

### Pattern 3: require_ollama Skip Fixture

**What:** Declare `require_ollama` as a function parameter to auto-skip a test when Ollama is unreachable. The fixture in `tests/conftest.py` is session-scoped and calls `pytest.skip()` automatically.

**When to use:** TEST-11 only. TEST-10 must NOT use it — the empty-JD error path exits before any Ollama call.

```python
# Source: tests/conftest.py (existing, Phase 8)
@pytest.mark.e2e
def test_golden_path(require_ollama, tmp_path):
    # require_ollama as positional arg triggers skip when Ollama is down
    # tmp_path is a pytest built-in fixture, isolated per-test
    ...
```

### Pattern 4: Output File Assertion via glob + re.match

**What:** Use `list(tmp_path.glob("tailored_resume_*.tex"))` to find output files, then `re.match` to validate the filename format.

**When to use:** TEST-11 — verifies file was created with the expected timestamp filename pattern without hardcoding a specific timestamp.

```python
# Source: Pattern established in Phase 9 test_resume_writer.py
output_files = list(tmp_path.glob("tailored_resume_*.tex"))
assert len(output_files) == 1
assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)
```

### Anti-Patterns to Avoid

- **Using `require_ollama` in TEST-10:** TEST-10 is the error-path test that must run without Ollama. Adding `require_ollama` would cause it to be skipped when Ollama is absent — the opposite of the requirement.
- **Importing from other test files:** `MINIMAL_RESUME` must be defined locally in `test_cli.py`, not imported from `tests/integration/test_llm_client.py`. Cross-test-file imports create implicit coupling and are not idiomatic pytest.
- **Using `cwd` in subprocess.run:** Not needed because `/workspace/src` is on `sys.path` via the venv editable install `.pth` file. Adding `cwd='/workspace'` would work but is unnecessary.
- **Content assertions in TEST-11:** LaTeX content correctness is covered by integration tests in Phase 10. TEST-11 should only assert structural properties: exit code, stdout message, file existence, filename pattern.
- **Forgetting `@pytest.mark.e2e` on both tests:** `--strict-markers` is active in `pyproject.toml`. Any test in `tests/e2e/` without a recognized marker will cause a pytest error.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ollama availability detection | Custom HTTP probe in test file | `require_ollama` fixture from `tests/conftest.py` | Already implemented, session-scoped (probes once), consistent across all test layers |
| Temp directory cleanup | `tempfile.mkdtemp()` + manual shutil.rmtree | `pytest.tmp_path` built-in fixture | Auto-cleanup after each test, isolated per-test, no manual teardown needed |
| Process execution | `os.system()` or `Popen` | `subprocess.run(capture_output=True, text=True)` | `run` is the correct modern API; `os.system` provides no stdout/stderr capture |

**Key insight:** All infrastructure for this phase was built in Phases 8-10. The only new artifact is `test_cli.py`.

## Common Pitfalls

### Pitfall 1: TEST-10 accidentally uses require_ollama

**What goes wrong:** If `require_ollama` is added to TEST-10 as a fixture argument (or via a class-level fixture), the test is skipped when Ollama is absent — defeating its purpose as an always-runnable error-path test.

**Why it happens:** Symmetry instinct — both tests live in the same file, both are E2E tests, so it feels natural to give both the same fixtures.

**How to avoid:** Only TEST-11 gets `require_ollama`. TEST-10 function signature is `def test_empty_jd_exits_1()` with no fixture arguments (other than none).

**Warning signs:** `pytest -m e2e` with Ollama stopped shows both tests skipped instead of just TEST-11.

### Pitfall 2: CLI_PATH derivation broken by wrong parent index

**What goes wrong:** `Path(__file__).parents[1]` (instead of `parents[2]`) gives `tests/e2e`, not the repo root — making the derived `cli.py` path point to `tests/e2e/src/cli.py` which doesn't exist.

**Why it happens:** Off-by-one in parent counting: `parents[0]` = `tests/e2e`, `parents[1]` = `tests`, `parents[2]` = repo root.

**How to avoid:** Use `parents[2]` exactly as specified in D-01. Verified: `Path('/workspace/tests/e2e/test_cli.py').parents[2] / 'src' / 'cli.py'` resolves to `/workspace/src/cli.py` which exists.

**Warning signs:** `FileNotFoundError` or `ModuleNotFoundError` when running tests.

### Pitfall 3: Asserting against tmp_path but also writing to resumes/output/

**What goes wrong:** If `--output-dir` is omitted from the subprocess call, `cli.py` uses `OUTPUT_DIR` from `config.py` which resolves to `/workspace/resumes/output/`. The test asserts on `tmp_path` and finds no files.

**Why it happens:** Omitting `--output-dir` from the subprocess flags.

**How to avoid:** Always pass `--output-dir`, `str(tmp_path)` in TEST-11. Verified: `argparse` correctly routes `--output-dir` to `args.output_dir` in `cli.py`.

**Warning signs:** `assert len(output_files) == 1` fails with `0 items`; files appear in `resumes/output/` instead.

### Pitfall 4: Missing `@pytest.mark.e2e` triggers strict-markers error

**What goes wrong:** Unmarked test in `tests/e2e/` causes `PytestUnknownMarkWarning` to be treated as an error due to `--strict-markers` in `addopts`.

**Why it happens:** Forgetting the decorator, especially if refactoring test function signatures.

**How to avoid:** Both test functions get `@pytest.mark.e2e` — no exceptions.

**Warning signs:** `ERRORS` section in pytest output before any tests run; message: `'e2e' is not a registered marker` (if a typo) or `Unknown pytest.mark...` with strict markers.

## Code Examples

Verified patterns from confirmed sources:

### TEST-10: Empty JD Error Path

```python
# Source: Verified live — subprocess.run with input="END\n" against /workspace/src/cli.py
@pytest.mark.e2e
def test_empty_jd_exits_1_with_stderr_message():
    result = subprocess.run(
        [sys.executable, CLI_PATH],
        input="END\n",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Error: Job description cannot be empty." in result.stderr
```

### TEST-11: Golden Path (Ollama-dependent)

```python
# Source: CONTEXT.md D-04, D-06, D-08 (project decisions)
@pytest.mark.e2e
def test_golden_path_exits_0_creates_output_file(require_ollama, tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text(MINIMAL_RESUME, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, CLI_PATH,
         "--resume", str(resume_file),
         "--output-dir", str(tmp_path)],
        input="Python backend engineer with REST API experience\nEND\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Tailored resume written to:" in result.stdout
    output_files = list(tmp_path.glob("tailored_resume_*.tex"))
    assert len(output_files) == 1
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)
```

### Full Module Structure

```python
# Source: CONTEXT.md (module structure from D-01, D-03, D-09)
import re
import subprocess
import sys
from pathlib import Path

import pytest

CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)


@pytest.mark.e2e
def test_empty_jd_exits_1_with_stderr_message():
    ...


@pytest.mark.e2e
def test_golden_path_exits_0_creates_output_file(require_ollama, tmp_path):
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `sys.path.insert` hacks in test files | `pythonpath = ["src"]` in `pyproject.toml` | Phase 8 | No manual path manipulation in test files |
| `subprocess.PIPE` with `Popen` | `subprocess.run(capture_output=True)` | Python 3.7+ | Single-call API; `capture_output=True` replaces `stdout=PIPE, stderr=PIPE` |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `subprocess.run` with `input="END\n"` and `capture_output=True, text=True` is the correct pattern for synchronous CLI testing | Standard Stack | Low — verified empirically in this session; subprocess docs confirm |
| A2 | `re` stdlib is the right tool for filename pattern assertion | Standard Stack | Negligible — same pattern used in Phase 9 test_resume_writer.py |
| A3 | `pathlib.Path` `.glob()` is reliable for finding single output file in tmp_path | Code Examples | Negligible — verified empirically |

**All critical claims were verified live in this session against the actual codebase.** The only ASSUMED items are general Python stdlib claims (not package-level risks).

## Open Questions

None — the phase scope is fully specified by the CONTEXT.md decisions and verified against the actual codebase state.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | Test runner | ✓ | 9.0.3 | — |
| Python (venv) | subprocess invocation | ✓ | 3.14.5 at `/workspace/.venv/bin/python3` | — |
| `tests/e2e/` directory | Test file location | ✓ | exists, empty | — |
| `tests/conftest.py` `require_ollama` fixture | TEST-11 skip gate | ✓ | implemented in Phase 8 | — |
| Ollama | TEST-11 execution | ✗ | not running | TEST-11 skips via `require_ollama`; TEST-10 still passes |

**Missing dependencies with no fallback:** None — all blocking dependencies are present.

**Missing dependencies with fallback:** Ollama is absent but TEST-11 skips gracefully. `pytest -m e2e` with Ollama stopped skips TEST-11 and passes TEST-10, satisfying success criterion 3.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/e2e/test_cli.py -m e2e -v` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-10 | Empty JD subprocess exits 1, stderr contains error message, no Ollama needed | e2e | `uv run pytest tests/e2e/test_cli.py::test_empty_jd_exits_1_with_stderr_message -v` | ❌ Wave 0 |
| TEST-11 | Golden-path subprocess exits 0, stdout contains success message, `.tex` file created in `tmp_path` | e2e | `uv run pytest tests/e2e/test_cli.py::test_golden_path_exits_0_creates_output_file -v` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/e2e/test_cli.py -m e2e -v`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/e2e/test_cli.py` — covers TEST-10 and TEST-11

*(No other gaps — pytest infrastructure, markers, conftest, and the e2e directory are all in place from prior phases.)*

## Security Domain

This phase writes test-only code. No production code is modified, no authentication/authorization/session/crypto logic is introduced. ASVS categories V2-V6 do not apply. The subprocess invocation pattern does not introduce injection risks — `CLI_PATH` is a `Path` object derived from `__file__` (not user input), and subprocess arguments are literal strings.

## Sources

### Primary (HIGH confidence)

- Live codebase verification — `src/cli.py` line 44-46 (exact empty-JD error message), line 59 (exact success stdout message), lines 21-22 (--resume and --output-dir flags)
- Live subprocess verification — `subprocess.run([sys.executable, str(CLI_PATH)], input="END\n", ...)` confirmed `returncode=1` and `stderr='Error: Job description cannot be empty.\n'`
- `tests/conftest.py` — confirmed `require_ollama` fixture is session-scoped and calls `pytest.skip()` when Ollama is unreachable
- `pyproject.toml` — confirmed `--strict-markers`, `-ra`, `--import-mode=importlib` in addopts; `e2e` marker registered
- `tests/unit/test_resume_writer.py` — established `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", ...)` pattern (Phase 9)
- `tests/integration/test_llm_client.py` — established `MINIMAL_RESUME` local constant pattern (Phase 10)
- Editable install `.pth` file at `/workspace/.venv/lib/python3.14/site-packages/_editable_impl_resume_tailor.pth` — adds `/workspace/src` to `sys.path` so subprocess can import CLI's dependencies

### Secondary (MEDIUM confidence)

- `subprocess.run` Python docs [ASSUMED] — `capture_output=True, text=True` is the canonical pattern for CLI subprocess testing
- pytest `tmp_path` fixture [ASSUMED] — built-in, isolated per-test, auto-cleanup

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all packages are stdlib or already installed; verified in this session
- Architecture: HIGH — one new file, zero infrastructure changes needed; all patterns verified against existing codebase
- Pitfalls: HIGH — derived from direct code inspection and live subprocess verification

**Research date:** 2026-06-08
**Valid until:** Stable indefinitely for this phase (no moving targets; all decisions locked and verified against actual code)
