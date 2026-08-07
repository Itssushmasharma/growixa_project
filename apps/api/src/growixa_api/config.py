import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# When running pytest, ENVIRONMENT is set to "test" via .env.test so
# we never accidentally connect to the live dev database.
_env_file = ".env.test" if os.getenv("ENVIRONMENT") == "test" else ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file, extra="ignore")

    environment: str = "local"
    log_level: str = "info"

    database_url: str
    redis_url: str
    rabbitmq_url: str

    # Origins the Next.js frontend runs on locally — needed so browser-based fetches from
    # apps/web can complete credentialed (cookie-based) requests.
    # 3000 is Compose web; 3001 is worktree preview; 3100 is Playwright e2e.
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3100",
    ]

    jwt_signing_key: str = "CHANGE_ME_LOCAL_DEV_ONLY"
    # Fernet symmetric key for provider-credential encryption at rest (DEC-GRX-009), e.g.
    # email_provider_connections.smtp_password_encrypted. Distinct from jwt_signing_key —
    # this one is reversible by design (the worker must decrypt to actually send), so it
    # must never be reused for anything that should stay one-way. Generate a real key via
    # `Fernet.generate_key()` in production; this default is local-dev-only.
    encryption_key: str = "U640ORbquCvIAZca0r5qqd173t669iSoJ3gSuoGGSr0="
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    invitation_ttl_days: int = 7
    password_reset_ttl_minutes: int = 30
    # GRX-SAAS-003 Phase C: how long a self-registration's verification link stays
    # valid. Longer than password_reset_ttl_minutes (a returning user checks their
    # inbox faster than a brand-new signup might), shorter than invitation_ttl_days
    # (no existing relationship vouching for the recipient).
    email_verification_ttl_hours: int = 24

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

    # GRX-SCHED-002: how often the in-process scheduler ticker polls for due campaigns.
    # 5s keeps scheduled sends responsive in dev/demo without meaningfully loading the
    # DB (one indexed UPDATE...RETURNING per tick); raise in production if poll load
    # ever matters more than dispatch latency.
    scheduler_poll_interval_seconds: float = 5.0

    # Platform-level transactional email: sends the self-registration verification link.
    # Deliberately separate from the customer-owned email_provider_connections table
    # (Postmark/Custom SMTP per account, GRX-EMAIL-011) -- a brand-new account has no
    # provider of its own yet, so the platform sends this one email on the account's
    # behalf, the way any SaaS sends its own signup confirmations. An empty host means
    # "not configured yet" -- registration still succeeds, the email is just skipped
    # (and logged), so this ships safely before real SMTP credentials are set.
    platform_smtp_host: str = ""
    platform_smtp_port: int = 587
    platform_smtp_username: str = ""
    platform_smtp_password: str = ""
    platform_smtp_from_email: str = "noreply@growixa.local"
    platform_smtp_from_name: str = "Growixa"

    # Base URL of the deployed frontend, used to build the verification link emailed to
    # a new signup (e.g. https://growixa.netlify.app). Defaults to local dev.
    frontend_base_url: str = "http://localhost:3000"

    # GRX-SAAS-010: how long a support session stays usable after it's opened, before
    # every read/write action through it starts rejecting (re-checked at call time, not
    # only at creation — see THREAT_MODEL.md T39).
    support_session_ttl_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
