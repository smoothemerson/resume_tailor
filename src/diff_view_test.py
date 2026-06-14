import unittest
from unittest.mock import patch

from diff_view import show_diff


class TestShowDiffTTYGate(unittest.TestCase):
    def test_suppressed_when_not_tty(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            with patch("builtins.print") as mock_print:
                show_diff("original", "tailored changed")
                mock_print.assert_not_called()

    def test_shows_diff_on_tty(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch(
                "builtins.print",
                side_effect=lambda *a: printed.append(a[0] if a else ""),
            ):
                show_diff("line 1\nline 2", "line 1\nline 2 changed")
            self.assertTrue(any("line 2 changed" in line for line in printed))


class TestShowDiffNormalization(unittest.TestCase):
    def test_trailing_spaces_not_shown_as_diff(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            with patch("builtins.print") as mock_print:
                show_diff("line 1   \nline 2  ", "line 1\nline 2")
                mock_print.assert_not_called()

    def test_blank_line_collapse_not_shown_as_diff(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            with patch("builtins.print") as mock_print:
                # both inputs have >2 blank lines; _normalize caps each run to 2
                show_diff("a\n\n\n\nb", "a\n\n\n\n\nb")
                mock_print.assert_not_called()

    def test_identical_texts_no_output(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            with patch("builtins.print") as mock_print:
                show_diff("same text", "same text")
                mock_print.assert_not_called()


class TestShowDiffColors(unittest.TestCase):
    def test_added_line_is_green(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch(
                "builtins.print",
                side_effect=lambda *a: printed.append(a[0] if a else ""),
            ):
                show_diff("line one", "line two")
            self.assertTrue(any(line.startswith("\033[32m") for line in printed))

    def test_removed_line_is_red(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch(
                "builtins.print",
                side_effect=lambda *a: printed.append(a[0] if a else ""),
            ):
                show_diff("line one", "line two")
            self.assertTrue(any(line.startswith("\033[31m") for line in printed))

    def test_header_plus_not_colored(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch(
                "builtins.print",
                side_effect=lambda *a: printed.append(a[0] if a else ""),
            ):
                show_diff("a", "b")
            self.assertTrue(any(line == "+++ tailored" for line in printed))

    def test_header_minus_not_colored(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            printed = []
            with patch(
                "builtins.print",
                side_effect=lambda *a: printed.append(a[0] if a else ""),
            ):
                show_diff("a", "b")
            self.assertTrue(any(line == "--- original" for line in printed))


class TestShowDiffNeverRaises(unittest.TestCase):
    def test_empty_strings_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            show_diff("", "")

    def test_not_tty_no_exception(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            show_diff("", "")


if __name__ == "__main__":
    unittest.main()
