# Test Pitfalls — Resume Tailor CLI v1.2

**Domain:** Adding integration and e2e tests to an existing Python CLI that wraps a local LLM API
**Researched:** 2026-06-02
**Confidence:** HIGH for pytest infrastructure and subprocess patterns (grounded in official pytest docs and codebase inspection); HIGH for LLM test anti-patterns (grounded in published research and project-specific constraints); MEDIUM for import resolution (multiple valid approaches exist, project-specific layout determines best path)

---

## Scope

This document covers pitfalls specific to **v1.2 test coverage** — the act of adding integration and e2e tests to an already-working CLI. It does not repeat v1.0 pitfalls (fence stripping, timeout handling, encoding) or v1.1 pitfalls (diff noise, keyword scoring). It focuses on test infrastructure mistakes.

**Codebase state entering v1.2:**
- 18 unit tests in `src/llm_client_test.py` and `src/cli_test.py`
- Tests co-located in `src/` alongside source modules
- `sys.path.insert(0, str(Path(__file__).parent))` in each test file
- `pytest>=9.0.3` as dev dependency, no `[tool.pytest.ini_options]` section in `pyproject.toml`
- No `conftest.py`, no registered markers, no `tests/` directory yet
- `config.py` uses `Path(__file__).parent.parent` to anchor paths to the repo root

---

## Non-determinism Pitfalls

### Pitfall 1: Asserting Exact LLM Output Content in Integration Tests

**What goes wrong:**
An integration test calls `generate_tailored_resume()` against real Ollama and asserts that specific phrases appear in the output — for example, `assert "Python" in result` or `assert "summary" in result.lower()`. The test passes on the day it is written. Two weeks later, after a model update or a different system load pattern, the phrasing changes and the test fails. No code changed; the model changed.

Even with `temperature=0`, local models are not bit-reproducible across restarts, hardware states, or version bumps. Research confirms that even so-called "deterministic" LLM settings produce different outputs across runs for non-trivial reasons (quantization, batching, kernel scheduling). See: "Non-Determinism of 'Deterministic' LLM Settings" (arxiv 2408.04667).

**Why it happens:**
Developers reach for content assertions because they seem to verify that the model "did the right thing." For a resume tailor, "did the right thing" is the wrong question for a test to answer.

**Prevention:**
Assert structure, not content. The existing `_validate_latex()` function already defines the contract: the output must start with `\documentclass` and contain `\end{document}`. Integration tests should assert exactly these structural invariants — nothing more.

Correct assertion set for an integration test against real Ollama:
- `result.lstrip().startswith("\\documentclass")` — the output is LaTeX, not prose
- `"\\end{document}" in result` — the output is not truncated
- `len(result) > len(resume_text) * 0.5` — the output is not pathologically short (a guard against silent truncation, not a content assertion)
- The call did not raise `RuntimeError` or `ValueError` (i.e., none of the guards in `_validate_latex` or `_strip_fences` tripped)

Do not assert: specific section names, specific keywords from the JD, specific rewritten phrases, number of bullet points, or any sentence-level content.

**Phase to address:** Any phase writing integration tests. Define the assertion set in a shared fixture or helper — do not let individual test authors invent their own assertions.

---

### Pitfall 2: Relying on `done_reason=stop` as a Correctness Signal

**What goes wrong:**
An integration test checks `data["done_reason"] == "stop"` to confirm the model finished "normally." This passes even when the model returns well-formed LaTeX that is semantically nonsensical, incomplete, or has silently changed phrasing in ways that break the resume. `done_reason=stop` only means the model hit a natural end-of-sequence token — it is a generation boundary signal, not a quality signal.

**Prevention:**
Leave `done_reason` handling in `llm_client.py` where it already is (raising on `length`). Do not add extra assertions on `done_reason` in integration tests — it adds false confidence without real coverage.

**Phase to address:** Integration test phase. Note in the test's docstring (or a comment if the no-docstring rule is relaxed for tests) why structural assertions are sufficient.

---

### Pitfall 3: Using a Large Model for Integration Tests (Timeout Flakiness)

