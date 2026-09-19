from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / ".env").exists():
            return parent
    return current.parents[3] if len(current.parents) > 3 else current.parent


REPOSITORY_ROOT = _find_repo_root()


class Settings(BaseSettings):
    app_name: str = "Sahachari API"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    database_url: str = "sqlite:///./sahachari.db"
    cors_origins: list[str] = [
        "*",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ]
    supabase_project_ref: str | None = "oqknqbpaqpwjimpngnyx"
    supabase_url: str | None = "https://oqknqbpaqpwjimpngnyx.supabase.co"
    supabase_publishable_key: str | None = "sb_publishable_okzDXNucTtH9UMT2KMMpWQ_ukCCmweG"
    supabase_anon_key: str | None = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9xa25xYnBhcXB3amltcG5nbnl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk3MzU1ODAsImV4cCI6MjEwNTMxMTU4MH0.j2FICCBLxfeo48Cqe8SsLMVTMIDcD1n1p_FF9_0q5Os"
    )
    supabase_service_role_key: str | None = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9xa25xYnBhcXB3amltcG5nbnl4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTczNTU4MCwiZXhwIjoyMTA1MzExNTgwfQ.hAOFHBqFnZQYDT4hNbsQMBVNK5fkvh3mEjqkFhlYGWY"
    )
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
    exotel_exophone: str | None = "+914045902294"
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
        env_file=(
            REPOSITORY_ROOT / ".env",
            REPOSITORY_ROOT / ".env.local",
            Path(__file__).resolve().parents[3] / ".env",
            Path(__file__).resolve().parents[2] / ".env",
            Path.cwd() / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("supabase_url", mode="before")
    @classmethod
    def normalize_supabase_url(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip().strip("'").strip('"')
            if cleaned and not cleaned.startswith(("http://", "https://")):
                return f"https://{cleaned}"
            return cleaned.rstrip("/") if cleaned else cleaned
        return value

    @field_validator("supabase_anon_key", "supabase_service_role_key", mode="before")
    @classmethod
    def clean_supabase_keys(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().strip("'").strip('"')
        return value

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
