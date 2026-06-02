# Test Features — Resume Tailor CLI v1.2

**Domain:** Python CLI test pyramid — unit, integration, e2e for an LLM-backed CLI
**Researched:** 2026-06-02
**Confidence:** HIGH (derived from direct codebase analysis + verified pytest patterns)

---

## Scope

This document covers test behaviors to build in v1.2. The existing 18 tests (11 in
`llm_client_test.py`, 7 in `cli_test.py`) use `unittest` + `unittest.mock` and cover
`_strip_fences`, `_validate_latex`, health-check mocking, done_reason guard, CLI input
loop, empty-JD exit, and error propagation. These are already shipped and excluded.

Gaps that v1.2 must fill:
- `_build_messages()` is entirely untested
- `resume_reader.py` and `resume_writer.py` are entirely untested
- `_check_ollama_health()` has no isolated unit tests (only tested as a side effect via `generate_tailored_resume`)
- No integration tests (real Ollama HTTP calls)
- No e2e tests (subprocess invocation of the CLI)
- No pytest infrastructure (no `conftest.py`, no markers, no organized test layout)

---

## Unit Tests

### Table stakes

These behaviors must be covered. They are deterministic, require no external services, and
directly protect the modules' contracts.

| Behavior | Module | Test approach | Why it matters |
|----------|--------|---------------|----------------|
| `_build_messages()` returns exactly 2 messages | `llm_client.py` | Assert `len(result) == 2` | Ollama `/api/chat` requires a messages list; extra or missing messages cause silent misbehavior |
| First message has `role == "system"` | `llm_client.py` | Assert `result[0]["role"] == "system"` | System/user separation is the entire purpose of `/api/chat` over `/api/generate` |
| Second message has `role == "user"` | `llm_client.py` | Assert `result[1]["role"] == "user"` | Same contract enforcement |
| User message contains `<job_description>` XML tag | `llm_client.py` | Assert `"<job_description>"` in `result[1]["content"]` | If the tag is absent, the prompt structure is broken and the model won't parse correctly |
| User message contains `<resume>` XML tag | `llm_client.py` | Assert `"<resume>"` in `result[1]["content"]` | Same structural contract |
| User message embeds the job description text | `llm_client.py` | Assert `job_description` in `result[1]["content"]` | Verifies the parameter is actually threaded in, not silently swallowed |
| User message embeds the resume text | `llm_client.py` | Assert `resume_text` in `result[1]["content"]` | Same |
| System prompt contains `<PERSONA>` tag | `llm_client.py` | Assert `"<PERSONA>"` in `result[0]["content"]` | Validates the XML-structured prompt is present; not just non-empty |
| System prompt contains `<CONSTRAINTS>` tag | `llm_client.py` | Assert `"<CONSTRAINTS>"` in `result[0]["content"]` | The anti-hallucination section is the most critical guardrail — must not accidentally be stripped |
| System prompt contains `\documentclass` instruction | `llm_client.py` | Assert `"\\documentclass"` in `result[0]["content"]` | The output format instruction must be present verbatim |
| `_check_ollama_health()` raises `RuntimeError` on `ConnectionError` | `llm_client.py` | Mock `requests.get` to raise `ConnectionError`; assert `RuntimeError` | Isolated test, not covered via `generate_tailored_resume` |
| `_check_ollama_health()` raises `RuntimeError` on `Timeout` | `llm_client.py` | Mock `requests.get` to raise `Timeout`; assert `RuntimeError` | The timeout path exists in the code but has no test |
| `_check_ollama_health()` does not raise on 200 response | `llm_client.py` | Mock `requests.get` returning 200; assert no exception | Positive path needed alongside negative paths |
| `read_resume()` returns file contents as string | `resume_reader.py` | `tmp_path` fixture; write `.tex` file; assert return value | Module has no tests at all |
| `read_resume()` raises `FileNotFoundError` on missing file | `resume_reader.py` | Pass nonexistent path; assert `FileNotFoundError` | Already wrapped with a custom message — test the raise not just the existence of the function |
| `write_resume()` creates output directory if it does not exist | `resume_writer.py` | Pass `tmp_path / "new_subdir"`; assert directory exists after call | `mkdir(parents=True, exist_ok=True)` — if that line is ever removed, nothing else catches it |
| `write_resume()` returns a `Path` object | `resume_writer.py` | Assert `isinstance(result, Path)` | `cli.py` calls `.resolve()` on the return value — wrong type would raise `AttributeError` at runtime |
| `write_resume()` filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex` | `resume_writer.py` | `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)` | The timestamp pattern is the user-visible contract; test it structurally without depending on the exact time |
| `write_resume()` writes the content to disk | `resume_writer.py` | Assert `result.read_text() == content` | Verifies content is not silently truncated or encoded differently |

### Differentiators

These tests add coverage depth but are not blocking. Build them after table stakes are passing.

| Behavior | Module | Why valuable |
|----------|--------|--------------|
| `_build_messages()` with empty strings as inputs | `llm_client.py` | Edge case: empty JD or empty resume should not crash `_build_messages`; the failure should surface at the LLM layer, not here |
| System prompt content is non-empty and substantial (len > 500) | `llm_client.py` | Prevents accidental truncation from a refactor that loses the multi-line string |
| `read_resume()` with a file containing non-ASCII characters | `resume_reader.py` | The `encoding="utf-8"` argument is explicit; verify it handles UTF-8 cleanly (accented characters in contact info or company names) |
| `write_resume()` called twice in same second does not collide | `resume_writer.py` | Two calls within the same second produce the same timestamp — the tool does not guard against this. Documenting the behavior via a test is better than silent surprise. |
| `_check_ollama_health()` does not raise on non-200 response | `llm_client.py` | The current implementation only catches exceptions — it does not check the HTTP status code. If the contract is intentional, a test documents it. If it is an oversight, the test surfaces it. |

### Anti-features / Out of scope for unit tests

| What to avoid | Why |
|---------------|-----|
| Testing `_build_messages()` prompt content quality (phrasing, tone) | That is an LLM eval concern, not a unit test concern. Tests must not encode phrasing that is expected to evolve. |
| Testing `_strip_fences()` and `_validate_latex()` more thoroughly | Already covered by 7 existing tests. No gap. |
| Testing `generate_tailored_resume()` with real HTTP at unit level | Real HTTP belongs in integration tests. Unit tests mock at the `requests` layer. |
| Testing config.py constants | Constants by definition have no logic to test. Asserting `OLLAMA_MODEL == "qwen3:14b"` creates a test that breaks on every config change without providing any safety signal. |
| Asserting exact system prompt text | The prompt will evolve. Testing structural markers (`<PERSONA>`, `<CONSTRAINTS>`, `\documentclass`) is the correct contract; testing exact phrasing is fragile and punishes improvement. |
| Testing `log_manager.py` | It is a 3-method wrapper over `print()`. The behavior that matters (stderr output) is tested at the CLI level. |

---

## Integration Tests

These tests make real HTTP calls to a locally running Ollama instance. They require Ollama to
be running and should be skipped gracefully when it is not. No subprocess; import and call
`generate_tailored_resume()` directly.

### Table stakes

| Behavior | Invariant tested | Scope |
|----------|-----------------|-------|
| `_check_ollama_health()` does not raise when Ollama is running | Connectivity only — verifies the happy path | Direct function call with no mocks |
| `generate_tailored_resume()` returns a non-empty string | Output exists and is a string | Direct function call with a minimal `.tex` fixture and short JD |
| Returned string starts with `\documentclass` | Structural invariant — holds regardless of LLM output variation | `assert result.lstrip().startswith("\\documentclass")` |
| Returned string contains `\end{document}` | Structural invariant — truncated output is a hard failure | `assert "\\end{document}" in result` |
| Returned string does not contain markdown fences | `_strip_fences()` contract holds end-to-end | `assert "```" not in result` |

**Invariant-based testing rationale:** LLM output varies on every call. The test cannot assert
"the word 'Python' appears in section 3." It can assert that `_validate_latex()` passes, that the
document structure is intact, and that the output is a string. These invariants are stable across
every non-truncated run from any capable model.

**Fixture requirement:** Integration tests need a minimal but valid `.tex` file — roughly 20-30
lines with `\documentclass`, `\begin{document}`, one `\section{Summary}`, one `\section{Skills}`,
and `\end{document}`. This is enough for the model to produce structurally valid output without
hitting context limits. Store this as `tests/fixtures/minimal_resume.tex`.

### Differentiators

| Behavior | Why valuable |
|----------|--------------|
| `generate_tailored_resume()` with `model` parameter override | Verifies the `model` argument is actually threaded into the payload; can use a small fast model in CI to keep latency down |
| Response time under a reasonable ceiling (e.g., 120 seconds) | Catches context-window overload or runaway generation early; use `time.time()` before/after, not a timeout that fails the test |
| HTTP 404 or unexpected status raises `RuntimeError` | Verify the `raise_for_status()` path; can be tested by pointing at a bad endpoint URL in a separate test |

### Non-determinism handling

**Strategy: test structure, not content.** The correct approach for a non-deterministic text output
is to test the properties that must always hold regardless of what the model generates:

1. Return type is `str`
2. Structural markers (`\documentclass`, `\end{document}`) are present
3. No markdown fences survived
4. No exception was raised

**Do not test:** Specific words, section content, keyword presence, or anything that depends on
model behavior. These will produce intermittent failures that erode trust in the test suite.

**Skipping when Ollama is down:** Define an `ollama_available()` helper in `conftest.py` that
attempts `requests.get("http://localhost:11434/api/tags", timeout=3)` and returns `True` or
`False`. Use `@pytest.mark.skipif(not ollama_available(), reason="Ollama not running")` on all
integration and e2e tests. This avoids `FAILED` in CI where Ollama is absent; tests report `SKIP`
instead. Alternatively, use `pytest.mark.integration` as a custom marker and exclude it with
`-m "not integration"` in CI pipelines where Ollama is not available.

**Run count:** Do not run integration tests multiple times to "average" non-determinism. One call
is sufficient when testing structural invariants. Multi-run averaging is appropriate for LLM
evaluation frameworks (quality scoring) — not for structural pass/fail tests.

---

## E2E Tests

These tests invoke the CLI via `subprocess.run()` and verify exit codes, output files, and
stderr messages. They exercise the full integration: argparse, input loop, Ollama call, file write.

### Table stakes

| Behavior | How to test | Assert |
|----------|-------------|--------|
| Golden path exits with code 0 | `subprocess.run` with `--resume`, `--output-dir`, job description piped via `input=` | `result.returncode == 0` |
| Output file is created in the specified `--output-dir` | List `output_dir` after golden path run | `len(list(output_dir.glob("*.tex"))) == 1` |
| Output filename matches `tailored_resume_YYYYMMDD_HHMMSS.tex` | Inspect the filename of the created file | `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", file.name)` |
| Empty job description exits with code 1 | Pipe `"END\n"` as stdin | `result.returncode == 1` |
| Empty job description prints error to stderr | Same run | `"empty"` in `result.stderr.lower()` or `"Error"` in `result.stderr` |
| Missing resume file exits with code 1 | Pass `--resume /nonexistent/path.tex` | `result.returncode == 1` |
| Missing resume file prints error to stderr | Same run | `result.stderr` is non-empty |
| Progress message appears in stdout | Golden path run | `"Tailoring resume"` in `result.stdout` |
| Success message with output path appears in stdout | Golden path run | `"Tailored resume written to:"` in `result.stdout` |

