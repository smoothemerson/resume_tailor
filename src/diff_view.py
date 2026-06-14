import difflib
import sys

_GREEN = "\033[32m"
_RED = "\033[31m"
_RESET = "\033[0m"


def _normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    result: list[str] = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result)


def _colorize(line: str) -> str:
    if line.startswith("+") and not line.startswith("+++"):
        return _GREEN + line + _RESET
    if line.startswith("-") and not line.startswith("---"):
        return _RED + line + _RESET
    return line


def show_diff(original: str, tailored: str) -> None:
    if not sys.stdout.isatty():
        return
    norm_orig = _normalize(original)
    norm_tail = _normalize(tailored)
    diff = list(
        difflib.unified_diff(
            norm_orig.splitlines(),
            norm_tail.splitlines(),
            fromfile="original",
            tofile="tailored",
            lineterm="",
        )
    )
    if not diff:
        return
    for line in diff:
        print(_colorize(line))
