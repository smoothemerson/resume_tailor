import pytest
import requests
from unittest.mock import MagicMock, patch

from llm_client import (
    _build_messages,
    _check_ollama_health,
    _strip_fences,
    _validate_latex,
    generate_tailored_resume,
)


@pytest.mark.unit
def test_build_messages_returns_two_element_list():
    result = _build_messages("resume text", "job description")
    assert len(result) == 2


@pytest.mark.unit
def test_build_messages_role_ordering():
    result = _build_messages("resume text", "job description")
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"


@pytest.mark.unit
def test_build_messages_system_contains_persona_tag():
    result = _build_messages("resume text", "job description")
    assert "<PERSONA>" in result[0]["content"]
    assert "</PERSONA>" in result[0]["content"]


@pytest.mark.unit
def test_build_messages_system_contains_constraints_tag():
    result = _build_messages("resume text", "job description")
    assert "<CONSTRAINTS>" in result[0]["content"]
    assert "</CONSTRAINTS>" in result[0]["content"]


@pytest.mark.unit
def test_build_messages_user_contains_job_description_xml_tag():
    result = _build_messages("resume text", "job description")
    assert "<job_description>" in result[1]["content"]
    assert "</job_description>" in result[1]["content"]


@pytest.mark.unit
def test_build_messages_user_embeds_job_description_content():
    result = _build_messages("resume text", "python developer")
    assert "python developer" in result[1]["content"]


@pytest.mark.unit
def test_build_messages_user_contains_resume_xml_tag():
    result = _build_messages("resume text", "job description")
    assert "<resume>" in result[1]["content"]
    assert "</resume>" in result[1]["content"]


@pytest.mark.unit
def test_build_messages_user_embeds_resume_content():
    result = _build_messages("my specific resume", "job description")
    assert "my specific resume" in result[1]["content"]


@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_connection_error_raises_runtime_error(mock_get):
    mock_get.side_effect = requests.ConnectionError("connection refused")
    with pytest.raises(RuntimeError, match="not reachable"):
        _check_ollama_health()


@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_timeout_raises_runtime_error(mock_get):
    mock_get.side_effect = requests.Timeout("timed out")
    with pytest.raises(RuntimeError, match="timed out"):
        _check_ollama_health()


@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_http_error_raises_runtime_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("503")
    mock_get.return_value = mock_response
    with pytest.raises(RuntimeError, match="HTTP error"):
        _check_ollama_health()


@pytest.mark.unit
@patch("llm_client.requests.get")
def test_check_ollama_health_200_does_not_raise(mock_get):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    _check_ollama_health()
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@pytest.mark.unit
def test_strip_fences_removes_latex_fence():
    fenced = "```latex\n\\documentclass{article}\n\\end{document}\n```"
    assert _strip_fences(fenced) == "\\documentclass{article}\n\\end{document}"


@pytest.mark.unit
def test_strip_fences_no_op_on_clean_content():
    content = "\\documentclass{article}\n\\end{document}"
    assert _strip_fences(content) == content


@pytest.mark.unit
def test_strip_fences_removes_fence_without_language_tag():
    fenced = "```\n\\documentclass{article}\n\\end{document}\n```"
    assert _strip_fences(fenced) == "\\documentclass{article}\n\\end{document}"


@pytest.mark.unit
def test_validate_latex_raises_on_missing_documentclass():
    with pytest.raises(ValueError, match="documentclass"):
        _validate_latex("not latex at all\n\\end{document}")


@pytest.mark.unit
def test_validate_latex_raises_on_missing_end_document():
    with pytest.raises(ValueError, match=r"end\{document\}"):
        _validate_latex("\\documentclass{article}\ntruncated")


@pytest.mark.unit
def test_validate_latex_returns_text_on_valid_input():
    valid = "\\documentclass{article}\nbody\n\\end{document}"
    assert _validate_latex(valid) == valid


@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_truncated_raises(mock_post, mock_health):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "length",
        "message": {"content": ""},
    }
    mock_post.return_value = mock_response
    with pytest.raises(RuntimeError, match="truncated"):
        generate_tailored_resume("resume", "job desc")


@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_returns_tailor_result(mock_post, mock_health):
    valid_latex = "\\documentclass{article}\nbody\n\\end{document}"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": valid_latex},
    }
    mock_post.return_value = mock_response
    result = generate_tailored_resume("resume", "job desc")
    assert result.content == valid_latex
    assert result.fences_stripped is False


