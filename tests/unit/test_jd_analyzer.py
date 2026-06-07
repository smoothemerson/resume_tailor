import pytest
import requests
from unittest.mock import MagicMock, patch

from jd_analyzer import analyze_job_description


@pytest.mark.unit
@patch("jd_analyzer.requests.post")
def test_analyze_job_description_returns_dict_with_three_keys(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": '{"technologies": ["Python"], "requirements": ["5 years"], "emphasis_areas": ["ML"]}'},
    }
    mock_post.return_value = mock_response
    result = analyze_job_description("some job description")
    assert isinstance(result, dict)
    assert "technologies" in result
    assert "requirements" in result
    assert "emphasis_areas" in result


@pytest.mark.unit
@patch("jd_analyzer.requests.post")
def test_analyze_job_description_returns_none_on_json_parse_failure(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": "not json at all"},
    }
    mock_post.return_value = mock_response
    result = analyze_job_description("some job description")
    assert result is None


@pytest.mark.unit
@patch("jd_analyzer.requests.post")
def test_analyze_job_description_returns_none_on_missing_required_keys(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": '{"technologies": [], "requirements": []}'},
    }
    mock_post.return_value = mock_response
    result = analyze_job_description("some job description")
    assert result is None


@pytest.mark.unit
@patch("jd_analyzer.requests.post")
def test_analyze_job_description_returns_none_on_connection_error(mock_post):
    mock_post.side_effect = requests.ConnectionError("refused")
    result = analyze_job_description("some job description")
    assert result is None


@pytest.mark.unit
@patch("jd_analyzer.requests.post")
def test_analyze_job_description_returns_none_on_truncation(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "length",
        "message": {"content": ""},
    }
    mock_post.return_value = mock_response
    result = analyze_job_description("some job description")
    assert result is None


@pytest.mark.unit
@patch("jd_analyzer.requests.post")
def test_analyze_job_description_returns_none_on_fence_wrapped_valid_json(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "done_reason": "stop",
        "message": {"content": '```json\n{"technologies": ["Go"], "requirements": ["3 years"], "emphasis_areas": ["backend"]}\n```'},
    }
    mock_post.return_value = mock_response
    result = analyze_job_description("some job description")
    assert isinstance(result, dict)
    assert result is not None
