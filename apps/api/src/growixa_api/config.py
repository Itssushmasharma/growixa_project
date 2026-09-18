import os
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# When running pytest, ENVIRONMENT is set to "test" via .env.test so
# we never accidentally connect to the live dev database.
_env_file = ".env.test" if os.getenv("ENVIRONMENT") == "test" else ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file, extra="ignore")

    # Several hosting platforms' secrets UIs (confirmed on Hugging Face Space
    # variables/secrets) silently append a trailing newline to a pasted value --
    # db.py's _normalize_database_url already had to work around this for
    # DATABASE_URL specifically; this strips every string setting the same way at
    # parse time so the bug can't resurface field by field. A real production
    # incident: PLATFORM_SMTP_HOST had a trailing "\n", which aiosmtplib correctly
    # rejects ("hostname param contains prohibited newline characters") -- but that
    # ValueError wasn't caught by smtp_transport.py's own error handling, so it
    # crashed registration with a 500 instead of just skipping the email.
    @field_validator("*", mode="before")
    @classmethod
    def _strip_whitespace(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    environment: str = "local"
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://growixa:local_dev_pg_pw@localhost:5433/growixa_test"
    redis_url: str = "redis://localhost:6379/1"
    rabbitmq_url: str = "amqp://guest:local_dev_mq_pw@localhost:5672/"

    # Origins the Next.js frontend runs on — needed so browser-based fetches from
    # apps/web can complete credentialed (cookie-based) requests.
    # Accepts comma-separated list or JSON array in env vars.
    cors_allowed_origins: list[str] | str = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3100",
    ]

    @field_validator("cors_allowed_origins", mode="after")
    @classmethod
    def _normalize_cors_allowed_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            val = value.strip()
            if val.startswith("[") and val.endswith("]"):
                import json

                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        return value

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

    # Slice 5 (Social Publishing, DEC-GRX-023): the API's own publicly-reachable base
    # URL, used to build the Instagram OAuth redirect_uri — must exactly match what's
    # registered in the Meta Developer App.
    api_public_url: str = "http://localhost:8000"
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    instagram_graph_api_version: str = "v21.0"
    # How long a generated OAuth `state` value stays valid in Redis before the connect
    # flow must be restarted — see THREAT_MODEL.md T44.
    instagram_oauth_state_ttl_seconds: int = 600

    # GRX-AUTH-006: Google OAuth 2.0 / SSO credentials & state TTL
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_state_ttl_seconds: int = 600

    # IITD IAM / Keycloak Universal SSO (OIDC)
    iam_oidc_issuer: str = "https://auth.iitdeveloper.com/realms/iitd"
    iam_client_id: str = "growixa-app"
    iam_client_secret: str = ""
    iam_oauth_state_ttl_seconds: int = 600

    # Phase 4 Social Channels OAuth credentials
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    twitter_client_id: str = ""
    twitter_client_secret: str = ""

    # Slice 5 media storage (DEC-GRX-024): Supabase Storage, called directly via its
    # REST API (growixa_api.files.storage_client) — no SDK, matching this codebase's
    # existing thin-provider-wrapper convention. The bucket is public-read by
    # requirement (Instagram fetches media by plain URL) — see THREAT_MODEL.md T48.
    supabase_storage_url: str = ""
    supabase_storage_service_key: str = ""
    supabase_storage_bucket: str = "social-media"

    # GRX-SOCIAL-007: how often the social post scheduler ticker polls for due posts —
    # same default and rationale as scheduler_poll_interval_seconds, its campaigns
    # equivalent, running as a second independent ticker.
    social_scheduler_poll_interval_seconds: float = 5.0

    # Slice 7 (Billing, DEC-GRX-029): Razorpay Test/Live Mode API credentials. Empty
    # defaults mean "not configured yet" -- the plan-sync CLI and, later, the webhook
    # receiver and checkout routes fail cleanly (not with a confusing auth error) until
    # real Test Mode credentials are set. Never used directly by
    # billing/providers/razorpay_provider.py's callers -- always passed through
    # RazorpayProvider(key_id=..., key_secret=...), matching the AI providers'
    # constructor-injection convention rather than a global client singleton.
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    # Set once the webhook is registered in the Razorpay dashboard (GRX-BILL-003) --
    # verifies POST /billing/razorpay's payload actually came from Razorpay
    # (THREAT_MODEL.md T60), distinct from key_id/key_secret which authenticate
    # outbound API calls, not inbound webhook deliveries.
    razorpay_webhook_secret: str = ""

    # GRX-BILL-006: how often the cancellation-downgrade ticker polls for CANCELED
    # subscriptions past their current_period_end. Unlike scheduler_poll_interval_seconds
    # (campaigns/social posts, where a few seconds of lateness is user-visible), a
    # downgrade only ever needs to land sometime within the day its period actually
    # ends -- an hourly poll is more than precise enough and avoids an otherwise-always-
    # empty query running every 5s forever.
    billing_downgrade_poll_interval_seconds: float = 3600.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