@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_fences_stripped_flag(mock_post, mock_health):
    valid_latex = "\\documentclass{article}\nbody\n\\end{document}"
    fenced = f"```latex\n{valid_latex}\n```"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": fenced},
    }
    mock_post.return_value = mock_response
    result = generate_tailored_resume("resume", "job desc")
    assert result.content == valid_latex
    assert result.fences_stripped is True


@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_connection_error_raises(mock_post, mock_health):
    mock_post.side_effect = requests.ConnectionError("refused")
    with pytest.raises(RuntimeError, match="Cannot connect"):
        generate_tailored_resume("resume", "job desc")


@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_timeout_raises(mock_post, mock_health):
    mock_post.side_effect = requests.Timeout("timed out")
    with pytest.raises(RuntimeError, match="timed out"):
        generate_tailored_resume("resume", "job desc")


@pytest.mark.unit
@patch("llm_client._check_ollama_health")
@patch("llm_client.requests.post")
def test_generate_tailored_resume_missing_content_key_raises(mock_post, mock_health):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"done_reason": "stop", "message": {}}
    mock_post.return_value = mock_response
    with pytest.raises(RuntimeError, match="Unexpected Ollama response"):
        generate_tailored_resume("resume", "job desc")


@pytest.mark.unit
def test_build_messages_with_analysis_includes_jd_analysis_tag():
    result = _build_messages("r", "jd", {"technologies": [], "requirements": [], "emphasis_areas": []})
    assert "<jd_analysis>" in result[1]["content"]
    assert "</jd_analysis>" in result[1]["content"]


@pytest.mark.unit
def test_build_messages_without_analysis_omits_jd_analysis_tag():
    result = _build_messages("r", "jd")
    assert "<jd_analysis>" not in result[1]["content"]


def _system_constraints_block() -> str:
    content = _build_messages("resume text", "job description")[0]["content"]
    return content[content.index("<CONSTRAINTS>") : content.index("</CONSTRAINTS>")]


@pytest.mark.unit
def test_build_messages_system_contains_allowed_tag():
    result = _build_messages("resume text", "job description")
    assert "<ALLOWED>" in result[0]["content"]
    assert "</ALLOWED>" in result[0]["content"]


@pytest.mark.unit
def test_build_messages_allowed_section_names_six_rewritable_elements():
    content = _build_messages("resume text", "job description")[0]["content"]
    allowed = content[content.index("<ALLOWED>") : content.index("</ALLOWED>")]
    assert "Title line" in allowed
    assert "Employer taglines" in allowed
    assert "Employer bullet points" in allowed
    assert "Project subtitle" in allowed
    assert "Project bullet points" in allowed
    assert "Skills content" in allowed


@pytest.mark.unit
def test_build_messages_allowed_section_closes_with_byte_identical_rule():
    content = _build_messages("resume text", "job description")[0]["content"]
    allowed = content[content.index("<ALLOWED>") : content.index("</ALLOWED>")]
    assert "Everything not listed above must remain byte-for-byte identical." in allowed


@pytest.mark.unit
def test_build_messages_system_omits_legacy_instructions_tag():
    result = _build_messages("resume text", "job description")
    assert "<INSTRUCTIONS>" not in result[0]["content"]
    assert "</INSTRUCTIONS>" not in result[0]["content"]


@pytest.mark.unit
def test_build_messages_constraints_contain_must_not_change_list():
    assert "MUST NOT CHANGE:" in _system_constraints_block()


@pytest.mark.unit
def test_build_messages_constraints_name_protected_elements_by_latex_pattern():
    constraints = _system_constraints_block()
    assert r"{\Huge \scshape {Name}}\\" in constraints
    assert r"\begin{center}...\end{center}" in constraints
    assert r"\header{Education}" in constraints
    assert r"\header{Languages}" in constraints
    assert r"\textbf{EMPLOYER}\textbf{ | ROLE} \hfill LOCATION\ $\cdot$\ DATES\\" in constraints
    assert r"\href{url}{\textbf{ProjectName}}" in constraints
    assert r"\header{...}" in constraints
    assert r"\documentclass" in constraints
    assert r"Bullet point count: do not add or remove \item entries in any list" in constraints


@pytest.mark.unit
def test_build_messages_constraints_contain_technology_fidelity_rule():
    assert "TECHNOLOGY FIDELITY:" in _system_constraints_block()


@pytest.mark.unit
def test_build_messages_technology_fidelity_includes_azure_aws_example():
    constraints = _system_constraints_block()
    assert "if the resume mentions Azure, Azure must remain" in constraints
    assert "AWS, AWS must not be added" in constraints