**Stdin piping pattern:** Use `subprocess.run()` with `input=` and `text=True`. The CLI reads
until `"END"` on a line by itself. The correct input format is:

```python
job_input = "Senior Python Engineer\nRequires FastAPI and PostgreSQL\nEND\n"
result = subprocess.run(
    ["python", "-m", "cli", "--resume", str(resume_path), "--output-dir", str(output_dir)],
    input=job_input,
    capture_output=True,
    text=True,
    cwd="/workspace/src",
)
```

The `\n` after `END` is required. Without it, the `input()` call on the last line blocks waiting
for a newline and the subprocess hangs. This is the most common e2e test setup failure for this
CLI pattern.

### Differentiators

| Behavior | Why valuable |
|----------|--------------|
| `--model` flag is accepted without error | Argparse config test; confirms the flag wires through without breaking the call |
| `--output-dir` creates a nested directory that does not exist | Confirms `mkdir(parents=True)` path works from the CLI level, not just unit level |
| Output file contents start with `\documentclass` | Verifies the full pipeline writes correct content, not just that a file was created. This is the one content check worth doing at e2e level. |
| Whitespace-only job description exits with code 1 | Pipe `"   \nEND\n"`; the `.strip()` in `cli.py` should catch it; an e2e test confirms no regression |

