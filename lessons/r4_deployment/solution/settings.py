from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="R4_", env_file=".env", extra="ignore")

    environment: Literal["dev", "test", "prod"] = "dev"
    secret_key: SecretStr | None = None
    allowed_hosts: list[str] = ["*"]  # env: R4_ALLOWED_HOSTS='["api.example.com"]'
    version: str = "dev"

    @model_validator(mode="after")
    def production_guards(self):
        """Fail fast at boot. A misconfigured prod deploy should crash immediately, not leak later."""
        if self.environment == "prod":
            if self.secret_key is None or len(self.secret_key.get_secret_value()) < 32:
                raise ValueError("R4_SECRET_KEY must be set (>= 32 chars) in prod")
            if "*" in self.allowed_hosts:
                raise ValueError("R4_ALLOWED_HOSTS must list real hostnames in prod")
        return self

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"
