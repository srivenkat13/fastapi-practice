from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed config, read from environment variables (BOOKSHELF_APP_NAME=...) and an optional .env file."""

    model_config = SettingsConfigDict(env_prefix="BOOKSHELF_", env_file=".env", extra="ignore")

    app_name: str = "Bookshelf"
    debug: bool = False
    max_page_size: int = 50


@lru_cache  # read and validate the env once; tests call get_settings.cache_clear()
def get_settings() -> Settings:
    return Settings()
