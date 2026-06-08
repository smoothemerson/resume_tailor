import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

from guards import run_guards


class TestCheckMissingSections(unittest.TestCase):
    def test_missing_section_triggers_warning(self):
        original = "\\header{Skills}\n\\header{Experience}"
        tailored = "\\header{Experience}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            mock_logger.warning.assert_called_once_with('Section "Skills" missing from tailored output.')

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
            self.assertTrue(
                any("LLM returned markdown fences" in c for c in calls)
            )

    def test_inline_code_fence_triggers_warning(self):
        tailored = "\\documentclass{article}\n```python\ncode\n```\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards("", tailored, fences_stripped=False)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(
                any("inline code fences" in c for c in calls)
            )

    def test_markdown_heading_triggers_warning(self):
        tailored = "\\documentclass{article}\n# Heading\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards("", tailored, fences_stripped=False)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(
                any("markdown heading markers" in c for c in calls)
            )

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
        original = "\\employer{Acme Corp}{2022}{Engineer}"
        tailored = "\\documentclass{article}\n\\end{document}"
        with patch("guards.logger") as mock_logger:
            run_guards(original, tailored)
            calls = [str(c) for c in mock_logger.warning.call_args_list]
            self.assertTrue(
                any("Acme Corp" in c for c in calls)
            )

    def test_employer_in_both_original_and_tailored_no_warning(self):
        original = "\\employer{Acme Corp}{2022}{Engineer}"
        tailored = "\\employer{Acme Corp}{2022}{Engineer}"
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


if __name__ == "__main__":
    unittest.main()
