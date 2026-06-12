---
status: diagnosed
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
  root_cause: "Anti-fabrication relies solely on a soft prompt instruction (TECHNOLOGY FIDELITY rule) whose compliance is probabilistic; compounded by (1) <jd_analysis> injecting an unconstrained JD-technology list that primes the model to insert those names, (2) no temperature/seed in Ollama options so default sampling makes compliance vary run-to-run (the intermittent 'sometimes'), and (3) no post-generation technology-fidelity guard in guards.py so violations pass silently"
  artifacts:
    - path: "src/llm_client.py"
      issue: "<jd_analysis> technologies list injected with no usage instruction (lines 117-128); no temperature/seed in payload options (line 167); fidelity constraint single-sited on Skills element only, not reinforced at bullet/tagline rewrite instructions"
    - path: "src/guards.py"
      issue: "run_guards checks sections, format, and employers only — no technology-fidelity check comparing output tokens against base-resume content"
    - path: "src/jd_analyzer.py"
      issue: "produces the JD technology list that becomes the priming vector; its output is fed into the prompt unconstrained"
  missing:
    - "Set options.temperature to 0 or ~0.2 (optionally fixed seed) in the tailoring payload"
    - "System-prompt rule explaining <jd_analysis>: technologies absent from the resume are relevance-ranking signals only and must never appear in output (or pre-filter the list to the intersection with base-resume content)"
    - "Repeat the fidelity constraint at the bullet/tagline items in <ALLOWED>"
    - "Post-generation guard in guards.py flagging (or retrying) when output contains JD-analysis technology tokens absent from the base resume"
  debug_session: ".planning/debug/fabricated-technologies.md"
