import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from growixa_api import __version__
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
from growixa_api.roles.api import router as roles_router
from growixa_api.templates.api import router as templates_router
from growixa_api.users.api import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # GRX-SCHED-002: only runs under a real ASGI server (uvicorn) — httpx's
    # ASGITransport used throughout this repo's tests never invokes the lifespan
    # protocol, so no test accidentally spins up a background ticker.
    task = asyncio.create_task(run_scheduler_loop(get_settings().scheduler_poll_interval_seconds))
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def create_app() -> FastAPI:
    # No prior module configured a handler for the "growixa_api" logger namespace (unlike
    # apps/worker's main.py) — without this, the scheduler ticker's logger.info/.exception
    # calls in campaigns/scheduler.py silently go nowhere, since uvicorn only configures its
    # own "uvicorn"/"uvicorn.access"/"uvicorn.error" loggers, not application-level ones.
    logging.basicConfig(level=get_settings().log_level.upper())

    app = FastAPI(title="Growixa API", version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(company_router)
    app.include_router(brand_router)
    app.include_router(users_router)
    app.include_router(roles_router)
    app.include_router(jobs_router)
    app.include_router(contacts_router)
    app.include_router(audit_router)
    app.include_router(integrations_router)
    app.include_router(templates_router)
    app.include_router(campaigns_router)
    app.include_router(email_delivery_router)
    app.include_router(email_delivery_public_router)
    app.include_router(analytics_router)
    return app
