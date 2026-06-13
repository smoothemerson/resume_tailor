import re
import sys

from log_manager import logger

_EMPLOYER_PATTERN = re.compile(r'\\employer\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}')


def _check_missing_sections(original: str, tailored: str) -> None:
    try:
        original_sections = re.findall(r'\\header\{([^}]+)\}', original)
        for section in original_sections:
            if f'\\header{{{section}}}' not in tailored:
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
        if re.search(r'\*\*[^*]+\*\*', tailored):
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
        for name, dates, title in tailored_employers:
            if (name, dates, title) not in original_employers:
                logger.warning(f'Employer "{name}" in tailored output was not in original resume — possible hallucination.')
    except Exception as exc:
        logger.warning(f"Employer check failed: {exc}")


def _check_fabricated_technologies(original: str, tailored: str, jd_technologies: list | None) -> None:
    if not jd_technologies:
        return
    try:
        for tech in jd_technologies:
            if not isinstance(tech, str) or len(tech.strip()) < 2:
                continue
            pattern = re.compile(
                r'(?<![A-Za-z0-9])' + re.escape(tech.strip()) + r'(?![A-Za-z0-9])',
                re.IGNORECASE,
            )
            if not pattern.search(original) and pattern.search(tailored):
                logger.warning(
                    f'Technology "{tech}" appears in tailored output but not in base resume — possible fabrication.'
                )
    except Exception as exc:
        logger.warning(f"Technology fidelity check failed: {exc}")


def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False, jd_technologies: list | None = None) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
    _check_fabricated_technologies(original_text, tailored_text, jd_technologies)
