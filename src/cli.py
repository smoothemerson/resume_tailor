import argparse
import sys
from pathlib import Path

from config import BASE_RESUME_PATH, OUTPUT_DIR
from diff_view import show_diff
from guards import run_guards
from jd_analyzer import analyze_job_description
from llm_client import TailorResult, generate_tailored_resume
from resume_reader import read_resume
from resume_writer import write_resume


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-tailor",
        description="Tailor a LaTeX resume to a job description using a local Ollama LLM.",
    )
    parser.add_argument("--model", default=None, help="Ollama model name (overrides config)")
    parser.add_argument("--resume", type=Path, default=None, help="Path to base .tex resume file")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for output files")
    args = parser.parse_args()

    resume_path = args.resume or BASE_RESUME_PATH
    output_dir = args.output_dir or OUTPUT_DIR

    print("Resume Tailor")
    print("Paste the job description below. Type END on a new line to submit.")
    print("")
    print(">")

    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)

    job_description = "\n".join(lines)

    if not job_description.strip():
        print("Error: Job description cannot be empty.", file=sys.stderr)
        sys.exit(1)

    print("Analyzing job description...", flush=True)

    try:
        analysis = analyze_job_description(job_description, model=args.model)
        resume_text = read_resume(resume_path)
        print("Tailoring resume — this may take a minute...", flush=True)
        result = generate_tailored_resume(resume_text, job_description, analysis=analysis, model=args.model)
        run_guards(resume_text, result.content, result.fences_stripped)
        output_path = write_resume(result.content, output_dir)
        show_diff(resume_text, result.content)
        print(f"Tailored resume written to: {output_path.resolve()}")
    except (RuntimeError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
