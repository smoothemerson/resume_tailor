---
status: complete
phase: 12-prompt-precision
source: [12-01-SUMMARY.md, 12-02-SUMMARY.md]
started: 2026-06-13T00:00:00Z
updated: 2026-06-13T00:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Test suite passes
expected: Run `pytest -x -q` from the project root. All 125 tests pass, 3 skipped (Ollama-dependent). No failures or errors.
result: pass

### 2. System prompt has ALLOWED section with 6 elements
expected: Open `src/llm_client.py` and find the `_build_messages()` function. The system prompt contains an `<ALLOWED>` section listing exactly six rewritable resume elements with their LaTeX patterns: (1) title line in contact header, (2) employer taglines (`\textit{\small ...}\\`), (3) employer bullet points (`\item` inside `\begin{itemize}`), (4) project subtitle, (5) project bullet points, (6) skills content (`\noindent\textbf{Category:}` lines). Closes with "Everything not listed above must remain byte-for-byte identical."
result: pass

### 3. CONSTRAINTS section has TECHNOLOGY FIDELITY rule
expected: In `src/llm_client.py` `_build_messages()`, the `<CONSTRAINTS>` section contains a TECHNOLOGY FIDELITY rule stating present technologies must remain, absent technologies must not be added, with the Azure/AWS example. The JD ANALYSIS USAGE rule immediately follows, stating jd_analysis technologies are "relevance-ranking signals" only and "must never appear in the output."
result: pass

### 4. Temperature 0.2 in Ollama payload
expected: In `src/llm_client.py`, the tailoring Ollama API payload includes `"temperature": 0.2` in the `options` dict (not 0, not 1.0 — specifically 0.2). Run `grep -n '"temperature"' src/llm_client.py` to confirm.
result: pass

### 5. Four inline fidelity reminders on ALLOWED bullets
expected: In `src/llm_client.py` `_build_messages()`, exactly four ALLOWED bullets carry the inline reminder "(mention only technologies already present in the original resume)". These appear on: employer taglines, employer bullet points, project subtitle, and project bullet points. Run `grep -c "already present in the original resume" src/llm_client.py` — result should be 4.
result: pass

### 6. Fabrication guard in guards.py
expected: Open `src/guards.py`. A `_check_fabricated_technologies()` private function exists. It uses `re.compile` with `re.escape` and word-boundary lookarounds for case-insensitive token-bounded matching, wrapped in try/except. `run_guards()` accepts a `jd_technologies` keyword parameter (4th param, default None). `cli.py` passes `analysis["technologies"]` into `run_guards` when analysis is not None.
result: pass

### 7. End-to-end CLI run (skip if Ollama not running)
expected: With Ollama running locally, run the CLI against a real job description. After the run: protected sections in the output (contact block, section headers `\header{...}`, employer header lines, project anchors `\href{url}{\textbf{ProjectName}}`) are byte-identical to the base resume. If the model added a technology not present in the base resume, a WARNING log line appears naming the technology and containing "possible fabrication".
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
