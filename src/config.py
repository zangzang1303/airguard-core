from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI20K Agent"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000"

    # LLM
    openai_api_key: str = ""
    openai_base_url: str | None = None
    model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_timeout_seconds: float = Field(default=12.0, gt=0, le=60)
    llm_max_tokens: int = Field(default=280, ge=64, le=1000)

    # Backend tools (the Agent has no DB or MQTT credentials)
    agent_backend_base_url: str = "http://localhost:8000"
    agent_tool_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    agent_tool_max_retries: int = Field(default=1, ge=0, le=3)

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
