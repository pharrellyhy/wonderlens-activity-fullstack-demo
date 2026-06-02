from agents import script_agent
from config import get_settings


def test_script_agent_dashscope_client_ignores_proxy_environment(monkeypatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://dashscope.example/v1")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    get_settings.cache_clear()
    script_agent._get_client.cache_clear()

    client = script_agent._get_client()

    assert client._client.trust_env is False
