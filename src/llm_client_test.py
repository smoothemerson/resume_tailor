import pytest
from unittest.mock import MagicMock, patch

import requests

from llm_client import TailorResult, _strip_fences, _validate_latex, generate_tailored_resume


def test_strip_latex_fence():
    result = _strip_fences("```latex\n\\documentclass{article}\n```")
    assert result == "\\documentclass{article}"


def test_strip_bare_fence():
    result = _strip_fences("```\n\\documentclass{article}\n```")
    assert result == "\\documentclass{article}"


def test_strip_tex_fence():
    result = _strip_fences("```tex\n\\documentclass{article}\n\\end{document}\n```")
    assert result == "\\documentclass{article}\n\\end{document}"


def test_no_op_on_clean_input():
    result = _strip_fences("\\documentclass{article}")
    assert result == "\\documentclass{article}"


def test_valid_latex_returns_text():
    text = "\\documentclass{article}\n\\end{document}"
    result = _validate_latex(text)
    assert result == text


def test_missing_end_document_raises():
    with pytest.raises(ValueError):
        _validate_latex("\\documentclass{article}")


def test_missing_documentclass_raises():
    with pytest.raises(ValueError):
        _validate_latex("\\end{document}")


def test_no_latex_raises():
    with pytest.raises(ValueError):
        _validate_latex("no latex here")


@patch("llm_client.requests.get")
def test_health_check_connection_error_raises_runtime_error(mock_get):
    mock_get.side_effect = requests.ConnectionError("connection refused")
    with pytest.raises(RuntimeError):
        generate_tailored_resume("resume text", "job description")


@patch("llm_client.requests.post")
@patch("llm_client.requests.get")
def test_done_reason_length_raises_runtime_error(mock_get, mock_post):
    mock_get.return_value = MagicMock(status_code=200)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "done_reason": "length",
        "message": {"content": ""},
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    with pytest.raises(RuntimeError):
        generate_tailored_resume("resume text", "job description")


@patch("llm_client.requests.post")
@patch("llm_client.requests.get")
def test_invalid_llm_output_raises_value_error(mock_get, mock_post):
    mock_get.return_value = MagicMock(status_code=200)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": "not valid latex at all"},
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    with pytest.raises(ValueError):
        generate_tailored_resume("resume text", "job description")


@patch("llm_client.requests.post")
@patch("llm_client.requests.get")
def test_returns_tailor_result_namedtuple(mock_get, mock_post):
    mock_get.return_value = MagicMock(status_code=200)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": "\\documentclass{article}\n\\end{document}"},
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    result = generate_tailored_resume("resume text", "job description")
    assert isinstance(result, TailorResult)


@patch("llm_client.requests.post")
@patch("llm_client.requests.get")
def test_fences_stripped_false_when_no_fences(mock_get, mock_post):
    mock_get.return_value = MagicMock(status_code=200)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": "\\documentclass{article}\n\\end{document}"},
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    result = generate_tailored_resume("resume text", "job description")
    assert not result.fences_stripped


@patch("llm_client.requests.post")
@patch("llm_client.requests.get")
def test_fences_stripped_true_when_raw_had_fences(mock_get, mock_post):
    mock_get.return_value = MagicMock(status_code=200)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": "```latex\n\\documentclass{article}\n\\end{document}\n```"},
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    result = generate_tailored_resume("resume text", "job description")
    assert result.fences_stripped


@patch("llm_client.requests.post")
@patch("llm_client.requests.get")
def test_content_field_is_stripped_latex(mock_get, mock_post):
    mock_get.return_value = MagicMock(status_code=200)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": "```latex\n\\documentclass{article}\n\\end{document}\n```"},
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    result = generate_tailored_resume("resume text", "job description")
    assert result.content == "\\documentclass{article}\n\\end{document}"
