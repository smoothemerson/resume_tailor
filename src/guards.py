import re

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


def _extract_section(text: str, section_name: str) -> str | None:
    pattern = rf'\\header\{{{re.escape(section_name)}\}}(.*?)(?=\\header\{{|$)'
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1) if m else None


def _extract_technologies(section_text: str) -> set[str]:
    cleaned = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', section_text)
    return {t.strip() for t in cleaned.split(',') if t.strip()}


def _check_technology_substitution(original: str, tailored: str) -> None:
    try:
        original_section = _extract_section(original, 'Skills')
        tailored_section = _extract_section(tailored, 'Skills')
        if original_section is None or tailored_section is None:
            return
        original_techs = _extract_technologies(original_section)
        tailored_techs = _extract_technologies(tailored_section)
        removed = original_techs - tailored_techs
        added = tailored_techs - original_techs
        if removed and added:
            logger.warning(f"Technology substitution in Skills: removed {sorted(removed)}, added {sorted(added)}")
        elif removed:
            logger.warning(f"Technologies removed from Skills: {sorted(removed)}")
        elif added:
            logger.warning(f"Technologies added to Skills not in original: {sorted(added)}")
    except Exception as exc:
        logger.warning(f"Technology substitution check failed: {exc}")


def _check_protected_sections(original: str, tailored: str) -> None:
    try:
        _contact_pattern = r'\\begin\{center\}(.*?)\\end\{center\}'
        original_contact_m = re.search(_contact_pattern, original, re.DOTALL)
        tailored_contact_m = re.search(_contact_pattern, tailored, re.DOTALL)
        if original_contact_m is not None and tailored_contact_m is not None:
            if original_contact_m.group(1).strip() != tailored_contact_m.group(1).strip():
                logger.warning("Contact block was modified in tailored output.")
        original_education = _extract_section(original, 'Education')
        tailored_education = _extract_section(tailored, 'Education')
        if original_education is not None and tailored_education is not None:
            if original_education.strip() != tailored_education.strip():
                logger.warning("Education section was modified in tailored output.")
        original_languages = _extract_section(original, 'Languages')
        tailored_languages = _extract_section(tailored, 'Languages')
        if original_languages is not None and tailored_languages is not None:
            if original_languages.strip() != tailored_languages.strip():
                logger.warning("Languages section was modified in tailored output.")
        original_headers = set(_EMPLOYER_PATTERN.findall(original))
        tailored_headers = set(_EMPLOYER_PATTERN.findall(tailored))
        for header in original_headers - tailored_headers:
            logger.warning(f'Employer header changed or removed: "{header[0]}"')
        _project_pattern = r'\\href\{([^}]+)\}\{\\textbf\{([^}]+)\}\}'
        original_projects = set(re.findall(_project_pattern, original))
        tailored_projects = set(re.findall(_project_pattern, tailored))
        for url, name in original_projects - tailored_projects:
            logger.warning(f'Project anchor changed or removed: "{name}" ({url})')
    except Exception as exc:
        logger.warning(f"Protected sections check failed: {exc}")


def run_guards(original_text: str, tailored_text: str, fences_stripped: bool = False) -> None:
    _check_missing_sections(original_text, tailored_text)
    _check_format_violations(tailored_text, fences_stripped)
    _check_hallucinated_employers(original_text, tailored_text)
    _check_technology_substitution(original_text, tailored_text)
    _check_protected_sections(original_text, tailored_text)
