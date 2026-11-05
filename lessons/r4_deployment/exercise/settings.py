from typing import Literal  # noqa: F401

from pydantic import SecretStr, model_validator  # noqa: F401
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """TODO:
    - env_prefix "R4_"
    - environment: "dev" | "test" | "prod" (default "dev")
    - secret_key: SecretStr | None = None
    - allowed_hosts: list[str] = ["*"]
    - version: str = "dev"
    - a model_validator: in prod, secret_key must be set and >= 32 chars, and "*" must not be in allowed_hosts
    - an `is_prod` property
    """

    model_config = SettingsConfigDict(env_prefix="R4_", extra="ignore")

    environment: str = "dev"
    secret_key: str = "changeme"  # 🐛 a default secret silently ships to production
