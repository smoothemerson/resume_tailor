import pytest
from unittest.mock import patch

from guards import _check_technology_substitution


@pytest.mark.unit
def test_technology_substitution_warns_on_substitution():
    original = r"\header{Skills}" + "\nPython, Java\n" + r"\header{Education}"
    tailored = r"\header{Skills}" + "\nPython, Go\n" + r"\header{Education}"
    with patch("guards.logger") as mock_logger:
        _check_technology_substitution(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Java" in c for c in calls)
        assert any("Go" in c for c in calls)


@pytest.mark.unit
def test_technology_substitution_warns_on_removal_only():
    original = r"\header{Skills}" + "\nPython, Java\n" + r"\header{Education}"
    tailored = r"\header{Skills}" + "\nPython\n" + r"\header{Education}"
    with patch("guards.logger") as mock_logger:
        _check_technology_substitution(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Java" in c for c in calls)


@pytest.mark.unit
def test_technology_substitution_warns_on_addition_only():
    original = r"\header{Skills}" + "\nPython\n" + r"\header{Education}"
    tailored = r"\header{Skills}" + "\nPython, Go\n" + r"\header{Education}"
    with patch("guards.logger") as mock_logger:
        _check_technology_substitution(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Go" in c for c in calls)


@pytest.mark.unit
def test_technology_substitution_silent_for_identical():
    original = r"\header{Skills}" + "\nPython, Java\n" + r"\header{Education}"
    tailored = r"\header{Skills}" + "\nPython, Java\n" + r"\header{Education}"
    with patch("guards.logger") as mock_logger:
        _check_technology_substitution(original, tailored)
        mock_logger.warning.assert_not_called()


@pytest.mark.unit
def test_technology_substitution_silent_for_no_skills_section():
    original = r"\header{Experience}" + "\nSome experience content\n" + r"\header{Education}"
    tailored = r"\header{Experience}" + "\nSome experience content\n" + r"\header{Education}"
    with patch("guards.logger") as mock_logger:
        _check_technology_substitution(original, tailored)
        mock_logger.warning.assert_not_called()


@pytest.mark.unit
def test_technology_substitution_malformed_input_no_raise():
    _check_technology_substitution(None, None)
