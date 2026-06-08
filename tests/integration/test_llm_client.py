import pytest

from llm_client import _check_ollama_health, generate_tailored_resume

MINIMAL_RESUME = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "\\section{Summary}\n"
    "AI engineer with 3 years experience.\n"
    "\\end{document}"
)


@pytest.mark.integration
def test_ollama_health_check_does_not_raise(require_ollama):
    _check_ollama_health()


@pytest.mark.integration
def test_generate_tailored_resume_returns_valid_latex(require_ollama):
    MINIMAL_JD = "Python backend engineer with REST API experience"
    result = generate_tailored_resume(MINIMAL_RESUME, MINIMAL_JD)
    assert result.content.lstrip().startswith("\\documentclass")
    assert result.content.rstrip().endswith("\\end{document}")
    assert "```" not in result.content
    assert result.fences_stripped is False
