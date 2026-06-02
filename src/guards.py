import re
import sys

from log_manager import logger

_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')


def _check_missing_sections(original: str, tailored: str) -> None:
    try:
        original_sections = re.findall(r'\\header\{([^}]+)\}', original)
        for section in original_sections:
            if section not in tailored:
                logger.warning(f'Section "{section}" missing from tailored output.')
    except Exception as exc:
        logger.warning(f"Section check failed: {exc}")


def _check_format_violations(tailored: str, fences_stripped: bool) -> None:
    try:
        if fences_stripped:
            logger.warning("LLM returned markdown fences that were stripped from output.")
        if "```" in tailored:
            logger.warning("Tailored output contains inline code fences.")
        if re.search(r'(?m)^#{1,6} ', tailored):
            logger.warning("Tailored output contains markdown heading markers.")
        if re.search(r'\*\*\S[^*]*\S\*\*', tailored):
            logger.warning("Tailored output contains markdown bold markers.")
    except Exception as exc:
        logger.warning(f"Format violation check failed: {exc}")


def _check_hallucinated_employers(original: str, tailored: str) -> None:
    try:
        original_employers = _EMPLOYER_PATTERN.findall(original)
        tailored_employers = _EMPLOYER_PATTERN.findall(tailored)
        for name, dates, title in original_employers:
            if (name, dates, title) not in tailored_employers:
                logger.warning(f'Employer "{name}" from original resume not found in tailored output.')
    except Exception as exc:
        logger.warning(f"Employer check failed: {exc}")


def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
