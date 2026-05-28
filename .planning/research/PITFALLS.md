# Domain Pitfalls

**Domain:** Python CLI tool — local Ollama LLM — LaTeX resume output
**Researched:** 2026-05-28
**Confidence:** HIGH (domain-specific, drawn from Ollama API behavior, Python requests library, LaTeX encoding, and CLI input-handling patterns)

---

## Critical Pitfalls

### Pitfall 1: LLM Returns Markdown-Fenced LaTeX Instead of Raw `.tex`

**Severity:** CRITICAL — output is silently broken

**What goes wrong:**
Models like mistral and llama3 default to "helpful" markdown formatting. Even with instructions like "return only LaTeX", they routinely wrap output in triple-backtick fences:

```
```latex
\documentclass{article}
...
```
```

If the tool writes this directly to a `.tex` file, `pdflatex` fails with cryptic parse errors. The bug is invisible at write-time — it only surfaces when the user tries to compile.

**Why it happens:**
Instruction-tuned models are trained on markdown-heavy data. "Return only LaTeX" is interpreted as a style hint, not a hard format constraint. Without a parsing/stripping layer, the guardrail has no teeth.

**Warning signs:**
- First-run test produces a `.tex` file that fails to compile
- Output file starts with ` ```latex ` or contains ` ``` ` anywhere
- Model returns a preamble explanation before `\documentclass`

**Prevention:**
1. In the system prompt, use explicit negative constraints: "Do NOT wrap output in markdown code fences. Do NOT include any text before `\documentclass` or after the final `\end{document}`."
2. Add a post-processing strip function regardless of the prompt: scan for ` ```...``` ` wrapper and remove it before writing to disk.
3. Add a minimal output validator: check that the response starts with `\documentclass` (after stripping whitespace) and contains `\end{document}`.

**Phase:** Phase 1 (core LLM call). Strip function must be present before any output is written.

---

### Pitfall 2: Ollama `requests` Call Hangs Silently on Model Load

**Severity:** CRITICAL — looks like a hang to the user, no feedback

**What goes wrong:**
When the target model is not already loaded in Ollama's memory, the first call triggers a model load that can take 15-90 seconds for 7B+ parameter models. The `requests.post()` call blocks with no output, no progress indicator, and no timeout by default. If `timeout=` is not set, the call hangs indefinitely. If it IS set too short (e.g. 30s), the request raises `requests.exceptions.Timeout` before generation even starts.

**Why it happens:**
Ollama loads models lazily on first use. The HTTP connection stays open during load. `requests` default timeout is `None` — no timeout. Developers test on warm models and never hit the cold-load case.

**Warning signs:**
- Script appears frozen after "Calling model..." with no output
- The behavior is only reproducible on first run after machine restart
- Log shows request was sent but no response for 60+ seconds

**Prevention:**
1. Set a generous `timeout` on the `requests.post()` call. For generation, use a tuple: `timeout=(10, 300)` — 10 seconds to connect, 300 seconds to receive. This prevents silent hangs while allowing slow generation.
2. Print a progress message immediately before the API call: "Calling Ollama (this may take a minute on first run)..."
3. Separately, use the `/api/tags` endpoint with a short timeout at startup to confirm Ollama is reachable before sending the full prompt. Fail fast with a clear error rather than hanging.

**Phase:** Phase 1 (Ollama API integration). Timeout tuple and startup check must be in the initial implementation.

---

### Pitfall 3: Response Truncation Due to `num_predict` Default

**Severity:** CRITICAL — output is a partial `.tex` file

**What goes wrong:**
Ollama's `/api/generate` has a default `num_predict` of -1 (unlimited) in some versions, but the effective context window interacts with `num_ctx`. If the base resume is long (300+ lines) and the generated output is similarly long, the response can be silently cut off mid-document. The file is written but ends at line 200, and `pdflatex` fails with "unexpected end of file."

The non-streaming response returns a `done_reason` field. If `done_reason` is `"length"` rather than `"stop"`, the generation was truncated by the context limit.

**Why it happens:**
A full LaTeX resume sent as input + a full tailored resume as output can easily exceed 4096 tokens. The default `num_ctx` for many Ollama models is 2048 or 4096. The prompt alone may consume most of the context window, leaving insufficient space for the full output.

**Warning signs:**
- Output `.tex` file ends mid-command or mid-environment
- `pdflatex` reports "unexpected end of file" or "missing \end{document}"
- `done_reason: "length"` in the API response

