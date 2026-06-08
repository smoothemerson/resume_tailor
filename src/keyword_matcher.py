import re
import sys

STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "to", "for", "with",
    "is", "are", "be", "on", "at",
})


def show_keyword_match(analysis: dict, tailored_text: str) -> None:
    if not sys.stdout.isatty():
        return
    try:
        keywords = _collect_keywords(analysis)
        matched = _match_keywords(keywords, tailored_text)
        _print_summary(matched, len(keywords))
    except Exception:
        return


def _collect_keywords(analysis: dict) -> list[str]:
    pool: list[str] = []
    for field in ("technologies", "requirements", "emphasis_areas"):
        for kw in analysis.get(field, []):
            if kw.lower() in STOP_WORDS:
                continue
            if len(kw.strip()) <= 1:
                continue
            pool.append(kw)
    return pool


def _match_keywords(keywords: list[str], tailored_text: str) -> list[str]:
    matched: list[str] = []
    for kw in keywords:
        pattern = re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE)
        if pattern.search(tailored_text):
            matched.append(kw)
    return matched


def _print_summary(matched: list[str], total: int) -> None:
    print(f"Keyword match: {len(matched)}/{total}")
    if matched:
        print(f"  {', '.join(matched)}")