**What goes wrong:**
Integration tests call `generate_tailored_resume()` with the default model (`qwen3:14b`). On a cold system, the model needs to load from disk. On a warm system it runs in under 30 seconds. On a cold system it can take 2-3 minutes. Tests that pass locally on a warm system fail in CI after a machine reboot or in a fresh container. The tests look flaky but the real cause is cold-load latency.

**Prevention:**
Integration tests should use a small, fast model explicitly — `qwen3:1.7b` or `phi3:mini` rather than the production model. The `generate_tailored_resume()` function already accepts a `model` parameter. Pass a small model name as a pytest fixture or constant in `conftest.py`. The structural assertions do not depend on model quality — only on output format — so a fast small model is correct for integration tests.

Add an explicit timeout check: if the integration test takes over 120 seconds, something is wrong. The default `TIMEOUT = (10, 300)` in `config.py` allows up to 5 minutes of read timeout, which is correct for production but masks integration test hangs. Integration test fixtures should call with a shorter timeout override or simply document the expected wall-clock range.

**Phase to address:** Integration test phase setup.

---

## Subprocess / E2E Pitfalls

### Pitfall 4: Using `capsys` Instead of `capfd` for Subprocess Output Capture

**What goes wrong:**
E2E tests invoke the CLI via `subprocess.run(["resume-tailor", ...])` and attempt to capture its output using pytest's `capsys` fixture. `capsys` intercepts writes to Python's `sys.stdout` and `sys.stderr` objects only — it has no effect on output from a subprocess that has its own file descriptors. The captured output is empty even when the CLI printed to stdout.

This is confirmed in the official pytest documentation: "If you want to capture at the file descriptor level you can use the `capfd` fixture... [it] allows to also capture output from libraries or subprocesses that directly write to operating system level output streams."

**Prevention:**
E2E tests that invoke the CLI via `subprocess.run()` should use `subprocess.run(..., capture_output=True, text=True)` to capture stdout and stderr directly in the `CompletedProcess` return value, and read them from `result.stdout` and `result.stderr`. Do not use `capsys` or `capfd` for this. The `capture_output=True` shorthand sets `stdout=PIPE, stderr=PIPE` and is the correct pattern for subprocess-level capture.

**Phase to address:** E2E test phase.

---

### Pitfall 5: Passing stdin as a String Without Encoding Alignment

**What goes wrong:**
The CLI's input loop reads from `input()`, which in turn reads from `sys.stdin`. When the test invokes the CLI via `subprocess.run(["resume-tailor", ...], input="job description\nEND\n")`, it passes a Python `str`. If `subprocess.run` is called without `text=True`, the `input=` argument must be `bytes`. Passing a `str` without `text=True` raises `TypeError`. Passing `bytes` with `text=True` also raises `TypeError`.

A subtler problem: the test passes `"job description\nEND\n"` as stdin but the CLI reads `input()` in a loop, looking for a line `"END"` exactly. If the test sends `"END\n"` the `line.strip() == "END"` check succeeds. If the test accidentally sends `" END"` (leading space from a multiline string) or `"END "` (trailing space), the CLI waits forever for stdin to close or for the sentinel, and the subprocess hangs until the test timeout.

**Prevention:**
- Always call `subprocess.run(..., text=True, input="...\nEND\n")` for the CLI's stdin.
- Write the stdin string as a named variable in the test, not inline, so its exact content is visible.
- Include a `timeout=` argument on every `subprocess.run` in test code: `subprocess.run(..., timeout=30)`. This converts a hang into a `subprocess.TimeoutExpired` exception rather than a test suite stall.
- The sentinel must be exactly `"END"` on its own line with no leading or trailing whitespace.

Example of the correct pattern:
```python
stdin_input = "Senior ML Engineer role\nEND\n"
result = subprocess.run(
    ["resume-tailor", "--model", INTEGRATION_MODEL],
    input=stdin_input,
    capture_output=True,
    text=True,
    timeout=120,
)
assert result.returncode == 0
```

**Phase to address:** E2E test phase, first test written.

---

### Pitfall 6: Not Checking `returncode` and Ignoring `stderr` on Failure

**What goes wrong:**
E2E tests assert that a file was written to the output directory without first checking `result.returncode`. If the CLI failed (exit 1) but the assertion only looks for the file, the test passes vacuously if a file from a previous run happens to be present. Conversely, a test that checks `assert result.returncode == 0` fails with a confusing message ("assert 1 == 0") that hides the actual error written to stderr.

