import re
import subprocess
import sys
from pathlib import Path

import pytest

CLI_PATH = Path(__file__).parents[2] / "src" / "cli.py"

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)


@pytest.mark.e2e
def test_empty_jd_exits_1_with_stderr_message():
    result = subprocess.run(
        [sys.executable, CLI_PATH],
        input="END\n",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Error: Job description cannot be empty." in result.stderr


@pytest.mark.e2e
def test_golden_path_exits_0_creates_output_file(require_ollama, tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text(MINIMAL_RESUME, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, CLI_PATH,
         "--resume", str(resume_file),
         "--output-dir", str(tmp_path)],
        input="Python backend engineer with REST API experience\nEND\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Tailored resume written to:" in result.stdout
    output_files = list(tmp_path.glob("tailored_resume_*.tex"))
    assert len(output_files) == 1
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", output_files[0].name)
