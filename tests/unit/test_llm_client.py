import pytest
import requests
from unittest.mock import MagicMock, patch

from llm_client import _build_messages, _check_ollama_health


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