**Prevention:**
Always check both `returncode` and `stderr` in the same assertion block. On failure, include `result.stderr` in the assertion message:

```python
assert result.returncode == 0, f"CLI exited {result.returncode}: {result.stderr}"
```

For error-path tests (testing that the CLI fails correctly), assert the expected error message in `result.stderr`:
```python
assert result.returncode == 1
assert "Job description cannot be empty" in result.stderr
```

Do not assert output file existence without first confirming `returncode == 0`.

**Phase to address:** E2E test phase.

---

### Pitfall 7: E2E Tests Write Real Files to the Production Output Directory

**What goes wrong:**
The CLI writes output to `config.OUTPUT_DIR`, which is `resumes/output/` relative to the repo root. E2E tests that run the CLI subprocess without redirecting the output directory will write real `.tex` files into `resumes/output/` on every test run. After 10 test runs there are 10 timestamped files in the repo that are test artifacts, not real tailored resumes. `git status` becomes noisy; the files may be accidentally committed; and the test cannot assert on the exact filename because it includes a timestamp.

**Prevention:**
Always pass `--output-dir` to the CLI in every E2E test, pointing to a `tmp_path` directory:

```python
def test_golden_path(tmp_path):
    result = subprocess.run(
        ["resume-tailor", "--model", INTEGRATION_MODEL, "--output-dir", str(tmp_path)],
        input="Senior ML Engineer\nEND\n",
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    output_files = list(tmp_path.glob("tailored_resume_*.tex"))
    assert len(output_files) == 1
```

`tmp_path` is a pytest built-in fixture that provides a unique per-test temporary directory and is cleaned up automatically after the test session (keeping the last 3 runs by default).

Also add `resumes/output/tailored_resume_*.tex` to `.gitignore` as a defensive measure, but this does not replace the `--output-dir tmp_path` pattern in tests.

**Phase to address:** E2E test phase, before any test writes a file.

---

### Pitfall 8: Invoking the CLI via `sys.argv` Patch in E2E Tests

**What goes wrong:**
A developer writes an "E2E" test that calls `main()` directly via `with patch("sys.argv", [...])` rather than via `subprocess.run`. This is not an E2E test — it is an in-process function call test. It cannot catch import errors, entry point misconfiguration, or environment issues that only surface when the process boundary is crossed. The existing `cli_test.py` tests already use this pattern correctly for unit tests. Writing a new test that does the same thing and calling it an "E2E test" adds no coverage.

**Prevention:**
E2E tests must invoke the CLI via `subprocess.run(["resume-tailor", ...])` using the installed entry point. This verifies the packaging, the `[project.scripts]` entry in `pyproject.toml`, and the actual CLI path resolution. If `uv tool install .` hasn't been run in the test environment, use `subprocess.run(["python", "-m", "src.cli", ...])` or `subprocess.run(["python", "src/cli.py", ...])` as a fallback, but document which mode is being used.

The distinction between test layers for this project:
- Unit tests: patch `sys.argv`, call `main()` directly, mock all I/O
- Integration tests: call `generate_tailored_resume()` directly with real Ollama, no subprocess
- E2E tests: `subprocess.run(["resume-tailor", ...])` with real Ollama

**Phase to address:** Test infrastructure planning phase — define the layer boundaries before writing tests.

---

## External Service Dependency Pitfalls

### Pitfall 9: Tests Fail in CI Without a Useful Error (Ollama Not Running)

**What goes wrong:**
Integration and e2e tests that require Ollama fail in CI environments where Ollama is not installed or not running. The failure message is a `requests.ConnectionError` deep in a traceback, not a skip or a clear "Ollama not available" message. The test run shows 12 errors with no obvious explanation for a developer reading the CI log who doesn't know Ollama is a dependency.

An equally bad failure mode: the test is not skipped but hangs for 300 seconds (the read timeout from `config.py`) waiting for a connection that never comes, blocking the entire test suite.

**Prevention:**
Define a pytest fixture in `conftest.py` that checks Ollama availability and skips the test if it is unreachable:

