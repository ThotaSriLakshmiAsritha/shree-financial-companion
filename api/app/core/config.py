from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_name: str = "Sahachari API"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    database_url: str = "sqlite:///./sahachari.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    supabase_project_ref: str | None = None
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_database_url_template: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout_seconds: float = 20.0
    exotel_api_key: str | None = None
    exotel_api_token: str | None = None
    exotel_account_sid: str | None = None
    exotel_base_url: str = "https://api.in.exotel.com"
    exotel_webhook_secret: str | None = None
    exotel_exophone: str | None = None
    sarvam_api_key: str | None = None
    sarvam_base_url: str = "https://api.sarvam.ai"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_stt_mode: str = "transcribe"
    sarvam_tts_model: str = "bulbul:v3"
    # Priya is a Sarvam Bulbul v3 female voice with multilingual support.
    sarvam_tts_speaker: str = "priya"
    sarvam_timeout_seconds: float = 30.0
    sarvam_agent_id: str | None = None
    sarvam_agent_tool_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_ROOT / ".env", REPOSITORY_ROOT / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("sqlite:///./"):
            relative_path = Path(value.removeprefix("sqlite:///./"))
            return f"sqlite:///{(REPOSITORY_ROOT / relative_path).as_posix()}"
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
