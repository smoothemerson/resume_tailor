import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-tailor",
        description="Tailor a LaTeX resume to a job description using a local Ollama LLM.",
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