```python
import pytest
import requests

def _ollama_is_running() -> bool:
    try:
        requests.get("http://localhost:11434/api/tags", timeout=3)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False

@pytest.fixture(autouse=False)
def require_ollama():
    if not _ollama_is_running():
        pytest.skip("Ollama not running at localhost:11434")
```

Apply this fixture to all integration and e2e tests. Use a 3-second connect timeout — not the 10-second production timeout — so the skip decision is fast.

Also register the `integration` and `e2e` markers so that the test suite can be run with `pytest -m "not integration and not e2e"` in environments where Ollama is unavailable. See the pytest marker pitfall below.

**Phase to address:** Test infrastructure phase (conftest.py), before any integration test is written.

---

### Pitfall 10: Test Ordering Exposes a Race Between Health Check and Generation

**What goes wrong:**
The integration test for `_check_ollama_health()` runs, succeeds, and confirms Ollama is reachable. Then the test for `generate_tailored_resume()` runs, but between the two tests Ollama is briefly unavailable (e.g., model reloading). The `generate_tailored_resume()` test fails not because the function is wrong but because of test ordering and timing.

This is unlikely in practice (Ollama on a local machine is stable), but it surfaces in edge cases: the health check test may call `/api/tags` which triggers a model listing, and immediately after, the generation call may load a large model that takes 15 seconds. If the health check test ran on a different Ollama instance state than the generation test, results diverge.

**Prevention:**
Do not test `_check_ollama_health()` and `generate_tailored_resume()` as if they are independent. `generate_tailored_resume()` already calls the health check internally. An integration test for `generate_tailored_resume()` implicitly tests the health check path. A separate integration test for `_check_ollama_health()` in isolation is redundant and adds ordering sensitivity. Reserve the isolated `_check_ollama_health()` test for unit tests (where it is already present, mocked).

If an integration test for `_check_ollama_health()` in isolation is desired (e.g., to confirm it returns without raising when Ollama is running), mark it with `@pytest.mark.integration` and make it idempotent — it should not depend on results from any other test.

**Phase to address:** Integration test phase — explicitly decide which functions get standalone integration tests vs. being covered transitively.

---

### Pitfall 11: Integration Tests Leave Model State That Affects Subsequent Tests

**What goes wrong:**
An integration test sends a very large resume (or a very long job description) to Ollama and triggers `done_reason=length`. The model is now in a state where it may be partially loaded or the context window is exhausted. The next integration test, which expects a clean context, gets degraded output or a model timeout.

**Prevention:**
Integration tests should use a small, fixed job description and a small, fixed resume (not the real `english.tex` which is ~150 lines of LaTeX). Create a minimal fixture resume:

```tex
\documentclass{article}
\begin{document}
\section{Summary}
Software engineer.
\section{Skills}
Python
\end{document}
```

This ensures the prompt is well within the 8192 `num_ctx` window, finishes fast, and does not pollute Ollama's context state for subsequent tests.

**Phase to address:** Integration test phase — define the test resume fixture before writing any integration test.

---

## pytest Infrastructure Pitfalls

### Pitfall 12: PytestUnknownMarkWarning Cascades Into CI Noise or Strict-Mark Failures

**What goes wrong:**
A developer adds `@pytest.mark.integration` or `@pytest.mark.e2e` to tests without registering those markers. pytest emits `PytestUnknownMarkWarning` for every unregistered mark. In a project with `--strict-markers` configured (or when a future CI step adds it), unregistered marks become errors and break the entire test run.

The warning itself, even without `--strict-markers`, is a signal that the marker is silently doing nothing if it appears in a `pytest -m integration` invocation — pytest cannot filter on an unregistered marker reliably.

**Prevention:**
Register all custom markers in `pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests that require a running Ollama instance (deselect with '-m not integration')",
    "e2e: marks tests that run the full CLI subprocess with real Ollama",
]
```

This is the canonical location given the project already uses `pyproject.toml`. Do not also add a `pytest.ini` or `setup.cfg` — having both causes confusing precedence behavior.

Add `--strict-markers` to `addopts` now, not later:
```toml
addopts = ["--strict-markers"]
```

This converts future unregistered markers into errors immediately rather than silent warnings that are found only after markers are needed for filtering.

