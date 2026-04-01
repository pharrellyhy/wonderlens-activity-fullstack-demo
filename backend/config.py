"""Application configuration loaded from .env (secrets) and config.yaml (app config)."""

import functools
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_YAML_PATH = Path(__file__).parent / "config.yaml"


def _load_yaml_config() -> dict[str, Any]:
    """Load application config values from config.yaml."""
    if _CONFIG_YAML_PATH.exists():
        with open(_CONFIG_YAML_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


_yaml_config: dict[str, Any] = _load_yaml_config()


class Settings(BaseSettings):
    """Unified settings from environment variables and config.yaml."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Secrets — loaded from .env
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    google_application_credentials: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""
    gemini_api_key: str = ""
    ali_api_key: str = ""
    ali_base_url: str = ""

    # App config — defaults from config.yaml, overridable by env vars
    gemini_model: str = str(_yaml_config.get("gemini_model", "gemini-2.5-flash"))
    openai_model: str = str(_yaml_config.get("openai_model", "gpt-5.2"))
    ali_model: str = str(_yaml_config.get("ali_model", "qwen3.5-plus"))
    ali_classifier_model: str = str(_yaml_config.get("ali_classifier_model", "qwen3.5-flash"))
    tts_model: str = str(_yaml_config.get("tts_model", "gemini-2.5-flash-tts"))
    director_timeout_ms: int = int(_yaml_config.get("director_timeout_ms", 200))
    director_max_tokens: int = int(_yaml_config.get("director_max_tokens", 150))
    script_timeout_ms: int = int(_yaml_config.get("script_timeout_ms", 600))
    script_max_tokens: int = int(_yaml_config.get("script_max_tokens", 600))
    script_turn_timeout_ms: int = int(_yaml_config.get("script_turn_timeout_ms", 5000))
    script_turn_max_tokens: int = int(_yaml_config.get("script_turn_max_tokens", 500))
    two_pass_enabled: bool = bool(_yaml_config.get("two_pass_enabled", False))
    planner_max_tokens: int = int(_yaml_config.get("planner_max_tokens", 400))
    planner_temperature: float = float(_yaml_config.get("planner_temperature", 0.3))
    speaker_temperature: float = float(_yaml_config.get("speaker_temperature", 0.7))
    turn_director_enabled: bool = bool(_yaml_config.get("turn_director_enabled", False))
    best_of_n: int = int(_yaml_config.get("best_of_n", 1))
    vision_timeout_ms: int = int(_yaml_config.get("vision_timeout_ms", 5000))
    max_retries: int = int(_yaml_config.get("max_retries", 3))
    db_path: str = str(_yaml_config.get("db_path", "data/demo.db"))
    log_level: str = str(_yaml_config.get("log_level", "INFO"))


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