**Prevention:**
1. Always check `response_json["done_reason"]`. If it equals `"length"`, raise an explicit error: "Output truncated by context limit. Try a shorter job description or a model with larger context."
2. Set `num_ctx` explicitly in the request options to 8192 or higher if the model supports it. Pass `"options": {"num_ctx": 8192}` in the request body.
3. Add a post-write validator: check that the last non-whitespace characters of the written file are `\end{document}`. If not, delete the file and abort with a clear error message.

**Phase:** Phase 1 (LLM call) + Phase 2 (output validation).

---

### Pitfall 4: Special Characters in Job Description Breaking the LaTeX Prompt

**Severity:** HIGH — causes prompt injection into LaTeX context or malformed output

**What goes wrong:**
Job descriptions routinely contain characters that are LaTeX control characters: `%`, `&`, `$`, `_`, `^`, `#`, `{`, `}`, `~`, `\`. When the job description is interpolated directly into the prompt, the model may interpret these as LaTeX commands and "correct" them in ways that corrupt the output resume.

A job description saying "Salary: $150K" or "skills: Python/C++ & ML" causes the model to either misinterpret the context or hallucinate LaTeX escaping where it should not.

**Why it happens:**
The prompt mixes two contexts: the job description (plain text) and the LaTeX document (structured markup). Without clear delimiters, the model conflates them.

**Warning signs:**
- Output resume has escaped characters (`\$`, `\%`) in unexpected places
- Bullets hallucinate content that paraphrases the salary or benefit lines from the JD
- Model starts "fixing" LaTeX in the job description section

**Prevention:**
1. Wrap the job description in the prompt with an explicit "NOT LaTeX" delimiter:

```
<job_description>
{job_description_text}
</job_description>

