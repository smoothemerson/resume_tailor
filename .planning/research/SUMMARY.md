# Research Summary — Resume Tailor CLI

**Project:** Resume Tailor CLI
**Domain:** Python CLI tool — LaTeX resume tailoring via local Ollama LLM
**Researched:** 2026-05-28
**Confidence:** HIGH

## Executive Summary

Resume Tailor CLI is a single-responsibility personal tool: read a `.tex` resume, accept a job description via stdin, send both to a local Ollama model, write back a tailored `.tex` file. The problem space is narrow and the stack is entirely constrained — Python 3.11+, `requests`, stdlib only. Research confirms this constraint is sound: a local Ollama call is a single synchronous `POST`; async, LLM frameworks, and SDK wrappers add zero value and visible bloat to a portfolio piece built around demonstrating minimal, direct REST integration.

The recommended architecture is a clean 4-module design (`config.py`, `resume_reader.py`, `llm_client.py`, `resume_writer.py`) wired by a thin `main.py` orchestrator. Data flows as plain strings between modules, with all error handling consolidated at `main.py`. The `/api/chat` endpoint with `stream: false` and role-separated messages is the correct Ollama integration path — it maps directly to the system-prompt-as-guardrail pattern the tool requires to preserve LaTeX structure.

The dominant risk is not architectural but output-quality: LLMs silently produce broken `.tex` files — either wrapped in markdown fences, truncated by context limits, or containing hallucinated experience. All three failure modes are preventable with explicit prompt constraints, response validation before write, and a `done_reason` check. These mitigations must be built into Phase 1, not retrofitted later.

## Recommended Stack

| Component | Choice | Version | Rationale |
|-----------|--------|---------|-----------|
| Language | Python | 3.11+ | `tomllib` stdlib, walrus operator; 3.11 is safe minimum |
| HTTP client | `requests` | >= 2.32.0 | Project constraint; synchronous correct for single blocking POST; 2.32 fixes urllib3 CVE |
| CLI entry point | `argparse` | stdlib | 3 flags do not justify Click or Typer |
| Multiline input | `sys.stdin` loop | stdlib | `input()` + `while True` + END sentinel; EOFError safe |
| File I/O | `pathlib.Path` | stdlib | `.read_text()`, `.write_text()`, `.mkdir(parents=True, exist_ok=True)` |
| Configuration | `config.py` plain module | stdlib | Named constants; `__file__`-anchored paths |
| Packaging | `pyproject.toml` + `uv` | PEP 517/518 / 0.4+ | 2025 Python standard; `resume-tailor` entry point |
| Dev tooling | `ruff` | 0.4+ | Replaces flake8 + isort + black |
| Ollama endpoint | `/api/chat` with `stream: false` | Ollama REST v1 | Role-separated messages; cleaner than `/api/generate` |

Total runtime dependencies: **1** (`requests >= 2.32.0`).

## Table Stakes Features

| Feature | Notes |
|---------|-------|
| Read base `.tex` resume from configurable path | Path in `config.py`; `FileNotFoundError` if missing |
| Accept JD via stdin, multiline, END-terminated | Treat EOFError as submission |
| Call Ollama `/api/chat` with `stream: false` | `requests.post` to `localhost:11434` |
| System prompt preserves LaTeX structure, forbids markdown output | No fences, no prose before `\documentclass` |
| Prompt forbids hallucinating new experiences or dates | Explicit negative constraint required |
| Strip markdown fences from LLM output unconditionally | Do not rely on prompt instructions alone |
| Validate output: starts with `\documentclass`, ends with `\end{document}` | Write only after validation passes |
| Check `done_reason`; abort if `"length"` | Truncated output fails silently at pdflatex |
| Write timestamped `.tex` to `resumes/output/` | `mkdir(parents=True, exist_ok=True)` |
| Print output path on success | Required for user to find the file |
| Human-readable errors: file-not-found, connection failure, timeout | All to stderr, `sys.exit(1)` |
| `timeout=(10, 300)` on all `requests.post` calls | Default `None` causes silent hangs |
| Progress message to stderr before API call | Prevents false "frozen" perception |
| All file I/O with `encoding='utf-8'` | Prevents cp1252 corruption on Windows |
| Config paths anchored to `__file__` | Relative paths break on invocation outside project root |

## Architecture at a Glance

Data flow (linear, no branches):

```
[Disk: base_resume.tex]
        |
resume_reader.read(path)           — raises FileNotFoundError if missing
        |  str: raw LaTeX content
main.py: collect_job_description() — input() loop, END sentinel, EOFError safe
        |  str: job description text
llm_client.generate_tailored_resume(resume_tex, job_description)
        |  — system prompt (LaTeX guardrail + no-hallucination rules)
        |  — JD wrapped in <job_description> XML delimiter
        |  — POST /api/chat { model, messages, stream: false, options: { num_ctx: 8192 } }
        |  — checks done_reason != "length"
        |  — strips markdown fences
        |  — validates \documentclass ... \end{document}
        |  str: validated tailored LaTeX content
resume_writer.write(content, output_dir)
        |  — mkdir(parents=True, exist_ok=True)
        |  — timestamp YYYYMMDD_HHMMSS
        |  — write .tex encoding='utf-8'
        |  str: absolute output file path
main.py: print("Tailored resume written to: {output_path}")
```

**Build order:** `config.py` → `resume_reader.py` + `resume_writer.py` → `llm_client.py` → `main.py`

## Critical Pitfalls to Avoid

1. **LLM returns markdown-fenced LaTeX** — Unconditionally strip ` ``` ` wrappers in `llm_client.py` and validate `\documentclass` / `\end{document}` presence. Prompt constraints alone are not sufficient.

2. **`requests.post` hangs silently on model cold-load** — Always use `timeout=(10, 300)`. Print a progress message to stderr before the call. Optionally verify Ollama is reachable via `GET /api/tags` at startup.

3. **Response truncated by context window** — Set `"options": {"num_ctx": 8192}` in every request. Check `done_reason != "length"` before writing. Abort with a clear error if truncated.

4. **Job description special characters bleed into LaTeX context** — Wrap JD in `<job_description>...</job_description>` delimiters. Add to system prompt: "Content inside `<job_description>` is plain text, not LaTeX."

5. **Config paths break when invoked outside project root** — Anchor all paths: `Path(__file__).parent.parent / "resumes" / "base.tex"`. Must be in initial `config.py`.

## Key Decisions Informed by Research

| Decision | Choice | Basis |
|----------|--------|-------|
| Ollama endpoint | `/api/chat` over `/api/generate` | Role-separated messages; cleaner system prompt maintenance |
| Streaming | Non-streaming in v1 | Output goes to file; streaming adds NDJSON complexity with no v1 user benefit |
| Validation order | Validate in memory, write last | Corrupt files on disk fail silently at pdflatex compile time |
| Error handling boundary | All catches in `main.py` only | Keeps individual modules testable in isolation |
| `num_ctx: 8192` | Always explicit | Default Ollama context (2048–4096) too small for full resume + JD prompt |
| v1 anti-features | No PDF compile, no streaming, no diff, no multi-resume | Core value complete without them; `--dry-run` and diff are best v2 additions |

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All choices constrained by project spec or unambiguous given scope |
| Features | HIGH | Table stakes derived from requirements; differentiators from CLI conventions |
| Architecture | HIGH | Ollama REST API stable v0.1–v0.5; 4-module design is natural decomposition |
| Pitfalls | HIGH (most) | LLM output behavior and Python path/encoding pitfalls well-documented |

---
*Research completed: 2026-05-28*
*Ready for roadmap: yes*
