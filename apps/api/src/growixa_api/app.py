import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from growixa_api import __version__
from growixa_api.accounts import models as accounts_models  # noqa: F401
from growixa_api.accounts.api import router as accounts_router
from growixa_api.ai.api import router as ai_router
from growixa_api.analytics.api import router as analytics_router
from growixa_api.audit.api import router as audit_router
from growixa_api.auth.api import router as auth_router
from growixa_api.brand.api import router as brand_router
from growixa_api.campaigns.api import router as campaigns_router
from growixa_api.campaigns.scheduler import run_scheduler_loop
from growixa_api.company.api import router as company_router
from growixa_api.config import get_settings
from growixa_api.contacts.api import router as contacts_router
from growixa_api.email_delivery.api import public_router as email_delivery_public_router
from growixa_api.email_delivery.api import router as email_delivery_router
from growixa_api.health import router as health_router
from growixa_api.integrations.api import router as integrations_router
from growixa_api.jobs.api import router as jobs_router
from growixa_api.platform_admin.api import ai_config_router as platform_admin_ai_config_router
from growixa_api.platform_admin.api import router as platform_admin_router
from growixa_api.platform_admin.api import (
    support_session_router as platform_admin_support_session_router,
)
from growixa_api.platform_admin.api import usage_router as platform_admin_usage_router
from growixa_api.platform_auth.api import router as platform_auth_router
from growixa_api.roles.api import router as roles_router
from growixa_api.social.api import oauth_router as social_oauth_router
from growixa_api.social.api import router as social_router
from growixa_api.social.scheduler import run_scheduler_loop as run_social_scheduler_loop
from growixa_api.templates.api import router as templates_router
from growixa_api.users.api import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # GRX-SCHED-002: only runs under a real ASGI server (uvicorn) — httpx's
    # ASGITransport used throughout this repo's tests never invokes the lifespan
    # protocol, so no test accidentally spins up a background ticker.
    task = asyncio.create_task(run_scheduler_loop(get_settings().scheduler_poll_interval_seconds))
    social_task = asyncio.create_task(
        run_social_scheduler_loop(get_settings().social_scheduler_poll_interval_seconds)
    )
    try:
        yield
    finally:
        task.cancel()
        social_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        with contextlib.suppress(asyncio.CancelledError):
            await social_task


def create_app() -> FastAPI:
    # No prior module configured a handler for the "growixa_api" logger namespace (unlike
    # apps/worker's main.py) — without this, the scheduler ticker's logger.info/.exception
    # calls in campaigns/scheduler.py silently go nowhere, since uvicorn only configures its
    # own "uvicorn"/"uvicorn.access"/"uvicorn.error" loggers, not application-level ones.
    logging.basicConfig(level=get_settings().log_level.upper())

    app = FastAPI(title="Growixa API", version=__version__, lifespan=lifespan)
    origins = get_settings().cors_allowed_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=(
            r"https://.*\.netlify\.app|https://.*\.vercel\.app|"
            r"https://.*\.onrender\.com|http://localhost:.*"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(platform_auth_router)
    app.include_router(platform_admin_router)
    app.include_router(platform_admin_usage_router)
    app.include_router(platform_admin_support_session_router)
    app.include_router(platform_admin_ai_config_router)
    app.include_router(accounts_router)
    app.include_router(company_router)
    app.include_router(brand_router)
    app.include_router(users_router)
    app.include_router(roles_router)
    app.include_router(jobs_router)
    app.include_router(contacts_router)
    app.include_router(audit_router)
    app.include_router(integrations_router)
    app.include_router(social_oauth_router)
    app.include_router(social_router)
    app.include_router(templates_router)
    app.include_router(campaigns_router)
    app.include_router(email_delivery_router)
    app.include_router(email_delivery_public_router)
    app.include_router(analytics_router)
    app.include_router(ai_router)
    return app
