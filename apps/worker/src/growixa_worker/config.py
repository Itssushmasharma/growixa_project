from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "info"
    rabbitmq_url: str
    database_url: str
    # Fernet key for decrypting SMTP credentials written by growixa_api's integrations
    # module (DEC-GRX-009) — must match that service's `encryption_key` setting exactly,
    # since both apps encrypt/decrypt the same `email_provider_connections` rows. Same
    # local-dev-only literal default as growixa_api.config.Settings.encryption_key.
    encryption_key: str = "U640ORbquCvIAZca0r5qqd173t669iSoJ3gSuoGGSr0="
    # Public base URL of growixa_api, used to build the unsubscribe link embedded in
    # every outbound campaign email (GRX-EMAIL-005) — points at the same origin
    # recipients' browsers must be able to reach, not an internal container hostname.
    api_public_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
