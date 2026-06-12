import pytest
from unittest.mock import patch

from guards import _check_technology_substitution, _check_protected_sections, run_guards


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


@pytest.mark.unit
def test_protected_sections_warns_on_contact_diff():
    original = r"\begin{center}Name A\end{center}"
    tailored = r"\begin{center}Name B\end{center}"
    with patch("guards.logger") as mock_logger:
        _check_protected_sections(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("contact" in c.lower() for c in calls)


@pytest.mark.unit
def test_protected_sections_warns_on_education_diff():
    original = r"\header{Education}BSc Computer Science\header{Languages}"
    tailored = r"\header{Education}BSc Data Science\header{Languages}"
    with patch("guards.logger") as mock_logger:
        _check_protected_sections(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Education" in c for c in calls)


@pytest.mark.unit
def test_protected_sections_warns_on_languages_diff():
    original = r"\header{Languages}English\header{Experience}"
    tailored = r"\header{Languages}French\header{Experience}"
    with patch("guards.logger") as mock_logger:
        _check_protected_sections(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Languages" in c for c in calls)


@pytest.mark.unit
def test_run_guards_warns_on_employer_header_change():
    original = r"\employer{Acme Corp}{2022}{Engineer}"
    tailored = r"\employer{Beta Corp}{2022}{Engineer}"
    with patch("guards.logger") as mock_logger:
        run_guards(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Acme Corp" in c for c in calls)


@pytest.mark.unit
def test_protected_sections_silent_when_unchanged():
    content = (
        r"\begin{center}Same Name\end{center}"
        + "\n"
        + r"\header{Education}BSc Same\header{Languages}English\header{Experience}"
        + "\n"
        + r"\employer{Same Corp}{2022}{Engineer}"
    )
    with patch("guards.logger") as mock_logger:
        _check_protected_sections(content, content)
        mock_logger.warning.assert_not_called()


@pytest.mark.unit
def test_protected_sections_empty_strings_no_raise():
    _check_protected_sections("", "")


@pytest.mark.unit
def test_run_guards_calls_technology_substitution():
    original = r"\header{Skills}" + "\nPython, Java\n" + r"\header{Education}"
    tailored = r"\header{Skills}" + "\nPython, Go\n" + r"\header{Education}"
    with patch("guards.logger") as mock_logger:
        run_guards(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("Java" in c for c in calls)
        assert any("Go" in c for c in calls)


@pytest.mark.unit
def test_run_guards_warns_on_contact_block_removed():
    original = r"\begin{center}Name A\nEmail A\end{center}"
    tailored = "No contact block here"
    with patch("guards.logger") as mock_logger:
        run_guards(original, tailored)
        calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("contact" in c.lower() for c in calls)
