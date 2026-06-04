import pytest
import requests
from config import OLLAMA_BASE_URL


@pytest.fixture(scope="session")
def ollama_available() -> bool:
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False


@pytest.fixture
def require_ollama(ollama_available: bool) -> None:
    if not ollama_available:
        pytest.skip("Ollama not available")
