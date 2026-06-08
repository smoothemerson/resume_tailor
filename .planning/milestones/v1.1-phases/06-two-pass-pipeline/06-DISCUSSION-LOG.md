# Phase 06: Two-Pass Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-05
**Phase:** 06-Two-Pass Pipeline
**Areas discussed:** Analysis output format, Progress messaging

---

## Analysis Output Format

### Q1: What should pass-1 return from the LLM?

| Option | Description | Selected |
|--------|-------------|----------|
| Structured JSON dict | JSON with keys like technologies[], requirements[], emphasis_areas[]. Phase 7 gets a ready-made keyword list. | ✓ |
| Plain text bullet list | Simpler prompt, but Phase 7 would need to regex-parse the text. More fragile. | |
| Freeform — let the model decide | No output format constraint. Phase 7 would need to re-run analysis or parse loosely. | |

**User's choice:** Structured JSON dict
**Notes:** None — recommended option selected.

---

### Q2: What keys should the JSON dict have?

| Option | Description | Selected |
|--------|-------------|----------|
| Exactly as ROADMAP: technologies, requirements, emphasis_areas | Three keys map 1:1 to what the roadmap specifies. Phase 7 knows exactly where to find keywords. | ✓ |
| Add a 4th key: keywords (flat merged list) | Adds a 'keywords' flat list for Phase 7 direct consumption. | |
| Slim it to just a flat keywords list | Single array, simpler but loses subcategory structure. | |

**User's choice:** Exactly as ROADMAP: technologies, requirements, emphasis_areas
**Notes:** None — recommended option selected.

---

### Q3: What does the analysis function return when JSON parsing fails (PIPE-03 fallback)?

| Option | Description | Selected |
|--------|-------------|----------|
| None | Return None on parse failure. Caller checks `if analysis is not None:`. Clean and explicit. | ✓ |
| Empty dict {} | Return {} on parse failure. Slightly more ambiguous — could mean 'parsed but empty' vs 'failed'. | |
| You decide | Leave to the planner — either works fine as long as fallback is consistent with PIPE-03. | |

**User's choice:** None
**Notes:** None — recommended option selected.

---

## Progress Messaging

### Q1: What does the user see before each LLM call?

| Option | Description | Selected |
|--------|-------------|----------|
| Two separate messages | "Analyzing job description..." before pass 1, then "Tailoring resume — this may take a minute..." before pass 2. | ✓ |
| Single combined message | "Analyzing and tailoring resume — this may take a minute..." before both calls start. | |
| You decide | Leave phrasing to the planner as long as both LLM calls are distinguishable. | |

**User's choice:** Two separate messages
**Notes:** None — recommended option selected.

---

### Q2: Exact wording for the pass-1 progress message?

| Option | Description | Selected |
|--------|-------------|----------|
| "Analyzing job description..." | Short and descriptive — consistent with existing message style. | ✓ |
| "Extracting requirements from job description..." | More explicit but slightly verbose. | |
| You decide | Leave exact wording to the planner as long as it's clearly distinct from the tailoring message. | |

**User's choice:** "Analyzing job description..."
**Notes:** None — recommended option selected.

---

### Q3: When fallback triggers, does the user see anything?

| Option | Description | Selected |
|--------|-------------|----------|
| Fully silent — user sees nothing | Tool behaves exactly as if single-pass was always the plan. Consistent with PIPE-03 and GUARD-04. | ✓ |
| Silent warning to stderr | Print fallback notice to stderr. More transparent but breaks PIPE-03's "no error surfaced" wording. | |
| You decide | Leave to the planner, as long as it's consistent with PIPE-03. | |

**User's choice:** Fully silent — user sees nothing
**Notes:** None — recommended option selected.

---

## Claude's Discretion

- **Injection placement:** How the `{technologies, requirements, emphasis_areas}` dict is formatted and embedded in the tailoring prompt (new XML tag in user message, or new section in system prompt) — left to planner.
- **Module location:** New `jd_analyzer.py` vs inside `llm_client.py` — left to planner.
- **Analysis system prompt persona and exact extraction prompt wording** — left to planner/implementer.

## Deferred Ideas

None — discussion stayed within phase scope.
