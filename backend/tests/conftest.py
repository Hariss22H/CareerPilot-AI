import pytest

import app.main as main


@pytest.fixture(autouse=True)
def isolate_external_services(monkeypatch):
    monkeypatch.setattr(main.settings, "mongodb_uri", "")
    monkeypatch.setattr(main.settings, "openai_api_key", "")
    monkeypatch.setattr(main.settings, "gemini_api_key", "")
