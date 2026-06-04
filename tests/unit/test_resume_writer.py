import re
from pathlib import Path

import pytest

from resume_writer import write_resume


@pytest.mark.unit
def test_write_resume_creates_output_directory(tmp_path):
    output_dir = tmp_path / "new_output"
    assert not output_dir.exists()
    write_resume("content", output_dir)
    assert output_dir.exists()


@pytest.mark.unit
def test_write_resume_returns_path(tmp_path):
    result = write_resume("content", tmp_path / "out")
    assert isinstance(result, Path)


@pytest.mark.unit
def test_write_resume_filename_matches_timestamp_pattern(tmp_path):
    result = write_resume("content", tmp_path / "out2")
    assert re.match(r"tailored_resume_\d{8}_\d{6}\.tex", result.name)


@pytest.mark.unit
def test_write_resume_content_equals_input_string(tmp_path):
    content = "\\documentclass{article}\n\\end{document}"
    result = write_resume(content, tmp_path / "out3")
    assert result.read_text(encoding="utf-8") == content
