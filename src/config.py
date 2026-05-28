from pathlib import Path

_ROOT = Path(__file__).parent.parent

OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "mistral-small3.2:24b"
BASE_RESUME_PATH: Path = _ROOT / "resumes" / "english.tex"
OUTPUT_DIR: Path = _ROOT / "resumes" / "output"
TIMEOUT: tuple[int, int] = (10, 300)