### Error path coverage

| Error condition | Trigger | Assert |
|-----------------|---------|--------|
| Ollama unreachable | Start test with Ollama confirmed down (or mock via `--resume` + env-override URL pointing at a dead port); alternately skip when Ollama must be up | `returncode == 1` and `result.stderr` contains `"Error"` |
| Empty JD (whitespace only) | Pipe `"   \nEND\n"` | `returncode == 1`, `result.stderr` non-empty |
| Resume path does not exist | `--resume /does/not/exist.tex` | `returncode == 1`, `result.stderr` non-empty |
| No traceback in stderr on any error | All error cases above | `"Traceback"` not in `result.stderr` — the try/except in `cli.py` must suppress it |

**Ollama-down e2e test:** This is the hardest e2e error path. Options in order of preference:
1. Use `@pytest.mark.skipif(not ollama_available(), ...)` to skip this test when Ollama is
   running (the test is only meaningful when Ollama is absent). Combine with an `ollama_required`
   marker for tests that need Ollama up.
2. Pass `--resume` pointing to a real file but use a patched config or env var to point the URL
   at a dead port (e.g., `localhost:19999`). This requires exposing the URL as a config override,
   which the current codebase does not support. Do not refactor `llm_client.py` just for this test.
3. Accept that the Ollama-down path is covered by unit tests (`_check_ollama_health()` mocks)
   and document this as a known gap in e2e coverage.