**Phase to address:** Test infrastructure phase — first thing added to `pyproject.toml` before any marker is applied.

---

### Pitfall 13: conftest.py Placed in the Wrong Directory

**What goes wrong:**
A developer creates `src/conftest.py` and adds fixtures and marker registration there. pytest picks it up for tests in `src/` but not for tests in a future `tests/` directory. When integration tests are placed in `tests/`, the `require_ollama` fixture is not found, resulting in a `fixture 'require_ollama' not found` error that looks like a pytest bug.

Alternatively, a developer creates `conftest.py` at the repo root but the project's `testpaths` points to `src/`, and pytest does not traverse up to find the root conftest during collection.

**Prevention:**
Place the root `conftest.py` at the project root (`/workspace/conftest.py`). pytest always loads conftest files by walking from the rootdir upward, so a root conftest is visible to all tests regardless of where they are collected from.

For this project's structure, the correct conftest locations are:
- `/workspace/conftest.py` — shared fixtures (`require_ollama`, test constants like `INTEGRATION_MODEL`)
- `/workspace/tests/conftest.py` (if a `tests/` directory exists) — fixtures scoped to that directory only

Do not place marker registration in both root and subdirectory conftest files — it creates duplicate registration warnings.

**Phase to address:** Test infrastructure phase — establish conftest.py location before writing any fixture.

---

### Pitfall 14: Import Errors When Moving Tests Out of `src/`

**What goes wrong:**
The current test files live in `src/` and use `sys.path.insert(0, str(Path(__file__).parent))` to import `llm_client`, `cli`, etc. If tests are moved to a `tests/` directory, this path insert points to `tests/`, not `src/`, and all imports fail with `ModuleNotFoundError`.

A developer who moves `llm_client_test.py` to `tests/` and updates the path insert to `str(Path(__file__).parent.parent / "src")` will make it work, but this creates a fragile per-file path configuration. If the project is later installed with `uv tool install .`, the src path insert may conflict with the installed package.

The existing `sys.path.insert(0, ...)` in each test file is a workaround for the absence of proper pytest path configuration. It should not be propagated to new test files.

**Prevention:**
Add `pythonpath` to `[tool.pytest.ini_options]` in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["src", "tests"]
```

With `pythonpath = ["src"]`, pytest adds `src/` to `sys.path` before collecting tests, making `import llm_client`, `import cli`, `import config` work from any test file in any directory without manual `sys.path` manipulation.

After adding this, remove the `sys.path.insert(0, ...)` lines from existing test files — they are no longer needed and can cause double-import confusion.

**Phase to address:** Test infrastructure phase — add `pythonpath` to pyproject.toml before any new test file is created.

---

### Pitfall 15: Marker Inheritance — `@pytest.mark.integration` on a Class Does Not Propagate Automatically Without `pytestmark`

**What goes wrong:**
A developer organizes integration tests in a class:

```python
class TestIntegration:
    @pytest.mark.integration
    def test_health_check(self): ...

    def test_generate(self): ...  # MISSING marker
```

`test_generate` is not marked and runs even when invoking `pytest -m "not integration"`. The developer assumed that marking the class or some tests in it would mark all methods — this is not how pytest works. Method-level markers do not inherit upward or downward.

The correct class-level marking uses `pytestmark`:

```python
class TestIntegration:
    pytestmark = pytest.mark.integration
```

or the decorator on the class itself:

```python
@pytest.mark.integration
class TestIntegration:
    ...
