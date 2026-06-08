# Phase 9: Unit Test Gaps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 09-unit-test-gaps
**Areas discussed:** File naming convention, Timestamp assertion strategy, Marker discipline, Overlap with existing tests

---

## File Naming Convention

| Option | Description | Selected |
|--------|-------------|----------|
| test_*.py (pytest default) | Matches pytest's default discovery pattern; dominant modern Python convention; visually distinct from src/*_test.py | ✓ |
| *_test.py (match src/ pattern) | Consistent with existing src/ files; two naming styles coexist | |

**User's choice:** test_*.py prefix (pytest default)
**Notes:** One file per source module — test_llm_client.py, test_resume_reader.py, test_resume_writer.py.

---

## Timestamp Assertion Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| re.match() regex assertion | Assert filename matches `tailored_resume_\d{8}_\d{6}\.tex`; simple, no mocking | ✓ |
| monkeypatch datetime.now() | Freeze time for exact filename assertion; more complex; datetime is C type requiring module-level patch | |

**User's choice:** re.match() regex assertion
**Notes:** Also assert file content equals input string (covers full TEST-07). Use pytest's tmp_path fixture for output directory.

---

## Marker Discipline

| Option | Description | Selected |
|--------|-------------|----------|
| @pytest.mark.unit on all tests/unit/ tests | Required for `pytest -m unit tests/unit/`; matches ROADMAP success criteria | ✓ |
| Skip markers, directory only | `pytest tests/unit/` works but `-m unit` returns zero results; diverges from ROADMAP command | |

**User's choice:** @pytest.mark.unit on all new tests in tests/unit/
**Notes:** src/*_test.py left as-is — no markers added to existing tests (out of scope for Phase 9).

---

## Overlap with Existing Tests

| Option | Description | Selected |
|--------|-------------|----------|
| Keep both (different call stack levels) | src/ test exercises generate_tailored_resume(); new test exercises _check_ollama_health() directly — both valid | ✓ |
| Remove the old src/ test | New isolated test makes old indirect test redundant; removes coverage of full error propagation path | |

**User's choice:** Keep both — different levels of the call stack
**Notes:** Also add HTTPError path coverage for _check_ollama_health() even though TEST-05 doesn't list it — it's in the function body and costs one test.

---

## Claude's Discretion

None — user answered all gray areas directly.

## Deferred Ideas

None — discussion stayed within phase scope.