**Recommendation:** Option 3 is correct for this codebase. The "Ollama unreachable" path is fully
exercised at the unit level. An e2e test for it would either require a codebase refactor (adds
complexity) or be unreliable (depends on Ollama being genuinely absent). Document the gap.

---

## Test Infrastructure

### Table stakes

| Artifact | Purpose |
|----------|---------|
| `tests/unit/` directory | Separate unit tests from integration and e2e |
| `tests/integration/` directory | Integration tests with real Ollama, clearly separated |
| `tests/e2e/` directory | Subprocess-based CLI tests |
| `tests/fixtures/minimal_resume.tex` | Shared `.tex` fixture for integration and e2e |
| `conftest.py` at `tests/` root | `ollama_available()` helper; `@pytest.fixture` for `tmp_path`-based output dirs; marker registration |
| `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml` | Register `integration` and `e2e` markers to suppress `PytestUnknownMarkWarning` |

### Differentiators

| Artifact | Purpose |
|----------|---------|
| `pytest -m "not integration and not e2e"` in CI | Allows running only unit tests without Ollama; integration and e2e run in local dev |
| Reuse of `minimal_resume.tex` across integration and e2e | Avoids test fixture drift; a single file is easier to maintain than one per test |

### Anti-features / Out of scope

| What to avoid | Why |
|---------------|-----|
| Migration of existing tests from `unittest` to `pytest` | The existing tests work and are already in the dev cycle; migrating them adds risk for no behavioral gain. Pytest runs `unittest.TestCase` subclasses natively. |
| Snapshot testing (comparing full output to a reference `.tex`) | LLM output changes every run. A snapshot that must be re-approved on every run is noise, not signal. |
| `pytest-subprocess` plugin | Adds a dev dependency for functionality that `subprocess.run` provides directly. The constraint is stdlib + requests for production; keep dev deps minimal too. |
| `pytest-asyncio` or async test setup | The codebase is entirely synchronous. No async test infrastructure needed. |
| Coverage enforcement (e.g., `--cov-fail-under=90`) | Coverage percentage is a proxy metric. For this codebase, test behavior coverage (the table-stakes list above) is the correct target. Do not optimize for coverage percentage. |

