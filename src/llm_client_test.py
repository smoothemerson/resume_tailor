import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))

import requests

from llm_client import _strip_fences, _validate_latex, generate_tailored_resume


class TestStripFences(unittest.TestCase):
    def test_strip_latex_fence(self):
        result = _strip_fences("```latex\n\\documentclass{article}\n```")
        self.assertEqual(result, "\\documentclass{article}")

    def test_strip_bare_fence(self):
        result = _strip_fences("```\n\\documentclass{article}\n```")
        self.assertEqual(result, "\\documentclass{article}")

    def test_strip_tex_fence(self):
        result = _strip_fences("```tex\n\\documentclass{article}\n\\end{document}\n```")
        self.assertEqual(result, "\\documentclass{article}\n\\end{document}")

    def test_no_op_on_clean_input(self):
        result = _strip_fences("\\documentclass{article}")
        self.assertEqual(result, "\\documentclass{article}")


class TestValidateLatex(unittest.TestCase):
    def test_valid_latex_returns_text(self):
        text = "\\documentclass{article}\n\\end{document}"
        result = _validate_latex(text)
        self.assertEqual(result, text)

    def test_missing_end_document_raises(self):
        with self.assertRaises(ValueError):
            _validate_latex("\\documentclass{article}")

    def test_missing_documentclass_raises(self):
        with self.assertRaises(ValueError):
            _validate_latex("\\end{document}")

    def test_no_latex_raises(self):
        with self.assertRaises(ValueError):
            _validate_latex("no latex here")


class TestGenerateTailoredResume(unittest.TestCase):
    @patch("llm_client.requests.get")
    def test_health_check_connection_error_raises_runtime_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("connection refused")
        with self.assertRaises(RuntimeError):
            generate_tailored_resume("resume text", "job description")

    @patch("llm_client.requests.post")
    @patch("llm_client.requests.get")
    def test_done_reason_length_raises_runtime_error(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(status_code=200)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "done_reason": "length",
            "message": {"content": ""},
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        with self.assertRaises(RuntimeError):
            generate_tailored_resume("resume text", "job description")

    @patch("llm_client.requests.post")
    @patch("llm_client.requests.get")
    def test_invalid_llm_output_raises_value_error(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(status_code=200)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "done_reason": "stop",
            "message": {"content": "not valid latex at all"},
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        with self.assertRaises(ValueError):
            generate_tailored_resume("resume text", "job description")


if __name__ == "__main__":
    unittest.main()
