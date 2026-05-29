# Phase 3: CLI Wiring - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

`cli.py` — the full orchestration flow implemented directly in `main()`: read resume → collect multiline job description → print progress message → call `generate_tailored_resume()` → write output → print success path. No new modules. Phase is complete when running `resume-tailor` end-to-end produces a tailored `.tex` file.

</domain>

<decisions>
## Implementation Decisions

### Orchestration Location
- **D-01:** The full flow lives **inside `cli.py:main()` directly** — no separate `main.py` module. This is the correct scale for a single-command tool; the Phase 2 CONTEXT.md references to "main.py" are superseded by this decision.
- **D-02:** Exception catching uses a **single broad `try/except` block** wrapping `read_resume()` + `generate_tailored_resume()` + `write_resume()`. Catches `RuntimeError` and `ValueError` raised by `llm_client.py`. No per-call granularity needed for a 3-step linear flow.
- **D-03:** Error messages at the CLI boundary use **`print(..., file=sys.stderr)`** — not `log_manager`. `cli.py` is the human-facing boundary; internal `log_manager` usage stays inside the domain modules (`resume_reader.py`, `llm_client.py`).

### Input UX
- **D-04:** On startup, print a **short instructions banner** to stdout before reading input:
  ```
  Resume Tailor
  Paste the job description below. Type END on a new line to submit.

  >
  ```
  The `>` prompt stays on the same line — user types after it for the first line, then continues on new lines.
- **D-05:** Input is collected with a **`while True` loop using `input()`**, accumulating lines until the user types `END` on a new line. `EOFError` (Ctrl+D) is caught and treated as submission — no error, just submits what was collected.
- **D-06:** Banner and prompt print to **stdout**. Error messages print to **stderr**.

### CLI Flags
- **D-07:** **No new flags added in Phase 3.** `argparse` stays in `cli.py` for `--help` only. All config (model, paths) comes from `config.py` constants. `--dry-run` and other v2 flags are deferred.

### Progress Message
- **D-08:** Print a progress message to stdout **after** job description submission and **before** the `generate_tailored_resume()` call, so the terminal does not appear frozen during LLM inference. Exact wording is Claude's discretion (see below).

### Claude's Discretion
- Exact wording of the progress message (e.g., "Tailoring resume..." or "Calling Ollama — this may take a minute...")
- Whether to flush stdout after the progress message (`print(..., flush=True)`) — recommended since Ollama can take up to 300s
- The exact `except` clause types: `except (RuntimeError, ValueError) as e` is sufficient; whether to also catch `Exception` as a fallback is Claude's call

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Scope
- `.planning/REQUIREMENTS.md` — Phase 3 requirements: CORE-02 (multiline JD input), CORE-03 (progress message), CORE-06 (success message with path); traceability table maps each to this phase
- `.planning/PROJECT.md` — constraints (stdlib + requests only, no logging module at CLI boundary), out-of-scope list

### Roadmap & Success Criteria
- `.planning/ROADMAP.md` §"Phase 3: CLI Wiring" — 3 success criteria that must all be TRUE before phase is complete

### Existing Source Files
- `src/cli.py` — current stub (argparse + empty main()); Phase 3 fills this in
- `src/config.py` — `BASE_RESUME_PATH`, `OUTPUT_DIR`, `OLLAMA_MODEL` constants; cli.py reads these for display/defaults
- `src/resume_reader.py` — `read_resume(path: Path) -> str`; raises nothing (uses sys.exit directly) — no catch needed for reader errors in the try block
- `src/llm_client.py` — `generate_tailored_resume(resume_text: str, job_description: str) -> str`; raises `RuntimeError` and `ValueError` on failure
- `src/resume_writer.py` — `write_resume(content: str, output_dir: Path) -> Path`; returns the output `Path` — cli.py uses this path in the success message

### Prior Phase Decisions
- `.planning/phases/02-llm-integration/02-CONTEXT.md` — D-06: `generate_tailored_resume()` returns validated LaTeX string only; D-07: health check is inside that function, not a separate call from cli.py

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/resume_reader.py`: `read_resume(path: Path) -> str` — call with `BASE_RESUME_PATH` from config
- `src/llm_client.py`: `generate_tailored_resume(resume_text, job_description)` — single call, health check included
- `src/resume_writer.py`: `write_resume(content, output_dir) -> Path` — returns the written file path; use `.resolve()` for the absolute path in the success message
- `src/config.py`: `BASE_RESUME_PATH`, `OUTPUT_DIR` — pass directly to reader/writer

### Established Patterns
- `resume_reader.py` uses `sys.exit(1)` directly on error (not raise) — it will exit before returning to the try block in `cli.py`; no need to catch reader errors separately
- `llm_client.py` uses `log_manager` internally; `cli.py` does NOT import log_manager
- All imports from `src/` flat layout: `from resume_reader import read_resume`, `from llm_client import generate_tailored_resume`, `from resume_writer import write_resume`, `from config import BASE_RESUME_PATH, OUTPUT_DIR`

### Integration Points
- `cli.py:main()` is the sole orchestrator: calls reader → collects JD → prints progress → calls LLM → calls writer → prints success path
- `write_resume()` returns the output `Path` — use `str(output_path.resolve())` for the absolute path in CORE-06

</code_context>

<specifics>
## Specific Ideas

- Banner text (D-04):
  ```
  Resume Tailor
  Paste the job description below. Type END on a new line to submit.

  >
  ```
  The `>` on its own line acts as the visual input prompt — user starts typing after it.
- Input loop: accumulate lines into a list, then `"\n".join(lines)` to produce the job description string
- Success message should print the **absolute** path (not relative), e.g.: `Tailored resume written to: /home/user/project/resumes/output/tailored_resume_20260529_143022.tex`
- `sys.exit(0)` is implicit on clean return from `main()`; `sys.exit(1)` called in the except block

</specifics>

<deferred>
## Deferred Ideas

- `--dry-run` flag (print prompt without calling Ollama) — listed in REQUIREMENTS.md v2 deferred
- `--model` / `--resume` CLI overrides — not in v1 REQUIREMENTS; deferred to future phase
- Diff output (base vs tailored resume) — REQUIREMENTS.md v2 deferred
- Streaming token output — REQUIREMENTS.md v2 deferred

</deferred>

---

*Phase: 3-CLI Wiring*
*Context gathered: 2026-05-29*