---

## Feature Dependencies

```
[Unit tests]
  _build_messages() tests ──────────────────── no dependencies
  _check_ollama_health() isolated tests ────── no dependencies
  resume_reader tests (tmp_path fixture) ───── pytest tmp_path (built-in)
  resume_writer tests (tmp_path fixture) ────── pytest tmp_path (built-in)

[Integration tests]
  real HTTP tests ──────────────────────────── Ollama running + tests/fixtures/minimal_resume.tex
  conftest.py ollama_available() ──────────── shared by integration + e2e

[E2E tests]
  subprocess CLI tests ────────────────────── Ollama running + tests/fixtures/minimal_resume.tex
  golden path ─────────────────────────────── resume_reader + resume_writer + llm_client all working
  error paths ─────────────────────────────── tmp_path for output dirs

[Test infrastructure]
  conftest.py ──────────────────────────────── must exist before integration + e2e tests
  pyproject.toml marker registration ────────── must exist to suppress warnings
```

### Build order

1. Test infrastructure (`conftest.py`, marker registration, `tests/` directory layout, `minimal_resume.tex`)
2. Unit tests for `_build_messages()` — no fixtures, no mocks, pure function
3. Unit tests for `_check_ollama_health()` in isolation — patch `requests.get` directly
4. Unit tests for `resume_reader` and `resume_writer` — use `pytest`'s `tmp_path` fixture
5. Integration tests — require `conftest.py` and `minimal_resume.tex`
6. E2E tests — require all of the above plus a working CLI invocation path

---

## Sources

- pytest skip/skipif documentation: [pytest skip and xfail](https://docs.pytest.org/en/stable/how-to/skipping.html) — HIGH confidence
- pytest custom markers: [Working with custom markers](https://docs.pytest.org/en/stable/example/markers.html) — HIGH confidence
- LLM integration testing patterns: [Integration Testing Workflows](https://apxml.com/courses/python-llm-workflows/chapter-9-testing-evaluating-llm-apps/integration-testing-llm-workflows) — MEDIUM confidence
- Non-determinism in AI testing: [Testing AI Agents: Validating Non-Deterministic Behavior](https://www.sitepoint.com/testing-ai-agents-deterministic-evaluation-in-a-non-deterministic-world/) — MEDIUM confidence
- CLI subprocess testing patterns: [pytest-subprocess-example](https://github.com/rhcarvalho/pytest-subprocess-example) — MEDIUM confidence
- Existing codebase: `/workspace/src/llm_client.py`, `/workspace/src/cli.py`, `/workspace/src/resume_reader.py`, `/workspace/src/resume_writer.py` — HIGH confidence

---

*Test feature research for: Resume Tailor CLI v1.2 Test Coverage*
*Researched: 2026-06-02*
