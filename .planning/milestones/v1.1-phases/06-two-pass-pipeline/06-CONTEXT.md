# Phase 06: Two-Pass Pipeline - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the LLM pipeline so a JD analysis call (pass 1) runs before the tailoring call (pass 2). Pass 1 extracts key technologies, role requirements, and emphasis areas from the job description and returns them as a structured JSON dict. That dict is then injected into the tailoring prompt (pass 2) to guide section-specific rewrites. When pass 1 fails for any reason (LLM error, JSON parse failure), the tool falls back silently to single-pass behavior — the user experience is unchanged.

Requirements: PIPE-01, PIPE-02, PIPE-03, PIPE-04.

</domain>

<decisions>
## Implementation Decisions

### Analysis Output Format (PIPE-01, PIPE-02)
- **D-01:** Pass-1 returns a structured JSON dict with exactly three keys: `technologies` (list), `requirements` (list), `emphasis_areas` (list). No additional keys. This maps 1:1 to ROADMAP's specified extraction targets and gives Phase 7 a ready-made keyword structure with no additional parsing.
- **D-02:** When pass-1 JSON parsing fails (including LLM errors, malformed JSON, missing keys), the analysis function returns `None`. The caller (`cli.py`) checks `if analysis is not None:` before injecting. `None` is unambiguous — it cannot be confused with an empty-but-valid response.

### Progress Messaging (PIPE-01)
- **D-03:** Two separate progress messages, one per LLM call:
  - Before pass 1: `"Analyzing job description..."` (printed with `flush=True`)
  - Before pass 2: existing `"Tailoring resume — this may take a minute..."` (unchanged)
  - This satisfies the ROADMAP success criterion that both calls are "visible via progress messages."
- **D-04:** When the pass-1 fallback triggers (analysis returned `None`), the tool is fully silent — no warning, no stderr message. Tool proceeds directly to the existing tailoring call. This is consistent with PIPE-03's "no abort, no error surfaced to user" and mirrors the guards' advisory-only pattern (GUARD-04).

### Fallback Behavior (PIPE-03, PIPE-04)
- **D-05:** Carries forward from prior phases — pass-1 failure falls back silently to single-pass. Both LLM calls respect the existing `done_reason: length` truncation guard with no new error handling paths.

### Claude's Discretion
- Injection placement: how the `{technologies, requirements, emphasis_areas}` dict is formatted and embedded in the tailoring prompt (new XML tag in the user message, or new section in the system prompt) is left to the planner. Both work — choose the approach most consistent with existing prompt structure.
- Module location for the JD analysis function: new `jd_analyzer.py` module (consistent with single-concern pattern) or inside `llm_client.py` alongside `generate_tailored_resume()` (both are LLM calls, tightly coupled). Planner decides.
- Analysis system prompt persona and exact extraction prompt wording are left to the planner/implementer.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/ROADMAP.md` §Phase 6 — Goal, success criteria, requirements list (PIPE-01 to PIPE-04)
- `.planning/REQUIREMENTS.md` §Two-Pass Pipeline — Full requirement text for PIPE-01, PIPE-02, PIPE-03, PIPE-04

### Source Files (must read before planning)
- `src/llm_client.py` — Core integration point: `generate_tailored_resume()`, `_build_messages()`, `TailorResult` NamedTuple, existing truncation guard (`done_reason: length`). Pass-1 analysis function and pass-2 injection both connect here.
- `src/cli.py` — Orchestration point: progress messages are printed here; analysis result is passed from pass-1 to pass-2 call here; fallback logic (`if analysis is not None:`) lives here.
- `src/guards.py` — Pattern reference for single-concern module with one public entry point; `jd_analyzer.py` (if created) follows this structure.
- `src/diff_view.py` — Pattern reference for a module that is called from `cli.py` and never raises.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generate_tailored_resume(resume_text, job_description, model)` in `llm_client.py` — existing LLM call pattern; pass-1 analysis call follows same structure (POST to `/api/chat`, `stream: False`, truncation guard)
- `_check_ollama_health()` in `llm_client.py` — already called once in `generate_tailored_resume()`; pass-1 does NOT need a second health check (health was verified at the start of the single call)
- `TailorResult` NamedTuple — established pattern for returning structured data from LLM calls; a similar structure or a plain dict is appropriate for the analysis result
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `TIMEOUT` in `config.py` — both LLM calls use these same config values

### Established Patterns
- **raise-not-exit**: `llm_client.py` raises `RuntimeError`/`ValueError`; only `cli.py` calls `sys.exit`. Analysis function follows the same rule.
- **Single-concern modules**: `guards.py`, `diff_view.py`, `resume_reader.py` each export one public entry point. A `jd_analyzer.py` module would fit this pattern.
- **Non-fatal fallback**: Guards wrap body in `try/except Exception` so `run_guards()` never raises. Analysis fallback follows same philosophy — `None` return instead of raise.
- **flush=True on progress**: `print("Tailoring resume...", flush=True)` in `cli.py`. New progress messages follow the same convention.
- **No new dependencies**: Both passes use stdlib + `requests` only. JSON parsing uses stdlib `json` module.

### Integration Points
- `cli.py` `main()` — new flow between `read_resume()` and `generate_tailored_resume()`:
  1. `print("Analyzing job description...", flush=True)` — new pass-1 progress message
  2. `analysis = analyze_job_description(job_description, model=args.model)` — new pass-1 call (returns `dict | None`)
  3. `print("Tailoring resume — this may take a minute...", flush=True)` — existing message, now for pass 2
  4. `result = generate_tailored_resume(resume_text, job_description, analysis=analysis, model=args.model)` — pass-2 call with injected analysis (or `None`)
- `generate_tailored_resume()` in `llm_client.py` — signature extends to accept optional `analysis: dict | None = None`; `_build_messages()` conditionally includes analysis content when analysis is not None
- Health check runs once (inside `generate_tailored_resume()` or extracted to a shared call) — not twice

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard approaches for JSON prompt extraction and injection.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-Two-Pass Pipeline*
*Context gathered: 2026-06-05*