```

Both class-level forms propagate the marker to all methods in the class. Method-level marking does not.

**Prevention:**
Use class-level `pytestmark` or decorate the class, not individual methods, when all tests in a class share the same marker. Document this convention in the project's test README or a comment in conftest.py.

**Phase to address:** Integration and e2e test phase — apply consistent marker placement from the first test class.

---

## File System / Isolation Pitfalls

### Pitfall 16: Unit Tests for `write_resume()` That Write to Real Paths

**What goes wrong:**
`write_resume()` calls `output_dir.mkdir(parents=True, exist_ok=True)` and then writes a file. A unit test that calls `write_resume("\\documentclass{article}\n\\end{document}", Path("/tmp/resume_test"))` or — worse — `write_resume(..., config.OUTPUT_DIR)` writes a real file to the filesystem. This test is not isolated.

After 50 test runs, `/tmp/resume_test/` contains 50 timestamped files. The test cannot assert on the exact output path because the timestamp is generated at call time. The test is also non-deterministic about the filename, making assertions fragile.

**Prevention:**
Use `tmp_path` for all tests that call `write_resume()`:

```python
def test_write_resume_creates_timestamped_file(tmp_path):
    path = write_resume("\\documentclass{article}\n\\end{document}", tmp_path)
    assert path.parent == tmp_path
    assert path.name.startswith("tailored_resume_")
    assert path.suffix == ".tex"
    assert path.read_text() == "\\documentclass{article}\n\\end{document}"
```

The test asserts the filename pattern and the file content without depending on the specific timestamp. `tmp_path` is isolated per test and cleaned up automatically.

**Phase to address:** Unit test phase for `resume_writer.py`.

---

### Pitfall 17: Unit Tests for `read_resume()` That Use Real Files or Relative Paths

**What goes wrong:**
A test for `read_resume()` uses a real path like `Path("resumes/english.tex")` or `Path("/workspace/resumes/english.tex")`. This test is correct on the developer's machine but fails if:
- The test is run from a different working directory
- The real `english.tex` is modified (the test now fails because the expected content changed)
- The test is run in CI where `resumes/english.tex` is not present

The test is also not a unit test — it is an integration test against a real file that happens to exist in the repo.

**Prevention:**
Unit tests for `read_resume()` should use `tmp_path` to create a temporary `.tex` file:

```python
def test_read_resume_returns_content(tmp_path):
    resume = tmp_path / "test.tex"
    resume.write_text("\\documentclass{article}\n\\end{document}", encoding="utf-8")
    result = read_resume(resume)
    assert result == "\\documentclass{article}\n\\end{document}"

def test_read_resume_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_resume(tmp_path / "nonexistent.tex")
```

Never use `config.BASE_RESUME_PATH` in a unit test.

**Phase to address:** Unit test phase for `resume_reader.py`.

---

### Pitfall 18: `config.py` Path Anchoring Causes Import Side Effects in Tests

**What goes wrong:**
`config.py` executes `_ROOT = Path(__file__).parent.parent` at import time. This is correct for production use where `config.py` is at `src/config.py` and `_ROOT` is `/workspace`. However, if a test imports `config` from a different location (e.g., after a `uv tool install .` where the package is installed to `~/.local/lib`), `_ROOT` points to the installed location, not the repo. A test that relies on `config.BASE_RESUME_PATH` pointing to the repo's `resumes/english.tex` will fail silently with a `FileNotFoundError`.

This is not a bug to fix — `Path(__file__).parent.parent` is the correct and documented pattern for this project. The pitfall is in tests that use `config.BASE_RESUME_PATH` assuming it always points to the repo.

**Prevention:**
Tests must never import and use `config.BASE_RESUME_PATH` or `config.OUTPUT_DIR` as test inputs. These are runtime configuration values for the installed CLI. Tests should construct their own paths using `tmp_path`. The only acceptable use of `config` values in tests is to verify that the constants are set to expected types (e.g., `assert isinstance(config.OLLAMA_BASE_URL, str)`).

**Phase to address:** All test phases. This is a principle to establish at the start of test infrastructure setup.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Testing What the Model Returns (Prompt Testing)

**What it looks like:**
```python
messages = _build_messages(resume_text, "Python developer role")
assert "Alexandra" in messages[0]["content"]
assert "surgeon-precise" in messages[0]["content"]
assert "<PERSONA>" in messages[0]["content"]
```

**Why it's wrong:**
This test is asserting the specific text of the system prompt. If the prompt is improved (a core activity of an LLM tool), the test breaks and must be updated. The test creates friction against the most valuable type of iteration: refining the prompt. It also does not test anything that can go wrong at runtime — the prompt content is static Python code, not a runtime artifact.

**What to test instead:**
Test the *structure* of the messages: message count, role sequence (`system` then `user`), that the resume text and job description are present in the user message, that the user message contains the XML delimiters. Do not assert on any specific prose from the system prompt.

```python
def test_build_messages_structure():
    messages = _build_messages("RESUME", "JOB DESC")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "RESUME" in messages[1]["content"]
    assert "JOB DESC" in messages[1]["content"]
