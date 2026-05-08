import pytest
from config import Settings


def test_dashscope_settings_read_uppercase_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://dashscope.example/v1")
    monkeypatch.setenv("DASHSCOPE_MODEL", "qwen-test")
    monkeypatch.setenv("DASHSCOPE_CLASSIFIER_MODEL", "qwen-classifier-test")

    settings = Settings()

    assert settings.dashscope_api_key == "test-key"
    assert settings.dashscope_base_url == "https://dashscope.example/v1"
    assert settings.dashscope_model == "qwen-test"
    assert settings.dashscope_classifier_model == "qwen-classifier-test"
