# Phase 9: Unit Test Gaps - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Add isolated unit tests for `_build_messages()`, `_check_ollama_health()`, `read_resume()`, and `write_resume()` in `tests/unit/` — all mocked, all fast, zero Ollama dependency. Requirements TEST-04 through TEST-07.

</domain>

<decisions>
## Implementation Decisions

### File Organization
- **D-01:** New test files go in `tests/unit/` using `test_*.py` prefix (pytest default discovery pattern) — not `*_test.py` like `src/`.
- **D-02:** One file per source module: `test_llm_client.py` (covers `_build_messages` + `_check_ollama_health`), `test_resume_reader.py`, `test_resume_writer.py`.

### Markers
- **D-03:** Every new test in `tests/unit/` carries `@pytest.mark.unit` — required for `pytest -m unit tests/unit/` (ROADMAP success criteria command).
- **D-04:** `src/*_test.py` files are left as-is — no markers added to existing tests. They are not in scope for Phase 9.

### Timestamp Assertion (write_resume)
- **D-05:** Use `re.match(r"tailored_resume_\d{8}_\d{6}\.tex", path.name)` to assert filename pattern — no datetime mocking needed.
- **D-06:** Assert both filename pattern AND that `path.read_text(encoding="utf-8") == input_string` (covers full TEST-07 requirement).
- **D-07:** Use pytest's `tmp_path` fixture for the output directory in `write_resume()` tests.

### _check_ollama_health() Coverage
- **D-08:** Tests call `_check_ollama_health()` directly (not through `generate_tailored_resume()`), patching `llm_client.requests.get`.
- **D-09:** Cover all three paths: `ConnectionError` → `RuntimeError`, `Timeout` → `RuntimeError`, HTTP 200 → no raise.
- **D-10:** Also cover the `HTTPError` path (non-200 response raises `RuntimeError`) even though TEST-05 doesn't explicitly list it — it's already in the function body and costs one test.

### Overlap with Existing Tests
- **D-11:** Keep the existing `test_health_check_connection_error_raises_runtime_error` in `src/llm_client_test.py` — it tests at the `generate_tailored_resume()` level, which is a different layer from the new direct `_check_ollama_health()` tests. Both are valid; no duplication to remove.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/ROADMAP.md` §Phase 9 — Goal, success criteria (4 items), requirements list (TEST-04 to TEST-07)
- `.planning/REQUIREMENTS.md` §Unit Test Gaps — Full requirement text for TEST-04, TEST-05, TEST-06, TEST-07

### Source Files (read before writing tests)
- `src/llm_client.py` — Contains `_build_messages()` and `_check_ollama_health()` — inspect signatures, return types, and exception types before writing tests
- `src/resume_reader.py` — Contains `read_resume(path: Path) -> str` — simple, raises `FileNotFoundError`
- `src/resume_writer.py` — Contains `write_resume(content: str, output_dir: Path) -> Path` — uses `datetime.now().strftime` for filename
- `src/llm_client_test.py` — Existing tests; keep as-is; reference for patch target patterns (`llm_client.requests.get`, `llm_client.requests.post`)
- `tests/conftest.py` — Ollama fixtures available to tests/ subtree (not needed for unit tests but confirms directory structure)

### Phase 8 Context (test infrastructure decisions)
- `.planning/phases/08-test-infrastructure/08-CONTEXT.md` — D-01 to D-08 define pytest config, directory layout, and fixture design that Phase 9 builds on

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/llm_client_test.py` patch pattern: `@patch("llm_client.requests.get")` and `@patch("llm_client.requests.post")` — use the same module-qualified path in new tests
- `tests/conftest.py` `tmp_path` is a built-in pytest fixture, not from conftest — no import needed
- `_check_ollama_health()` uses `response.raise_for_status()` → `requests.HTTPError` → `RuntimeError`; Timeout uses `requests.Timeout`

### Established Patterns
- **raise-not-exit pattern**: `llm_client.py`, `resume_reader.py`, and `resume_writer.py` all raise — never call `sys.exit`. Tests can call functions directly without subprocess wrapping.
- **No `__init__.py` in tests/**: `tests/unit/` is a bare directory (rootdir-relative layout per Phase 8 D-03). Import resolution handled by `pythonpath = ["src"]` in pyproject.toml.
- `MagicMock(status_code=200)` for a passing health check mock — see existing tests for the pattern.

### Integration Points
- `pyproject.toml` already has `[tool.pytest.ini_options]` with `testpaths = ["src", "tests"]`, `pythonpath = ["src"]`, markers, and `addopts = "--strict-markers -ra"` — no changes needed.
- `tests/unit/` directory already exists (created in Phase 8).

</code_context>

<specifics>
## Specific Ideas

- `_build_messages()` tests: verify 2-element list, role ordering (`"system"` then `"user"`), and XML tag presence (`<job_description>`, `<resume>`, `<PERSONA>`, `<CONSTRAINTS>`) — do NOT assert exact prompt prose (per ROADMAP success criteria).
- `_check_ollama_health()` success test: mock `requests.get` to return `MagicMock(status_code=200)` with a no-op `raise_for_status`; assert the function returns `None` (no raise).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 9-Unit Test Gaps*
*Context gathered: 2026-06-04*