```

**Phase to address:** Unit test phase for `_build_messages`.

---

### Anti-Pattern 2: Testing Model Behavior (Response Quality Testing)

**What it looks like:**
```python
# Integration test
result = generate_tailored_resume(resume_text, "We are looking for a Python expert")
assert "Python" in result  # verify the model mentioned Python
assert "expert" in result.lower()  # verify it matched the JD language
```

**Why it's wrong:**
This is testing the model's response quality, not the code's correctness. The code's job is to call the API, handle errors, strip fences, and validate structure. If the model returns valid LaTeX that doesn't happen to contain "Python" (because it used "py" or omitted the keyword), the code is working correctly but the test fails.

**What to test instead:**
Call the code with a trivial resume and job description, and assert only that the code's output contracts are met: the result is a string, it starts with `\documentclass`, it contains `\end{document}`, and no exception was raised.

---

### Anti-Pattern 3: One Integration Test That Tests Everything

**What it looks like:**
```python
@pytest.mark.integration
def test_full_integration():
    resume = read_resume(config.BASE_RESUME_PATH)
    result = generate_tailored_resume(resume, "Senior ML Engineer at Acme Corp...")
    output_path = write_resume(result, tmp_path)
    assert output_path.exists()
    assert result.startswith("\\documentclass")
    # ...and 10 more assertions
```

**Why it's wrong:**
When this test fails, the failure could be in `read_resume`, `generate_tailored_resume`, `write_resume`, the model, the network, or the file system. A single large integration test provides no diagnostic value. It also runs Ollama against the real resume, which takes 30-120 seconds, making the failure feedback loop very slow.

**What to do instead:**
Test each module's integration point separately:
- `read_resume` with a `tmp_path` file (unit-level, fast)
- `generate_tailored_resume` with a minimal fixture resume (integration, real Ollama, small model)
- `write_resume` with `tmp_path` (unit-level, fast)
- Full CLI pipeline via subprocess (e2e, real Ollama, tests the integration of all three)

---

### Anti-Pattern 4: Skip Markers as a Permanent Escape Hatch

**What it looks like:**
```python
@pytest.mark.skip(reason="Ollama not always available")
@pytest.mark.integration
def test_generate_with_real_ollama():
    ...
```

**Why it's wrong:**
A test that is always skipped is not a test. It provides no coverage and creates the illusion of coverage. If the `skip` marker was added because the test was flaky or hard to run, that is the problem to solve (with the `require_ollama` fixture skip-by-condition pattern), not the test's existence.

**What to do instead:**
Use `require_ollama` fixture-based conditional skipping, not permanent `@pytest.mark.skip`. The test runs when Ollama is present and is appropriately skipped when it is not:

```python
@pytest.mark.integration
def test_generate_with_real_ollama(require_ollama):
    result = generate_tailored_resume(MINIMAL_RESUME, "Python developer", model=INTEGRATION_MODEL)
    assert result.lstrip().startswith("\\documentclass")
```

---

### Anti-Pattern 5: Using `unittest.TestCase` Patterns in New pytest Tests

**What it looks like:**
```python
class TestIntegration(unittest.TestCase):
    def test_generate(self):
        with self.assertRaises(RuntimeError):
            generate_tailored_resume("", "")
```

**Why it's wrong:**
The existing tests use `unittest.TestCase` (for historical reasons — they predate the pytest migration). New tests should use plain functions with pytest-style assertions (`assert`, `pytest.raises`). `unittest.TestCase` classes do not support pytest fixtures — `tmp_path`, `require_ollama`, and similar fixtures cannot be injected into `TestCase` methods. This blocks the fixture-based skip pattern required for Ollama-dependent tests.

**What to do instead:**
Write new integration and e2e tests as plain functions:
```python
@pytest.mark.integration
def test_generate(require_ollama, tmp_path):
    result = generate_tailored_resume(MINIMAL_RESUME, "Python developer", model=INTEGRATION_MODEL)
    assert result.lstrip().startswith("\\documentclass")
