import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli import main
from llm_client import TailorResult


class TestInputLoop(unittest.TestCase):
    @patch("sys.argv", ["resume-tailor"])
    @patch("cli.write_resume")
    @patch("cli.generate_tailored_resume")
    @patch("cli.read_resume")
    @patch("builtins.input")
    @patch("cli.run_guards")
    def test_end_sentinel_breaks_loop(self, mock_guards, mock_input, mock_read, mock_generate, mock_write):
        mock_input.side_effect = ["line one", "line two", "END"]
        mock_read.return_value = "resume text"
        mock_generate.return_value = TailorResult(content="\\documentclass{article}\n\\end{document}", fences_stripped=False)
        mock_write.return_value = Path("/tmp/tailored_resume_test.tex")

        with patch("builtins.print"):
            main()

        call_args = mock_generate.call_args
        self.assertIn("line one", call_args[0][1])
        self.assertIn("line two", call_args[0][1])
        mock_guards.assert_called_once_with(
            "resume text",
            "\\documentclass{article}\n\\end{document}",
            False,
        )

    @patch("sys.argv", ["resume-tailor"])
    @patch("cli.write_resume")
    @patch("cli.generate_tailored_resume")
    @patch("cli.read_resume")
    @patch("builtins.input")
    @patch("cli.run_guards")
    def test_eof_treated_as_submission(self, mock_guards, mock_input, mock_read, mock_generate, mock_write):
        mock_input.side_effect = ["line one", "line two", EOFError()]
        mock_read.return_value = "resume text"
        mock_generate.return_value = TailorResult(content="\\documentclass{article}\n\\end{document}", fences_stripped=False)
        mock_write.return_value = Path("/tmp/tailored_resume_test.tex")

        with patch("builtins.print"):
            main()

        mock_generate.assert_called_once()

    @patch("sys.argv", ["resume-tailor"])
    @patch("builtins.input")
    def test_empty_jd_exits_1(self, mock_input):
        mock_input.side_effect = ["END"]

        with self.assertRaises(SystemExit) as cm:
            with patch("builtins.print"):
                main()

        self.assertEqual(cm.exception.code, 1)


class TestErrorHandling(unittest.TestCase):
    @patch("sys.argv", ["resume-tailor"])
    @patch("cli.generate_tailored_resume")
    @patch("cli.read_resume")
    @patch("builtins.input")
    def test_runtime_error_from_llm_exits_1(self, mock_input, mock_read, mock_generate):
        mock_input.side_effect = ["Senior ML Engineer role", "END"]
        mock_read.return_value = "resume text"
        mock_generate.side_effect = RuntimeError("Ollama not reachable")

        with self.assertRaises(SystemExit) as cm:
            with patch("builtins.print"):
                main()

        self.assertEqual(cm.exception.code, 1)

    @patch("sys.argv", ["resume-tailor"])
    @patch("cli.generate_tailored_resume")
    @patch("cli.read_resume")
    @patch("builtins.input")
    def test_value_error_from_llm_exits_1(self, mock_input, mock_read, mock_generate):
        mock_input.side_effect = ["Senior ML Engineer role", "END"]
        mock_read.return_value = "resume text"
        mock_generate.side_effect = ValueError("Invalid LaTeX output")

        with self.assertRaises(SystemExit) as cm:
            with patch("builtins.print"):
                main()

        self.assertEqual(cm.exception.code, 1)


class TestSuccessPath(unittest.TestCase):
    @patch("sys.argv", ["resume-tailor"])
    @patch("cli.write_resume")
    @patch("cli.generate_tailored_resume")
    @patch("cli.read_resume")
    @patch("builtins.input")
    @patch("cli.run_guards")
    def test_progress_message_printed(self, mock_guards, mock_input, mock_read, mock_generate, mock_write):
        mock_input.side_effect = ["Software Engineer job", "END"]
        mock_read.return_value = "resume text"
        mock_generate.return_value = TailorResult(content="\\documentclass{article}\n\\end{document}", fences_stripped=False)
        output_path = MagicMock()
        output_path.resolve.return_value = Path("/tmp/tailored_resume_20260529.tex")
        mock_write.return_value = output_path

        printed_lines = []
        with patch("builtins.print", side_effect=lambda *a, **kw: printed_lines.append(a[0] if a else "")):
            main()

        self.assertTrue(
            any("Tailoring resume" in line for line in printed_lines),
            f"Expected progress message containing 'Tailoring resume' in print calls, got: {printed_lines}",
        )

    @patch("sys.argv", ["resume-tailor"])
    @patch("cli.write_resume")
    @patch("cli.generate_tailored_resume")
    @patch("cli.read_resume")
    @patch("builtins.input")
    @patch("cli.run_guards")
    def test_success_prints_absolute_path(self, mock_guards, mock_input, mock_read, mock_generate, mock_write):
        mock_input.side_effect = ["Software Engineer job", "END"]
        mock_read.return_value = "resume text"
        mock_generate.return_value = TailorResult(content="\\documentclass{article}\n\\end{document}", fences_stripped=False)
        output_path = MagicMock()
        output_path.resolve.return_value = Path("/tmp/tailored_resume_20260529.tex")
        mock_write.return_value = output_path

        printed_lines = []
        with patch("builtins.print", side_effect=lambda *a, **kw: printed_lines.append(a[0] if a else "")):
            main()

        self.assertTrue(
            any("Tailored resume written to:" in line for line in printed_lines)
        )


if __name__ == "__main__":
    unittest.main()
