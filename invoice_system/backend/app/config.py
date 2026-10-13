"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "sqlite:///./invoice_system.db"
    upload_dir: str = "./uploads"
    tesseract_cmd: str = "tesseract"
    log_level: str = "INFO"

    # LLM integration (set in .env)
    llm_provider: str = "claude"   # "claude" | "openai"
    llm_api_key: str = ""          # LLM_API_KEY in .env

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