```

The existing `unittest.TestCase` tests do not need to be rewritten — they work correctly under pytest. Just do not add new `TestCase` classes.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| pytest infrastructure (conftest, markers, pyproject.toml) | Markers not registered → PytestUnknownMarkWarning | Add `[tool.pytest.ini_options]` with `markers` and `--strict-markers` first |
| pytest infrastructure | `pythonpath` not set → import errors if `tests/` directory added | Add `pythonpath = ["src"]` to `[tool.pytest.ini_options]` |
| pytest infrastructure | conftest.py placed in `src/` → fixtures not visible to `tests/` | Place root conftest at `/workspace/conftest.py` |
| Unit tests (`resume_reader`, `resume_writer`) | Using real files or `config` paths | Use `tmp_path` fixture exclusively; never use `config.BASE_RESUME_PATH` |
| Unit tests (`_build_messages`) | Asserting system prompt prose content | Assert structure only (role sequence, XML delimiters, presence of inputs) |
| Integration tests | Using production model → cold-load latency flakiness | Define `INTEGRATION_MODEL` fixture pointing to a small fast model |
| Integration tests | No Ollama availability guard → confusing CI failures | Use `require_ollama` fixture with 3-second connect timeout |
| Integration tests | Asserting on LLM content → non-deterministic failures | Assert only `\documentclass` start and `\end{document}` presence |
| E2E tests | stdin not matching END sentinel exactly → subprocess hangs | Always use `timeout=` on `subprocess.run`; write stdin as named variable |
| E2E tests | Writing output to `config.OUTPUT_DIR` → test artifacts in repo | Always pass `--output-dir str(tmp_path)` in every E2E subprocess call |
| E2E tests | Calling `main()` directly and labeling it "E2E" | E2E must use `subprocess.run(["resume-tailor", ...])` |
| E2E tests | Using `capsys` for subprocess output | Use `capture_output=True, text=True` on `subprocess.run` |

---

## Sources

- pytest capture documentation: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html — `capsys` vs `capfd` distinction; subprocess capture behavior
- pytest markers documentation: https://docs.pytest.org/en/stable/how-to/mark.html — registration, PytestUnknownMarkWarning, `--strict-markers`
- pytest tmp_path documentation: https://docs.pytest.org/en/stable/how-to/tmp_path.html — cleanup behavior (last 3 retained), per-test isolation
- pytest pythonpath configuration: https://docs.pytest.org/en/stable/explanation/pythonpath.html — `pythonpath` setting in `[tool.pytest.ini_options]`
- pytest good practices: https://docs.pytest.org/en/stable/explanation/goodpractices.html — `testpaths`, `pythonpath`, src layout
- pytest markers working examples: https://docs.pytest.org/en/stable/example/markers.html — class-level `pytestmark`, `pytest_configure` registration
- pytest skip documentation: https://docs.pytest.org/en/stable/how-to/skipping.html — skip vs. xfail; fixture-based conditional skipping
- Separating unit and integration tests: https://www.pythontutorials.net/blog/how-to-keep-unit-tests-and-integrations-tests-separate-in-pytest/ — `addopts = -m "not integration"` pattern for CI
- Testing argparse applications: https://jugmac00.github.io/blog/testing-argparse-applications-the-better-way/ — subprocess vs. in-process invocation tradeoffs
- Non-determinism in LLM output: https://arxiv.org/pdf/2408.04667 — "Non-Determinism of 'Deterministic' LLM Settings"; why temperature=0 is not bit-reproducible
- Structural testing of LLM agents: https://arxiv.org/pdf/2601.18827 — separate deterministic structural assertions from probabilistic content evaluation
- Sourcery unit testing LLM output: https://www.sourcery.ai/blog/unit-testing-llm-output — practical patterns for testing systems that call LLMs
- pytest-with-eric markers guide: https://pytest-with-eric.com/pytest-best-practices/pytest-markers/ — custom marker registration and usage patterns
- pytest pythonpath setting: https://pytest-with-eric.com/introduction/pytest-pythonpath/ — four methods for resolving import paths in pytest

---

*Test pitfalls research for: Resume Tailor CLI v1.2 — test coverage milestone*
*Researched: 2026-06-02*
