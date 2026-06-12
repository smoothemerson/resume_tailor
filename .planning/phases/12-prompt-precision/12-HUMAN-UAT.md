---
status: complete
phase: 12-prompt-precision
source: [12-VERIFICATION.md]
started: 2026-06-11T00:00:00Z
updated: 2026-06-12T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. End-to-end tailoring run with live Ollama
expected: Run the CLI against a real job description with Ollama running. Protected sections (contact block, section headers, `\header{...}`, `\href{url}{\textbf{ProjectName}}`) are byte-identical in the output; only ALLOWED elements (title line, employer taglines/bullets, project subtitle/bullets, skills content) differ; no fabricated technologies appear.
result: issue
reported: "yes, did not modify contact, section headers. only did modified allowed elements. but sometimes it does fabricate techenologies that I do not have experience and it did put there cause of the JD."
severity: major

### 2. Contradiction behavior check (CR-01 / CR-02)
expected: Despite the internal prompt contradictions flagged in 12-REVIEW.md (ALLOWED title line vs "entire" contact-block protection; stale OUTPUT_FORMAT scope list), the model still rewrites the title line and project content correctly and does not touch the contact block.
result: pass

## Summary

total: 2
passed: 1
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "No fabricated technologies appear in the tailored output; only experience the user actually has is surfaced, even when the job description lists technologies absent from the base resume"
  status: failed
  reason: "User reported: sometimes it does fabricate technologies that I do not have experience and it did put there cause of the JD"
  severity: major
  test: 1
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
