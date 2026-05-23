from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM 백엔드
    llm_base_url: str = "http://localhost:8080"
    llm_default_model: str = "gemma-4-2b"
    llm_request_timeout: int | None = None
    llm_api_key: str | None = None
    llm_min_request_interval: float = 0.0

    # 서버
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "info"


settings = Settings()
