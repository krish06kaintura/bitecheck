"""
Centralized Configuration Module for BiteCheck India.
Uses Pydantic Settings for strongly-typed, validated environment configuration.
"""

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory: points to the root of the bitecheck project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    Validates types and provides sensible defaults for local development.
    """
    # Multimodal Vision API
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API Key for Agent 1 Multimodal Vision",
        validation_alias="GEMINI_API_KEY"
    )

    # Server & Environment
    app_env: Literal["development", "production", "test"] = Field(
        default="development",
        validation_alias="APP_ENV"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL"
    )
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    # Knowledge Base Directory Path
    data_dir: Path = Field(default=DATA_DIR)

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Singleton settings instance for the entire application
settings = Settings()
