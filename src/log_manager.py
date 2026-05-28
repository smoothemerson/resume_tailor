import sys


class _Logger:
    def info(self, message: str) -> None:
        print(message, file=sys.stderr)

    def warning(self, message: str) -> None:
        print(f"WARNING: {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        print(f"ERROR: {message}", file=sys.stderr)


logger = _Logger()
