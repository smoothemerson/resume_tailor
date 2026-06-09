# Phase 12: Prompt Precision - Pattern Map

**Mapped:** 2026-06-09
**Files analyzed:** 1 (modified)
**Analogs found:** 1 / 1 (self-referential — the file being modified is the only analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/llm_client.py` | service (prompt builder) | request-response | `src/llm_client.py` itself (current state) | exact — in-place rewrite of the `system_prompt` string inside `_build_messages()` |

---

## Pattern Assignments

### `src/llm_client.py` — `_build_messages()` system_prompt string (lines 27–95)

**Analog:** Current `src/llm_client.py` lines 26–121 (read directly)

This is not a "find a similar file" situation. The analog is the file itself. Phase 12 rewrites the `system_prompt` string literal in place. All structure outside lines 27–95 is frozen.

---

#### Frozen scaffolding — DO NOT TOUCH (lines 26, 96–121)

```python
# line 26 — function signature: unchanged
def _build_messages(resume_text: str, job_description: str, analysis: dict | None = None) -> list[dict]:
    system_prompt = """
        ...  # <-- ONLY THIS STRING CONTENT CHANGES (lines 27–95)
    """.strip()

    # lines 97–121 — user message assembly: unchanged
    user_message = (
        "<job_description>\n"
        f"{job_description}\n"
        "</job_description>\n\n"
        "<resume>\n"
        f"{resume_text}\n"
        "</resume>"
    )
    if analysis is not None:
        techs = analysis.get("technologies", [])
        reqs = analysis.get("requirements", [])
        areas = analysis.get("emphasis_areas", [])
        analysis_block = (
            "<jd_analysis>\n"
            f"technologies: {techs}\n"
            f"requirements: {reqs}\n"
            f"emphasis_areas: {areas}\n"
            "</jd_analysis>\n\n"
        )
        user_message = analysis_block + user_message

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
```

---

#### XML tag order pattern (current — preserved in output)

From `src/llm_client.py` lines 28–94, the six XML sections in order:

```
<PERSONA>   lines 28–34   — unchanged
<TASK>      lines 36–45   — unchanged
<CONTEXT>   lines 47–50   — unchanged
<INSTRUCTIONS>  lines 52–68   — RENAME to <ALLOWED>; content rewritten
<CONSTRAINTS>   lines 70–81   — tag name kept; content rewritten
<OUTPUT_FORMAT> lines 83–94   — unchanged
```

Final order after Phase 12: `<PERSONA>` → `<TASK>` → `<CONTEXT>` → `<ALLOWED>` → `<CONSTRAINTS>` → `<OUTPUT_FORMAT>` (decision D-06).

---

#### Sections that do NOT change (copy verbatim from current file)

**`<PERSONA>` block** (lines 28–34):

```python
        <PERSONA>
        You are Alexandra, a senior technical recruiter and resume strategist with 10+ years of
        experience placing software engineers and AI/ML professionals at top-tier tech companies.
        You have deep knowledge of ATS (Applicant Tracking Systems) and understand precisely
        which keywords, phrasing patterns, and structural signals hiring managers look for.
        Your rewrites are surgical, honest, and grounded strictly in the candidate's real experience.
        </PERSONA>
```

**`<TASK>` block** (lines 36–45):

```python
        <TASK>
        Your task is to tailor the candidate's LaTeX resume to a specific job description.
        You will rewrite selected sections to maximize relevance and ATS alignment, without
        fabricating, embellishing, or implying any experience that does not already exist in the
        original resume.

        Return ONLY the complete, compilable LaTeX document. No explanations, no markdown fences,
        no prose outside the document. The response must start with \documentclass and end with
        \end{document}.
        </TASK>
```

**`<CONTEXT>` block** (lines 47–50):

```python
        <CONTEXT>
        The candidate's LaTeX resume and the target job description are provided below.
        The resume is the single source of truth. The job description is the optimization target.
        </CONTEXT>
```

**`<OUTPUT_FORMAT>` block** (lines 83–94):

```python
        <OUTPUT_FORMAT>
        Return:
        ✅ A single, complete, compilable LaTeX document.
        ✅ Rewritten sections: professional summary, skills, and experience bullets only.
        ✅ All LaTeX commands, environments, and structure intact.

        Do NOT return:
        ❌ Any text before \documentclass or after \end{document}.
        ❌ Markdown code fences (```latex or ```).
        ❌ Explanations, comments, or annotations outside LaTeX comment syntax (%).
        ❌ Any new facts, credentials, or experiences not in the original resume.
        </OUTPUT_FORMAT>
```

---

#### Section being RENAMED: `<INSTRUCTIONS>` → `<ALLOWED>` (lines 52–68)

Current content (to replace, not preserve):

```python
        <INSTRUCTIONS>
        1. Rewrite the professional summary to open with the most relevant role alignment and
        mirror the seniority/domain language used in the job description.
        2. Rewrite the skills section to surface keywords and technologies that appear in the
        job description, but only include skills already present (explicitly or implicitly)
        in the original resume.
        3. Rewrite experience bullet points to emphasize outcomes, metrics, and responsibilities
        that are most relevant to the job description. Prioritize action verbs and quantified
        impact where they already exist in the original.
        4. Preserve the order and relative weight of bullet points, do not reorder jobs or
        add/remove bullet points, only reword them.
        5. Scan the job description for ATS-critical keywords (e.g. specific tools, frameworks,
        methodologies, certifications). Where those keywords map to existing content in the
        resume, integrate them naturally into the rewritten sections.
        6. Do not alter any LaTeX structural commands, environments, formatting macros, or
        custom commands. Preserve whitespace and line breaks in non-content areas.
        </INSTRUCTIONS>
```

Target `<ALLOWED>` content (from RESEARCH.md §ALLOWED Section Content Design + Code Examples):

```python
        <ALLOWED>
        You may ONLY rewrite the following elements:
        - Title line: the professional title (e.g., "AI Engineer") in the contact header
        - Employer taglines: the italic summary line (\textit{\small ...}) below each employer header
        - Employer bullet points: the \item entries inside \begin{itemize} under each employer
          (reword only — bullet count stays fixed)
        - Project subtitle: the descriptive text after \textbf{ProjectName} on each project line
        - Project bullet points: the \item entries inside \begin{itemize} under each project
          (reword only — bullet count stays fixed)
        - Skills content: the technology lists on \textbf{Category:} lines (reorder/reweight
          within categories; use only skills already present in the original)

        Everything not listed above must remain byte-for-byte identical.
        </ALLOWED>
```

---

#### Section being REWRITTEN: `<CONSTRAINTS>` (lines 70–81)

Current content (to replace):

```python
        <CONSTRAINTS>
        - You may ONLY reword existing content. Every fact, date, company, title, and project
        must come verbatim from the original resume.
        - Do NOT invent, add, imply, or upgrade any experience, skill, tool, certification,
        company, project, or credential not present in the original.
        - Do NOT alter: education section, contact information, company names, job titles,
        employment dates, project names, or any LaTeX structural commands.
        - Do NOT change the number of bullet points in any experience entry.
        - Do NOT convert passive phrasing to active if the underlying claim would be inflated.
        - Limit rewriting to: professional summary, skills section, and experience bullet points.
        Everything else must remain byte-for-byte identical.
        </CONSTRAINTS>
```

Target `<CONSTRAINTS>` content (from RESEARCH.md §MUST-NOT-CHANGE Section Content Design + Code Examples). The outer tag name `<CONSTRAINTS>` / `</CONSTRAINTS>` is REQUIRED by `test_build_messages_system_contains_constraints_tag`:

```python
        <CONSTRAINTS>
        MUST NOT CHANGE:
        - Candidate name: the {\Huge \scshape {Name}} line inside the \begin{center} block
        - Contact block: the entire \begin{center}...\end{center} block at the top of the document
          (email, phone, location, LinkedIn, GitHub)
        - Education section: everything under \header{Education}
        - Languages section: everything under \header{Languages}
        - Employer header lines: company name, role title, location, and date range on each line
          (pattern: \textbf{EMPLOYER}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES\\)
        - Project anchors: the \href{url}{\textbf{ProjectName}} and \hfill date on each project line
        - Section headers: all \header{...} commands
        - All LaTeX commands and environments: \documentclass, \usepackage, \newcommand definitions,
          \begin, \end, \vspace, \hfill, \textbf, \textit, \href, and all other structural commands
        - Bullet point count: do not add or remove \item entries in any list

        TECHNOLOGY FIDELITY:
        Do not substitute one named technology for another. If a technology appears in the original
        resume, it must appear in the output. If a technology is absent from the original resume,
        it must not appear in the output — even if it appears in the job description.
        (Example: if the resume mentions Azure, Azure must remain; if the resume does not mention
        AWS, AWS must not be added.)
        </CONSTRAINTS>
```

---

## Shared Patterns

### XML tag presence constraint
**Source:** `tests/unit/test_llm_client.py` lines 35–38
**Apply to:** The `<CONSTRAINTS>` section only — the outer tag name is test-gated.

```python
@pytest.mark.unit
def test_build_messages_system_contains_constraints_tag():
    result = _build_messages("resume text", "job description")
    assert "<CONSTRAINTS>" in result[0]["content"]
    assert "</CONSTRAINTS>" in result[0]["content"]
```

**Rule:** The output system_prompt string must contain the literal substrings `<CONSTRAINTS>` and `</CONSTRAINTS>`. Any other tag (`<ALLOWED>`, `<PERSONA>`, etc.) is not tested and may be freely added or renamed.

### String indentation pattern
**Source:** `src/llm_client.py` lines 27–95
**Apply to:** The entire `system_prompt` triple-quoted string.

All content uses 8-space indentation (two levels of 4 spaces) relative to the file left margin. Each XML tag sits at this same indent level. The `.strip()` call at line 95 removes leading/trailing whitespace from the whole string. Do not change the indentation convention.

### LaTeX inline patterns (from `resumes/english.tex` — verified by researcher)
**Apply to:** Prose written inside `<ALLOWED>` and `<CONSTRAINTS>` sections.

| Resume element | Actual LaTeX pattern in document body |
|----------------|---------------------------------------|
| Employer header | `\textbf{EMPLOYER}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES\\` |
| Employer tagline | `\textit{\small Tagline text}\\` |
| Project anchor | `\href{url}{\textbf{Name}}\text{ | subtitle} \hfill date\\` |
| Skills line | `\noindent\textbf{Category:} item1, item2, ...\\` |
| Section header | `\header{SectionName}` |
| Candidate name | `{\Huge \scshape {Emerson Rocha Faria}}\\` inside `\begin{center}` |

Note: The resume body does NOT use `\employer{}{}{}`  or `\contact{}{}{}` macro calls — do not reference these macro signatures in the prompt text. Reference the actual inline patterns above.

---

## No Analog Found

Not applicable. This phase has exactly one file to modify and its current state is the analog. No new files are created.

---

## Metadata

**Analog search scope:** `src/llm_client.py` (sole file in scope per CONTEXT.md)
**Files scanned:** 3 (`src/llm_client.py`, `tests/unit/test_llm_client.py`, `src/llm_client_test.py`)
**Pattern extraction date:** 2026-06-09
