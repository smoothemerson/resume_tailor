# Phase 3: CLI Wiring - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-29
**Phase:** 3-CLI Wiring
**Areas discussed:** Orchestration location, Input UX, CLI flags

---

## Orchestration Location

| Option | Description | Selected |
|--------|-------------|----------|
| Inside cli.py directly | Full flow in main(); correct scale for a single-command tool | ✓ |
| Separate main.py called from cli.py | cli.py stays thin, orchestration in main.py; consistent with Phase 2 CONTEXT.md refs but adds indirection | |

**User's choice:** Inside cli.py directly

| Option | Description | Selected |
|--------|-------------|----------|
| Broad try/except around the whole flow | One block wraps read_resume + generate_tailored_resume + write_resume | ✓ |
| Targeted catches per call | Separate except clauses per function; more verbose | |

**User's choice:** Broad try/except around the whole flow

| Option | Description | Selected |
|--------|-------------|----------|
| Plain print() to stderr | Direct print at CLI boundary; distinct from internal log_manager usage | ✓ |
| Use log_manager like other modules | Consistent with resume_reader.py and llm_client.py pattern | |

**User's choice:** Plain print() to stderr
**Notes:** cli.py is the human-facing boundary — keeping it distinct from internal module logging matches CLAUDE.md intent.

---

## Input UX

| Option | Description | Selected |
|--------|-------------|----------|
| Short instructions banner | 2-3 line header: tool name, what it does, how to submit | ✓ |
| Bare inline prompt | Single prompt line, no preamble | |
| Silent (no prompt text) | Tool reads stdin immediately with no instructions | |

**User's choice:** Short instructions banner
**Notes:** Banner text: `Resume Tailor\nPaste the job description below. Type END on a new line to submit.\n\n>`

| Option | Description | Selected |
|--------|-------------|----------|
| stdout | Standard for interactive CLI prompts | ✓ |
| stderr | Used when output is meant to be piped | |

**User's choice:** stdout

| Option | Description | Selected |
|--------|-------------|----------|
| while loop with input() + END sentinel | Matches CORE-02 spec; EOFError treated as submission | ✓ |
| sys.stdin.read() | Simpler code but breaks the END-on-new-line UX | |

**User's choice:** while loop with input() + END sentinel

---

## CLI Flags

| Option | Description | Selected |
|--------|-------------|----------|
| Config-only for v1 | No --model or --resume flags; users edit config.py | ✓ |
| Add --model and --resume overrides | Runtime overrides for config.py values; not in REQUIREMENTS.md | |
| Add --resume only | Single override flag; still unplanned scope for Phase 3 | |

**User's choice:** Config-only for v1

| Option | Description | Selected |
|--------|-------------|----------|
| Keep argparse, no flags added | argparse stays for --help; easy to add flags in v2 | ✓ |
| Remove argparse entirely | Simpler, but loses auto-generated --help | |

**User's choice:** Keep argparse, no flags added
**Notes:** --dry-run and other v2 flags stay deferred per REQUIREMENTS.md.

---

## Claude's Discretion

- Exact wording of the progress message
- Whether to flush stdout after the progress message (recommended given 300s timeout)
- Exact exception types in the except clause (RuntimeError + ValueError sufficient; broader Exception catch is optional)

## Deferred Ideas

- `--dry-run` flag — print the constructed LLM input without calling Ollama (REQUIREMENTS.md v2 deferred)
- `--model` / `--resume` CLI overrides — not in v1 requirements
- Diff output (base vs tailored resume) — REQUIREMENTS.md v2 deferred
- Streaming token output — REQUIREMENTS.md v2 deferred
