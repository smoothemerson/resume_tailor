import argparse
import sys

from config import BASE_RESUME_PATH, OUTPUT_DIR
from llm_client import generate_tailored_resume
from resume_reader import read_resume
from resume_writer import write_resume


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-tailor",
        description="Tailor a LaTeX resume to a job description using a local Ollama LLM.",
    )
    parser.parse_args()

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

    print("Tailoring resume — this may take a minute...", flush=True)

    try:
        resume_text = read_resume(BASE_RESUME_PATH)
        content = generate_tailored_resume(resume_text, job_description)
        output_path = write_resume(content, OUTPUT_DIR)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Tailored resume written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
