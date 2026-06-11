import pytest

from jd_analyzer import _parse_analysis_response


@pytest.mark.unit
def test_parse_valid_json_returns_dict():
    content = '{"technologies": ["Python"], "requirements": ["5 yrs"], "emphasis_areas": ["ML"]}'
    result = _parse_analysis_response(content)
    assert isinstance(result, dict)
    assert set(result.keys()) == {"technologies", "requirements", "emphasis_areas"}


@pytest.mark.unit
def test_parse_missing_key_returns_none():
    content = '{"technologies": ["Python"], "requirements": ["5 yrs"]}'
    assert _parse_analysis_response(content) is None


@pytest.mark.unit
def test_parse_non_list_value_returns_none():
    content = '{"technologies": "Python", "requirements": ["5 yrs"], "emphasis_areas": ["ML"]}'
    assert _parse_analysis_response(content) is None


@pytest.mark.unit
def test_parse_fenced_json_returns_dict():
    content = '```json\n{"technologies": ["Go"], "requirements": ["3 yrs"], "emphasis_areas": ["backend"]}\n```'
    assert _parse_analysis_response(content) is not None


@pytest.mark.unit
def test_parse_non_json_string_returns_none():
    assert _parse_analysis_response("not json at all") is None


@pytest.mark.unit
def test_parse_empty_string_returns_none():
    assert _parse_analysis_response("") is None
