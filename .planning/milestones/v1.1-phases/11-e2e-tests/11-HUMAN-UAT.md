---
status: complete
phase: 11-e2e-tests
source: [11-VERIFICATION.md]
started: 2026-06-08T18:30:00Z
updated: 2026-06-08T18:30:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. TEST-11 golden path with live Ollama

expected: With Ollama running and a model loaded, `uv run pytest tests/e2e/test_cli.py::test_golden_path_exits_0_creates_output_file -v` exits 0 with PASSED; stdout contains "Tailored resume written to:"; one `tailored_resume_YYYYMMDD_HHMMSS.tex` file exists in tmp_path
result: PASSED — 1 passed in 126.85s (0:02:06)

**Steps to verify:**
1. Start Ollama: `ollama serve` (in a separate terminal)
2. Ensure a model is loaded (e.g. `ollama pull llama3.2` or whichever is configured)
3. Run: `uv run pytest tests/e2e/test_cli.py::test_golden_path_exits_0_creates_output_file -v`
4. Confirm: PASSED, exit 0, stdout shows "Tailored resume written to:"

## Summary

total: 1
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
