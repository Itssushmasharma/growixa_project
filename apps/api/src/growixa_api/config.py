from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "info"

    database_url: str
    redis_url: str
    rabbitmq_url: str

    jwt_signing_key: str = "CHANGE_ME_LOCAL_DEV_ONLY"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    invitation_ttl_days: int = 7
    password_reset_ttl_minutes: int = 30

    # Redis-backed fixed-window rate limit shared by /auth/login and
    # /auth/password-reset/request (THREAT_MODEL.md T1/T12) — a conservative default per
    # AUTHENTICATION.md's "low single-digit attempts per short window" guidance.
    rate_limit_max_attempts: int = 5
    rate_limit_window_seconds: int = 60

    # Argon2id cost parameters — configurable per AUTHENTICATION.md so cost can be raised as
    # hardware improves without a schema/code change. Defaults match argon2-cffi's own
    # OWASP-baseline PasswordHasher defaults.
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
