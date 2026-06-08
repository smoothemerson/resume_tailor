import pytest
import requests
from config import OLLAMA_BASE_URL


@pytest.fixture(scope="session")
def ollama_available() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        response.raise_for_status()
        return True
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
        return False


@pytest.fixture(scope="session")
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")
