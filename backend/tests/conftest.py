"""Keep automated tests offline regardless of developer environment settings."""
import pytest

from app.agents import llm
from app.config import Settings


@pytest.fixture(autouse=True)
def offline_llm_settings(monkeypatch):
    settings = Settings(
        _env_file=None, llm_provider="mock", llm_api_key="",
        llm_base_url="", llm_model="test-model",
    )
    monkeypatch.setattr(llm, "get_settings", lambda: settings)
