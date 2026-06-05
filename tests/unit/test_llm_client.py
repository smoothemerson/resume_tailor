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
