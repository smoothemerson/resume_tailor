import unittest
from unittest.mock import patch

from guards import run_guards


class TestCheckMissingSections(unittest.TestCase):
    def test_missing_section_triggers_warning(self):
        original = "\\header{Skills}\n\\header{Experience}"
        tailored = "\\header{Experience}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            mock_logger.warning.assert_called_once_with(
                'Section "Skills" missing from tailored output.'
            )

    def test_no_missing_sections_no_warning(self):
        original = "\\header{Skills}\n\\header{Experience}"
        tailored = "\\header{Skills}\n\\header{Experience}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            mock_logger.warning.assert_not_called()

    def test_original_with_no_headers_no_warning(self):
        original = "\\documentclass{article}\n\\end{document}"
        tailored = "\\documentclass{article}\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            mock_logger.warning.assert_not_called()

    def test_multiple_missing_sections(self):
        original = "\\header{Skills}\n\\header{Experience}\n\\header{Education}"
        tailored = "\\header{Education}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            self.assertEqual(mock_logger.warning.call_count, 2)


class TestCheckFormatViolations(unittest.TestCase):
    def test_fences_stripped_true_triggers_warning(self):
        tailored = "\\documentclass{article}\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards("", tailored, fences_stripped=True)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(any("LLM returned markdown fences" in c for c in calls))

    def test_inline_code_fence_triggers_warning(self):
        tailored = "\\documentclass{article}\n```python\ncode\n```\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards("", tailored, fences_stripped=False)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(any("inline code fences" in c for c in calls))

    def test_markdown_heading_triggers_warning(self):
        tailored = "\\documentclass{article}\n# Heading\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards("", tailored, fences_stripped=False)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(any("markdown heading markers" in c for c in calls))

    def test_clean_latex_no_warnings(self):
        tailored = "\\documentclass{article}\n\\begin{document}\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards("", tailored, fences_stripped=False)
            mock_logger.warning.assert_not_called()


class TestCheckHallucinatedEmployers(unittest.TestCase):
    def test_zero_employers_in_original_no_warning(self):
        original = "\\documentclass{article}\n\\end{document}"
        tailored = "\\documentclass{article}\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            mock_logger.warning.assert_not_called()

    def test_employer_in_original_missing_from_tailored_triggers_warning(self):
        original = r"\textbf{Acme Corp}\textbf{ | Engineer}"
        tailored = r"\documentclass{article}\n\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(any("Acme Corp" in c for c in calls))

    def test_employer_in_both_original_and_tailored_no_warning(self):
        original = r"\textbf{Acme Corp}\textbf{ | Engineer}"
        tailored = r"\textbf{Acme Corp}\textbf{ | Engineer}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            mock_logger.warning.assert_not_called()


class TestRunGuardsNeverRaises(unittest.TestCase):
    def test_run_guards_empty_strings_no_exception(self):
        run_guards("", "")

    def test_run_guards_malformed_input_no_exception(self):
        run_guards(None, None)

    def test_run_guards_fences_stripped_no_exception(self):
        run_guards("", "", fences_stripped=True)

    def test_run_guards_malformed_jd_technologies_no_exception(self):
        run_guards("", "", jd_technologies=[None, 123, "C"])


class TestCheckFabricatedTechnologies(unittest.TestCase):
    def test_jd_technology_absent_from_original_present_in_tailored_warns(self):
        original = "\\documentclass{article}\\end{document}"
        tailored = "\\documentclass{article} Kubernetes cluster \\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored, jd_technologies=["Kubernetes"])
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(any("Kubernetes" in c for c in calls))
            self.assertTrue(any("possible fabrication" in c for c in calls))

    def test_jd_technology_present_in_both_no_warning(self):
        original = "Python developer"
        tailored = "Python developer"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored, jd_technologies=["Python"])
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertFalse(any("possible fabrication" in c for c in calls))

    def test_jd_technologies_none_no_warning_no_raise(self):
        with patch("guards.logger") as mock_logger:
            run_guards("original", "tailored", jd_technologies=None)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertFalse(any("possible fabrication" in c for c in calls))

    def test_jd_technologies_empty_list_no_warning(self):
        with patch("guards.logger") as mock_logger:
            run_guards("original", "tailored", jd_technologies=[])
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertFalse(any("possible fabrication" in c for c in calls))

    def test_matching_is_case_insensitive_and_token_bounded(self):
        original = "\\documentclass{article}\\end{document}"
        tailored = "kubernetes cluster"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored, jd_technologies=["Kubernetes"])
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(any("possible fabrication" in c for c in calls))

        original2 = "JavaScript developer"
        tailored2 = "JavaScript developer"
        with patch("guards.logger") as mock_logger2:
            run_guards(original2, tailored2, jd_technologies=["Java"])
            calls2 = [str(c) for c in mock_logger2.warning.call_args_list]
            self.assertFalse(any("possible fabrication" in c for c in calls2))

    def test_technology_absent_from_both_original_and_tailored_no_warning(self):
        original = "Python developer"
        tailored = "Python developer"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored, jd_technologies=["Kubernetes"])
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertFalse(any("possible fabrication" in c for c in calls))

    def test_malformed_entries_in_list_never_raise(self):
        run_guards("original", "tailored", jd_technologies=[None, 123, "C"])

    def test_single_character_technology_names_skipped(self):
        original = "developer"
        tailored = "C developer"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored, jd_technologies=["C"])
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertFalse(any("possible fabrication" in c for c in calls))


if __name__ == "__main__":
    unittest.main()
