# Architecture Patterns

**Domain:** Python CLI tool — LaTeX resume tailoring via local Ollama LLM
**Researched:** 2026-05-28
**Confidence:** HIGH (Ollama REST API is stable and well-documented; patterns derived from project constraints)

---

## Component Map

### Modules and Responsibilities

| Module | Responsibility | Owns |
|--------|---------------|------|
| `main.py` | Entry point, orchestration, user I/O | CLI loop, argument parsing, exit codes |
| `config.py` | All configurable values as named constants | Model name, file paths, API URL, timeout |
| `resume_reader.py` | Read `.tex` file from disk | File existence check, UTF-8 read, raw string return |
| `llm_client.py` | Call Ollama REST API, return LLM response text | HTTP call, prompt assembly, response parsing, network errors |
| `resume_writer.py` | Write tailored `.tex` to timestamped output path | Directory creation, file write, path return |

### Who Talks to Whom

```
main.py
  ├── imports config.py          (reads constants only — no function calls)
  ├── calls resume_reader.py     (returns raw LaTeX string)
  ├── calls llm_client.py        (sends resume + job description, returns tailored LaTeX string)
  └── calls resume_writer.py     (receives tailored LaTeX string, returns output path)
```

`config.py` is a passive dependency — no module except `main.py` should import it. `llm_client.py` receives model/URL as parameters so it stays testable without touching global state.

### Component Boundaries

- `resume_reader.py` knows nothing about LLMs. It returns a plain string. If the file does not exist it raises `FileNotFoundError` — no swallowing.
- `llm_client.py` knows nothing about files. It receives `(resume_text, job_description, model, api_url)` and returns a string. All HTTP complexity lives here and nowhere else.
- `resume_writer.py` knows nothing about LLMs or HTTP. It receives a string and writes it. It returns the absolute path it wrote to.
- `main.py` is the only module that wires everything together and handles user-facing error messages. It catches domain exceptions and prints them; it never lets a traceback surface to the user.

---

## Data Flow

```
[Disk: english.tex]
        |
        v
resume_reader.read_resume(path)
        |
        v  str: raw LaTeX content
        |
main.py collects job description via stdin (multiline, END to submit)
        |
        v  str: job description
        |
llm_client.call(resume_text, job_description, model, api_url)
        |  -- assembles system + user messages
        |  -- POST /api/chat  (JSON body)
        |  -- parses response["message"]["content"]
        |
        v  str: tailored LaTeX content
        |
resume_writer.write(tailored_text)
        |  -- generates timestamp: YYYYMMDD_HHMMSS
        |  -- ensures resumes/output/ exists
        |  -- writes .tex file
        |
        v  str: output file path
        |
main.py prints success message + path to stdout
```

Data is always plain strings between modules. No shared mutable state. No global variables set at runtime.

---

## Ollama API Details

### Endpoint Choice: /api/chat over /api/generate

Use `/api/chat`. Reasons:

1. It accepts a `messages` array with explicit `role` fields (`system`, `user`, `assistant`). This maps directly to the system-prompt-as-guardrail pattern the project requires.
2. `/api/generate` accepts a single `prompt` string — system prompt has to be manually prepended with no role separation. Harder to maintain and test.
3. `/api/chat` is the current idiomatic endpoint; `/api/generate` is older and less structured.

**Confidence:** HIGH — this distinction has been stable in Ollama since v0.1.x.

### Request Format

```python
POST http://localhost:11434/api/chat
Content-Type: application/json

{
  "model": "mistral",
  "messages": [
    {
      "role": "system",
      "content": "<system prompt here>"
    },
    {
      "role": "user",
      "content": "<resume LaTeX + job description here>"
    }
  ],
  "stream": false
}
```

Setting `"stream": false` makes Ollama return a single JSON object. This is mandatory for this tool — there is no benefit to streaming into a file write.

### Response Format (non-streaming)

```json
{
  "model": "mistral",
  "created_at": "2026-05-28T...",
  "message": {
    "role": "assistant",
    "content": "\\documentclass[a4paper]{article}\n..."
  },
  "done": true,
  "done_reason": "stop",
  "total_duration": 12345678,
  "prompt_eval_count": 512,
  "eval_count": 1024
}
```

The tailored LaTeX lives at `response["message"]["content"]`. Check `response["done"] == True` before trusting the content.

### Response Parsing in llm_client.py

```python
import requests

def call(resume_text: str, job_description: str, model: str, api_url: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user",   "content": _build_user_message(resume_text, job_description)},
        ],
        "stream": False,
    }
    response = requests.post(f"{api_url}/api/chat", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    if not data.get("done"):
        raise ValueError("Ollama returned an incomplete response (done=False)")
    return data["message"]["content"]
```

`timeout=120` is a reasonable default for a local model on CPU; expose it in `config.py` for easy tuning.

### Streaming: When to Use It

Do not use streaming (`"stream": true`) in this tool. Streaming returns newline-delimited JSON objects, one per token, which requires a parse loop and adds complexity with zero user-facing benefit — the output is going to a file, not a terminal progress display.

