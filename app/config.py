"""
Centralized configuration management using pydantic-settings.

All application settings are loaded from environment variables or a .env file.
Settings are cached via @lru_cache to ensure a single instance across the app.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openweather_api_key: str = ""
    tavily_api_key: str = ""
    database_url: str = "./data/agent.db"
    checkpoint_db_url: str = "./data/checkpoints.db"
    ollama_model: str = "qwen2.5:7b-instruct-q4_K_M"
    ollama_base_url: str = "http://localhost:11434"
    agent_max_iterations: int = 10
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()
