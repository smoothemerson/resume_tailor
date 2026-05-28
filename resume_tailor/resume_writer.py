from pathlib import Path
from datetime import datetime


def write_resume(content: str, output_dir: Path) -> Path:
    """Write tailored LaTeX content to a timestamped file under output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tailored_resume_{timestamp}.tex"
    output_path.write_text(content, encoding="utf-8")
    return output_path
