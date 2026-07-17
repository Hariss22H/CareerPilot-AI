from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = ""
    mongodb_database: str = "careerpilot"
    mongodb_server_selection_timeout_ms: int = 5000
    mongodb_connect_timeout_ms: int = 5000
    jwt_secret: str = "development-only-change-me"
    jwt_expire_minutes: int = 60 * 24
    password_min_length: int = 8
    ai_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    model_name: str = "gemini-2.0-flash"
    frontend_url: str = "http://localhost:5173"
    max_file_size: int = 10 * 1024 * 1024
    min_resume_text_length: int = 80
    ai_timeout_seconds: float = 45
    chat_max_tokens: int = 700
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