If a future phase adds a "show progress while generating" UX, streaming becomes relevant. Defer that entirely.

### System Prompt Structure

The system prompt is the primary guardrail. Keep it in `llm_client.py` as a module-level constant or in a dedicated `prompts.py` if it grows large. Key instructions to include:

1. Return only valid LaTeX — no markdown fences, no prose, no explanations.
2. Preserve the document class, custom commands, and structural macros exactly.
3. Rewrite: summary/objective line, skills section, and bullet points to align with the job description.
4. Do not add experiences, employers, projects, or dates that are not in the original resume.
5. Do not remove the Education, Languages, or contact sections.

User message format:

```
--- RESUME ---
{resume_text}

--- JOB DESCRIPTION ---
{job_description}
```

Explicit delimiters prevent the model from confusing resume content with instructions.

---

## Error Handling Patterns

### Error Categories and Where to Handle Them

| Error | Where It Occurs | Who Catches It | User Message |
|-------|----------------|----------------|--------------|
| Resume file not found | `resume_reader.py` raises `FileNotFoundError` | `main.py` catches | "Resume file not found: {path}" |
| Ollama not running | `requests.post` raises `ConnectionError` | `main.py` catches | "Cannot connect to Ollama at {url}. Is it running?" |
| HTTP error from Ollama | `response.raise_for_status()` raises `HTTPError` | `main.py` catches | "Ollama returned HTTP {status}: {reason}" |
| Request timeout | `requests.post` raises `Timeout` | `main.py` catches | "Ollama timed out after {timeout}s. Try a smaller model or increase timeout." |
| Incomplete response | `data["done"] == False` | `llm_client.py` raises `ValueError` | "Ollama returned an incomplete response." |
| Output dir not writable | `resume_writer.py` raises `OSError` | `main.py` catches | "Cannot write output: {error}" |

### Pattern: Raise Domain Exceptions, Catch at main.py

Each module raises standard Python exceptions (no custom exception hierarchy needed at this scale). `main.py` is the single place that catches, formats, and prints user-facing error messages, then calls `sys.exit(1)`.

```python
# main.py pattern
try:
    resume_text = resume_reader.read(config.RESUME_PATH)
    job_description = collect_job_description()
    tailored = llm_client.call(resume_text, job_description, config.MODEL, config.API_URL)
    output_path = resume_writer.write(tailored)
    print(f"Tailored resume written to: {output_path}")
except FileNotFoundError as e:
    print(f"Error: Resume file not found — {e}", file=sys.stderr)
    sys.exit(1)
except requests.exceptions.ConnectionError:
    print(f"Error: Cannot connect to Ollama at {config.API_URL}. Is it running?", file=sys.stderr)
    sys.exit(1)
except requests.exceptions.Timeout:
    print(f"Error: Ollama timed out. Increase TIMEOUT in config.py or try a smaller model.", file=sys.stderr)
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    print(f"Error: Ollama HTTP error — {e}", file=sys.stderr)
    sys.exit(1)
except (OSError, ValueError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

Do not use bare `except Exception` as a catch-all — it hides bugs during development. Named exceptions at `main.py` is the right boundary.

---

## Build Order

Build in dependency order: leaf modules first, orchestrator last.

### Phase 1 — Config foundation
Build `config.py` first. Every other module imports from it. Establishing `RESUME_PATH`, `MODEL`, `API_URL`, `OUTPUT_DIR`, and `TIMEOUT` here means no other module has magic strings.

### Phase 2 — File I/O modules (no external deps)
Build `resume_reader.py` and `resume_writer.py` next. Both are pure file I/O with no network calls. They can be manually tested immediately with the existing `english.tex`. This validates that the read-write roundtrip works before any LLM is involved.

### Phase 3 — LLM client
Build `llm_client.py`. By this point `config.py` is done, so constants are available. Test with a real Ollama instance: send the actual resume and a sample job description, inspect the raw response JSON, confirm the LaTeX comes back clean. Tweak the system prompt here — this is where most iteration will happen.

### Phase 4 — main.py (orchestrator)
Wire all modules together. Add the multiline stdin collector. Add the error handler block. Run end-to-end.

### Rationale for This Order

- `config.py` has zero dependencies — build first, nothing blocks it.
- File I/O modules have no network dependency — validate disk behavior independently of Ollama availability.
- `llm_client.py` is the highest-risk module (external call, prompt engineering, response parsing) — isolate and test it before wiring.
- `main.py` only becomes meaningful when all other modules work — build last and use it as integration glue.

---

## Scalability Considerations

This tool is intentionally single-user, offline-first, CLI-only. Scalability is not a concern. The one performance variable is LLM inference speed, which is a function of model size and hardware — not addressable in code. Exposing `TIMEOUT` and `MODEL` in `config.py` is the correct handle for users to tune this.

---

## Sources

- Ollama REST API documentation: https://github.com/ollama/ollama/blob/main/docs/api.md (HIGH confidence — stable API, verified against training data through August 2025)
- Project requirements: `.planning/PROJECT.md`
- Actual resume structure: `english.tex` (reviewed to understand LaTeX macro complexity the system prompt must preserve)
