import sys
import unittest
from unittest.mock import patch

from keyword_matcher import show_keyword_match


class TestShowKeywordMatchTTYGate(unittest.TestCase):
    def test_suppressed_when_not_tty(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            with patch("builtins.print") as mock_print:
                show_keyword_match({"technologies": ["Python"], "requirements": [], "emphasis_areas": []}, "Python is great")
                mock_print.assert_not_called()

    def test_shows_output_when_tty(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match({"technologies": ["Python"], "requirements": [], "emphasis_areas": []}, "Python developer")
            self.assertTrue(len(printed) > 0)


class TestShowKeywordMatchOutput(unittest.TestCase):
    def test_header_format_with_match(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match({"technologies": ["Python", "FastAPI"], "requirements": [], "emphasis_areas": []}, "Python developer")
            self.assertEqual(printed[0], "Keyword match: 1/2")
            self.assertTrue(printed[1].startswith("  "))
            self.assertIn("Python", printed[1])

    def test_header_format_zero_match(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match({"technologies": ["Rust"], "requirements": [], "emphasis_areas": []}, "No relevant content")
            self.assertEqual(printed[0], "Keyword match: 0/1")
            self.assertEqual(len(printed), 1)

    def test_all_three_fields_pooled(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match(
                    {"technologies": ["Python"], "requirements": ["FastAPI"], "emphasis_areas": ["Docker"]},
                    "Python FastAPI Docker"
                )
            self.assertEqual(printed[0], "Keyword match: 3/3")


class TestShowKeywordMatchWholeWord(unittest.TestCase):
    def test_substring_not_matched(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match({"technologies": ["Python"], "requirements": [], "emphasis_areas": []}, "Pythonista developer")
            self.assertEqual(printed[0], "Keyword match: 0/1")

    def test_whole_word_matched_adjacent_punctuation(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match({"technologies": ["Python"], "requirements": [], "emphasis_areas": []}, "I use Python, and FastAPI")
            self.assertEqual(printed[0], "Keyword match: 1/1")


class TestShowKeywordMatchStopWords(unittest.TestCase):
    def test_stop_words_excluded_from_pool(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match(
                    {"technologies": ["and", "the", "Python"], "requirements": [], "emphasis_areas": []},
                    "and the Python"
                )
            self.assertEqual(printed[0], "Keyword match: 1/1")

    def test_single_char_excluded(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch("builtins.print", side_effect=lambda *a: printed.append(a[0] if a else "")):
                show_keyword_match(
                    {"technologies": ["C", "Python"], "requirements": [], "emphasis_areas": []},
                    "C Python"
                )
            self.assertEqual(printed[0], "Keyword match: 1/1")


class TestShowKeywordMatchNeverRaises(unittest.TestCase):
    def test_empty_dict_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            show_keyword_match({}, "any text")

    def test_missing_keys_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            show_keyword_match({"technologies": ["Python"]}, "text")

    def test_not_tty_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            show_keyword_match({}, "")

    def test_empty_tailored_text_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            show_keyword_match({"technologies": ["Python"], "requirements": [], "emphasis_areas": []}, "")


if __name__ == "__main__":
    unittest.main()
