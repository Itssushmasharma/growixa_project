import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Mirrors growixa_api.config's same pattern: when running pytest, ENVIRONMENT is set to
# "test" via pyproject.toml's pytest-env config, so tests load .env.test (a separate
# growixa_test database) instead of .env (the live dev database) — integration tests'
# fixture teardowns DELETE rows, and must never do that against dev/seed data.
_env_file = ".env.test" if os.getenv("ENVIRONMENT") == "test" else ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file, extra="ignore")

    environment: str = "local"
    log_level: str = "info"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    database_url: str = (
        "postgresql+asyncpg://growixa:growixa_test_secret@localhost:5432/growixa_test"
    )
    redis_url: str = "redis://localhost:6379/0"
    # Fernet key for decrypting SMTP credentials written by growixa_api's integrations
    # module (DEC-GRX-009) — must match that service's `encryption_key` setting exactly,
    # since both apps encrypt/decrypt the same `email_provider_connections` rows. Same
    # local-dev-only literal default as growixa_api.config.Settings.encryption_key.
    encryption_key: str = "U640ORbquCvIAZca0r5qqd173t669iSoJ3gSuoGGSr0="
    # Public base URL of growixa_api, used to build the unsubscribe link embedded in
    # every outbound campaign email (GRX-EMAIL-005) — points at the same origin
    # recipients' browsers must be able to reach, not an internal container hostname.
    api_public_url: str = "http://localhost:8000"

    # Slice 5 (Social Publishing, GRX-SOCIAL-008): needed for the inline near-expiry
    # token refresh check before each publish attempt. Must match growixa_api's own
    # instagram_app_id/instagram_app_secret exactly, same reasoning as encryption_key.
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    instagram_graph_api_version: str = "v21.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
