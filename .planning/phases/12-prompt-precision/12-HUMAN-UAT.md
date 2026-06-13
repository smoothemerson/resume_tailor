---
status: partial
phase: 12-prompt-precision
source: [12-VERIFICATION.md]
started: 2026-06-11T00:00:00Z
updated: 2026-06-13T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. End-to-end tailoring run with live Ollama (re-run after gap closure)
expected: Run the CLI against a real job description with Ollama running. Protected sections (contact block, section headers, `\header{...}`, `\href{url}{\textbf{ProjectName}}`) are byte-identical in the output; only ALLOWED elements (title line, employer taglines/bullets, project subtitle/bullets, skills content) differ; no fabricated technologies appear. If the model slips through, a WARNING log entry names the specific technology and contains "possible fabrication".
result: pending
note: "Three-layer defense implemented in 12-02: temperature=0.2 in payload, JD ANALYSIS USAGE rule in system prompt + inline fidelity reminders on 4 ALLOWED bullets, _check_fabricated_technologies guard in guards.py wired from cli.py. Live re-run needed to confirm gap is closed in practice."
severity: major

### 2. Contradiction behavior check (CR-01 / CR-02)
expected: Despite the internal prompt contradictions flagged in 12-REVIEW.md (ALLOWED title line vs "entire" contact-block protection; stale OUTPUT_FORMAT scope list), the model still rewrites the title line and project content correctly and does not touch the contact block.
result: pass

## Summary

total: 2
passed: 1
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

- truth: "No fabricated technologies appear in the tailored output; only experience the user actually has is surfaced, even when the job description lists technologies absent from the base resume"
  status: pending
  reason: "Three-layer defense implemented in 12-02 (temperature=0.2, JD ANALYSIS USAGE rule, inline reminders x4, _check_fabricated_technologies guard). All 4 missing items from diagnosis implemented. Live re-run pending."
  severity: major
  test: 1
  resolved_by: "12-02-PLAN"
  resolution_artifacts:
    - path: "src/llm_client.py"
      change: "temperature=0.2 in options payload; JD ANALYSIS USAGE rule in CONSTRAINTS; inline reminder on 4 ALLOWED bullets"
    - path: "src/guards.py"
      change: "_check_fabricated_technologies() guard with token-boundary regex; wired as fourth check in run_guards()"
    - path: "src/cli.py"
      change: "passes analysis['technologies'] to run_guards via dict-unpacking when analysis is not None"
  debug_session: ".planning/debug/fabricated-technologies.md"
