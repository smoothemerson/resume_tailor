---
status: diagnosed
trigger: "yes, did not modify contact, section headers. only did modified allowed elements. but sometimes it does fabricate techenologies that I do not have experience and it did put there cause of the JD."
created: 2026-06-12T00:00:00Z
updated: 2026-06-12T00:00:00Z
mode: find_root_cause_only
symptoms_prefilled: true
---

## Current Focus

hypothesis: CONFIRMED — fabrication is the result of a soft prompt-only guardrail being undermined by JD-technology priming, unconstrained sampling temperature, and zero post-generation technology validation
test: static analysis of prompt construction, request payload, and guard pipeline
expecting: n/a — diagnosis complete
next_action: return ROOT CAUSE FOUND to orchestrator (no fix in this mode)

## Symptoms

expected: "Run the CLI against a real job description with Ollama running. Protected sections are byte-identical; only ALLOWED elements differ; no fabricated technologies appear."
actual: "Protected sections honored; ALLOWED-only edits honored; but sometimes the output contains technologies the user has no experience with, pulled from the job description."
errors: none
reproduction: "Test 1 in 12-HUMAN-UAT.md — intermittent ('sometimes'); more likely when the JD lists technologies absent from the base resume"
started: "Discovered during UAT 2026-06-12 (phase 12 prompt-precision)"

## Eliminated

- hypothesis: "TECHNOLOGY FIDELITY rule is missing or not delivered to the model"
  evidence: "Rule exists at src/llm_client.py:87-93 with both directional clauses and the Azure/AWS example; 12-VERIFICATION.md runtime probe confirmed it renders inside <CONSTRAINTS> in the message actually sent to Ollama. The instruction is present — it is just not reliably obeyed."
  timestamp: 2026-06-12

- hypothesis: "Protected-section/structural enforcement is broken and fabrication leaks in via structural drift"
  evidence: "User confirmed contact block, section headers, and protected anchors are untouched; UAT Test 2 (contradiction behavior) passed. Fabrication occurs strictly inside ALLOWED rewrite sites (taglines, bullets, skills lines). This is content-level, not parsing/structure-level."
  timestamp: 2026-06-12

- hypothesis: "Output parsing (fence stripping / validation) corrupts or injects content"
  evidence: "_strip_fences and _validate_latex (src/llm_client.py:136-153) only remove markdown fences and assert documentclass/end{document} envelope; they never add tokens."
  timestamp: 2026-06-12

## Evidence

- timestamp: 2026-06-12
  checked: src/llm_client.py:163-168 (request payload)
  found: 'payload options are `{"num_ctx": 8192}` only. No temperature, no seed, no top_p. Verified via grep across src/*.py — the only `options` key in the codebase is num_ctx. Ollama therefore uses model-default sampling temperature (~0.6-0.8 for qwen3:14b).'
  implication: "Generation is stochastic. Compliance with the fidelity instruction varies run-to-run — this is the direct mechanism behind 'sometimes it fabricates'."

- timestamp: 2026-06-12
  checked: src/llm_client.py:117-128 and src/jd_analyzer.py:9-24 (jd_analysis injection)
  found: "analyze_job_description extracts `technologies` (a list of tech names from the JD) and _build_messages prepends `<jd_analysis>\\ntechnologies: [...]` as the FIRST content of the user message. The system prompt contains zero mention of <jd_analysis> — no instruction on what it is or how to use it, and no warning that listed technologies absent from the resume must not be inserted."
  implication: "The model is handed an explicit, prominent list of JD technologies with no usage constraint, while persona/task framing ('maximize relevance and ATS alignment', 'understand precisely which keywords... hiring managers look for') actively pulls it toward weaving those exact names into bullets. This priming directly opposes the TECHNOLOGY FIDELITY rule."

- timestamp: 2026-06-12
  checked: src/guards.py (post-generation guard pipeline)
  found: "run_guards checks: missing \\header sections, markdown format violations, and hallucinated/missing employers. There is NO check comparing technology tokens in the tailored output against the base resume — fidelity rule PRMP-03 has no runtime enforcement."
  implication: "When the model violates fidelity, nothing detects, warns, or rejects. The anti-fabrication guarantee rests 100% on probabilistic prompt compliance from a local 14B model."

- timestamp: 2026-06-12
  checked: src/llm_client.py:27-107 (system prompt structure)
  found: "TECHNOLOGY FIDELITY sits at the tail of <CONSTRAINTS>, after a nine-item structural MUST NOT CHANGE list. Within <ALLOWED>, the only per-element fidelity reminder ('use only skills already present in the original') is attached to the Skills element (line 64); employer/project bullet items say only 'reword only — bullet count stays fixed' with no content-fidelity reminder at the rewrite site where fabrication actually happens."
  implication: "The fidelity constraint is single-sited and not reinforced at the bullet/tagline rewrite instructions — the exact elements the user reports as fabrication targets."

- timestamp: 2026-06-12
  checked: src/cli.py:52-61 (pipeline wiring)
  found: "Default flow always runs analyze_job_description and passes analysis into generate_tailored_resume, so the JD-technologies priming block is present on every normal run. run_guards runs after generation but, per above, cannot catch fabricated technologies."
  implication: "The priming pathway is in the default path, not an optional flag."

## Resolution

root_cause: >
  Anti-fabrication is enforced only by a soft prompt instruction (TECHNOLOGY FIDELITY,
  src/llm_client.py:87-93) whose effect is probabilistic and is actively undermined by three
  compounding factors: (1) the <jd_analysis> block prepends an unannotated list of JD
  technologies to the user message (src/llm_client.py:117-128), priming the model to insert
  exactly those names while the persona/task framing rewards keyword alignment; (2) the
  Ollama request sets no temperature/seed (src/llm_client.py:167 — options only num_ctx),
  so default sampling (~0.6-0.8) makes instruction compliance vary run-to-run, producing the
  intermittent failure; (3) guards.py has no technology-fidelity check, so violations pass
  through undetected with no warning or retry.
fix: ""
verification: ""
files_changed: []