This is PLAIN TEXT. Do not interpret it as LaTeX. Use it only to understand the role requirements.
```

2. Do NOT escape special characters in the job description before sending — the model should receive it verbatim inside its plaintext container. Escaping can garble meaning.
3. Add a note in the system prompt: "The job description above may contain characters like $, %, &. These are plain text, not LaTeX commands."

**Phase:** Phase 1 (prompt engineering). Must be part of the initial prompt design.

---

### Pitfall 5: Non-Streaming Call Blocks With No User Feedback

**Severity:** HIGH — poor UX; user cannot tell if the tool is working or hung

**What goes wrong:**
Using `stream: false` (non-streaming) with Ollama means the HTTP response is not received until generation is fully complete. For a full resume, this is 30-120 seconds. During this time, the CLI shows no output. Users will kill the process assuming it is frozen, especially on first run.

**Why it happens:**
Non-streaming is simpler to implement (one `response.json()` call), so it is chosen first. The latency only becomes apparent with real inputs.

**Warning signs:**
- User reports the tool "freezes"
- CI or test runs time out because tests don't account for LLM latency
- Team assumes the tool is broken because no output appears for 60 seconds

**Prevention:**
1. Use streaming (`stream: true`) and print a progress indicator (dots, spinner, or token counter) to stderr during generation. This is not significantly more complex with `requests` — iterate over `response.iter_lines()`, decode each NDJSON chunk, and print a dot per chunk.
2. Alternatively: use non-streaming but print a "Generating resume, please wait..." message with elapsed seconds before the call, and suppress the terminal cursor to signal active work.
3. For a portfolio tool, streaming with visible output is the right choice — it also lets the user see the output being generated and abort early if the model is clearly going wrong.

**Phase:** Phase 1 (Ollama integration). Decide streaming vs non-streaming at this phase and stick to it.

---

## Moderate Pitfalls

### Pitfall 6: `requests` Default Behavior with NDJSON Streaming

**What goes wrong:**
Ollama's streaming endpoint returns newline-delimited JSON (NDJSON). Each line is a JSON object: `{"response": "token", "done": false}`. Using `response.text` or `response.json()` on a streaming response returns garbled or empty output. `response.iter_lines()` is required, and each line must be `json.loads()`-decoded individually. Additionally, the final line contains generation stats, not a token — it has `"done": true` and must be handled separately.

**Prevention:**
Use `response.iter_lines(decode_unicode=True)`, skip empty lines, `json.loads()` each, accumulate the `"response"` field when `done == false`, and stop when `done == true`. Never call `response.json()` on a streaming response.

**Phase:** Phase 1.

---

### Pitfall 7: LaTeX Source File Read as Wrong Encoding

**What goes wrong:**
The base `.tex` file may contain UTF-8 characters (em dashes, curly quotes, accented characters in names). Reading it with `open(path, 'r')` on Windows defaults to the system locale encoding (often cp1252), corrupting the file content before it reaches the prompt. The model then sees garbled text and may "correct" the encoding in ways that break the LaTeX.

**Prevention:**
Always read and write `.tex` files with explicit `encoding='utf-8'`: `open(path, 'r', encoding='utf-8')`. Apply this to both reading the base resume and writing the output file.

**Phase:** Phase 1 (file I/O). Must be in the initial implementation.

---

### Pitfall 8: Multiline Job Description Input Termination is Ambiguous

**What goes wrong:**
Using `input()` in a loop with an "END" terminator works on a happy path but fails in two real-world scenarios: (1) the user pastes a job description that contains a line reading "END" (rare but possible), and (2) the user sends EOF (Ctrl+D on Unix, Ctrl+Z on Windows) which raises `EOFError` and crashes instead of treating it as submission.

**Prevention:**
1. Use a sentinel that is clearly unambiguous — e.g., a blank line followed by "END", or use `sys.stdin` to detect EOF gracefully. Wrap the input loop in a `try/except EOFError` and treat EOF as submission, not an error.
2. Document the terminator clearly in the CLI prompt string: `"Enter job description (type END on a new line to submit, or Ctrl+D to finish):"`.

**Phase:** Phase 1 (CLI input handling).

---

### Pitfall 9: Output Directory Not Created Automatically

**What goes wrong:**
The output path `resumes/output/tailored_resume_YYYYMMDD_HHMMSS.tex` requires the `resumes/output/` directory to exist. If it does not, `open(path, 'w')` raises `FileNotFoundError`. This is a one-line fix but it surfaces as a confusing error message on first run for anyone who clones the repo.

**Prevention:**
Use `pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)` before opening the output file. This should be in the file-writing function, not in setup docs.

**Phase:** Phase 1 (file output).

---

### Pitfall 10: `config.py` Using Relative Paths Breaks When CLI is Run From a Different Directory

**What goes wrong:**
If `config.py` defines `BASE_RESUME_PATH = "resume.tex"` or `BASE_RESUME_PATH = "resumes/base.tex"` as a bare relative string, the path is resolved relative to the shell's current working directory at invocation time — not relative to the project root. Running `python src/main.py` from `/home/user/` instead of the project root silently reads the wrong file (or raises FileNotFoundError with a confusing path).

**Prevention:**
Anchor all paths to the project root using `__file__`:

```python
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
BASE_RESUME_PATH = PROJECT_ROOT / "resumes" / "base.tex"
```

This resolves correctly regardless of where the user invokes the script.

**Phase:** Phase 1 (config setup). Must be in initial `config.py`.

---

### Pitfall 11: LLM Hallucinating Work Experience or Dates

**What goes wrong:**
Even with a strict system prompt, instruction-tuned models sometimes add experience lines, adjust dates, change company names, or add skills that were not in the base resume. The output is syntactically valid LaTeX but factually wrong. This is the highest-risk output quality issue for a resume tool.

**Why it happens:**
Models are trained to be helpful and "fill gaps." If the job description asks for 5 years of Kubernetes experience and the base resume shows none, the model may add it. The system prompt says not to hallucinate, but prompt-level guardrails are probabilistic, not deterministic.

**Prevention:**
1. The system prompt must be explicit and specific: "You MUST NOT add any work experience, company names, job titles, dates, or skills that do not appear in the original resume. Rewrite bullets for emphasis, not invention. If the job requires a skill not in the resume, do not add it."
2. At minimum, the tool should print a diff-style summary or direct the user to compare the output: "Review the output carefully before using: tailored resumes can contain hallucinated content."
3. Long-term: a diff check between base and output (deferred per PROJECT.md Out of Scope) would catch this.

**Phase:** Phase 1 (prompt engineering) + Phase 2 (output review UX).

---

### Pitfall 12: Prompt Size Exceeding Context Window With Long Job Descriptions

**What goes wrong:**
The prompt combines: system instruction (300-500 tokens) + base resume (500-1500 tokens for a full .tex file) + job description (200-2000 tokens for a verbose JD). At the upper end, this can push 4000 tokens of input. On a 4096-token context model, there is almost no room for output. The model either truncates mid-resume or produces a very abbreviated output without warning.

**Prevention:**
1. Measure prompt size before sending. Use a rough token estimate: `len(prompt.split()) * 1.3` as a heuristic. Warn if estimated total exceeds 3000 tokens.
2. Set `num_ctx` to 8192 in the request options and document the minimum recommended model context size.
3. Guide users in the README: prefer models with 8k+ context (llama3.1, mistral-nemo) over base 4k models.

**Phase:** Phase 1 (API call construction).

---

## Minor Pitfalls

### Pitfall 13: Ollama Connection Error Message Is Cryptic

**What goes wrong:**
If Ollama is not running, `requests.post()` raises `requests.exceptions.ConnectionError` with a message like `HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded`. This is confusing to non-developers.

**Prevention:**
Catch `requests.exceptions.ConnectionError` explicitly and re-raise with a human-readable message: `"Ollama is not running. Start it with: ollama serve"`.

**Phase:** Phase 1 (error handling).

---

### Pitfall 14: Writing Output File Before Validating LLM Response

**What goes wrong:**
If the file is written immediately after receiving the response — before checking for truncation, markdown fences, or missing `\end{document}` — then a corrupt file exists on disk. If the user immediately runs `pdflatex` on it, they get compile errors and may not realize the LLM output was the problem.

**Prevention:**
Validate in memory first. Write to disk only after all checks pass. If validation fails, print the error and exit without writing.

**Phase:** Phase 1 (output pipeline).

---

### Pitfall 15: Model Name Mismatch Causing Silent Failure

**What goes wrong:**
If `config.py` specifies `MODEL = "mistral"` but the installed Ollama model is named `"mistral:latest"` or `"mistral:7b-instruct"`, Ollama returns a 404-style error in the response body (not always a non-200 HTTP status). The tool may not check the HTTP status code and treats the error body as a valid response, writing garbage to disk.

**Prevention:**
Always check `response.raise_for_status()` before reading the response body. Also check that the response JSON contains a `"response"` key — if it contains `"error"`, surface that message explicitly.

**Phase:** Phase 1 (API call + error handling).

---

## Phase Mapping

| Phase Topic | Likely Pitfall | Mitigation | Priority |
|-------------|---------------|------------|----------|
| First LLM call implementation | Pitfall 2 (timeout hang) | Timeout tuple `(10, 300)`, startup health check | Must-have in Phase 1 |
| First LLM call implementation | Pitfall 5 (no feedback) | Progress output to stderr before/during call | Must-have in Phase 1 |
| Prompt engineering | Pitfall 1 (markdown fences) | Strip function + output validator | Must-have in Phase 1 |
| Prompt engineering | Pitfall 4 (special char injection) | XML-style delimiter around JD in prompt | Must-have in Phase 1 |
| Prompt engineering | Pitfall 11 (hallucination) | Explicit negative constraints in system prompt | Must-have in Phase 1 |
| API call construction | Pitfall 3 (truncation) | Check `done_reason`, set `num_ctx: 8192` | Must-have in Phase 1 |
| API call construction | Pitfall 12 (context overflow) | Token estimation + warning | Should-have in Phase 1 |
| Streaming implementation | Pitfall 6 (NDJSON handling) | `iter_lines()` + per-line `json.loads()` | Must-have if streaming |
| File I/O | Pitfall 7 (encoding) | `encoding='utf-8'` on all file ops | Must-have in Phase 1 |
| File I/O | Pitfall 9 (missing directory) | `mkdir(parents=True, exist_ok=True)` | Must-have in Phase 1 |
| File I/O | Pitfall 14 (write before validate) | Validate in memory, write last | Must-have in Phase 1 |
| Config setup | Pitfall 10 (relative paths) | Anchor paths to `__file__` in config.py | Must-have in Phase 1 |
| CLI input | Pitfall 8 (multiline terminator) | EOFError handling, clear docs | Should-have in Phase 1 |
| Error handling | Pitfall 13 (connection error) | Catch + human-readable message | Must-have in Phase 1 |
| Error handling | Pitfall 15 (model name mismatch) | `raise_for_status()` + check for `"error"` key | Must-have in Phase 1 |
| Output review (Phase 2) | Pitfall 11 (hallucination) | Diff display or explicit review prompt | Should-have in Phase 2 |

---

## Confidence Notes

All pitfalls above are specific to the exact stack (Python + `requests` + Ollama REST API + LaTeX output + CLI input loop). They are drawn from known behavior of:

- Ollama's `/api/generate` endpoint (NDJSON streaming, `done_reason`, `num_ctx`, model cold-load latency)
- `requests` library behavior (default `None` timeout, `iter_lines()` for streaming, `raise_for_status()`)
- Instruction-tuned LLM output tendencies (markdown defaults, hallucination under instruction)
- LaTeX toolchain constraints (UTF-8 encoding, `pdflatex` sensitivity to malformed files)
- Python path resolution (`__file__`-anchoring vs CWD-relative strings)

Confidence: HIGH for Pitfalls 1-5, 7, 9-11, 13-15 (well-established patterns).
Confidence: MEDIUM for Pitfall 6 (NDJSON specifics depend on Ollama version), Pitfall 12 (token counts are estimates).
