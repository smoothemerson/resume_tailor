---
status: partial
phase: 12-prompt-precision
source: [12-VERIFICATION.md]
started: 2026-06-11T00:00:00Z
updated: 2026-06-11T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. End-to-end tailoring run with live Ollama
expected: Run the CLI against a real job description with Ollama running. Protected sections (contact block, section headers, `\header{...}`, `\href{url}{\textbf{ProjectName}}`) are byte-identical in the output; only ALLOWED elements (title line, employer taglines/bullets, project subtitle/bullets, skills content) differ; no fabricated technologies appear.
result: [pending]

### 2. Contradiction behavior check (CR-01 / CR-02)
expected: Despite the internal prompt contradictions flagged in 12-REVIEW.md (ALLOWED title line vs "entire" contact-block protection; stale OUTPUT_FORMAT scope list), the model still rewrites the title line and project content correctly and does not touch the contact block.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
