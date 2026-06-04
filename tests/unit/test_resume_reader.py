import pytest

from resume_reader import read_resume


@pytest.mark.unit
def test_read_resume_returns_file_content(tmp_path):
    resume_file = tmp_path / "resume.tex"
    resume_file.write_text("\\documentclass{article}", encoding="utf-8")
    assert read_resume(resume_file) == "\\documentclass{article}"


@pytest.mark.unit
def test_read_resume_missing_file_raises_file_not_found_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_resume(tmp_path / "nonexistent.tex")
