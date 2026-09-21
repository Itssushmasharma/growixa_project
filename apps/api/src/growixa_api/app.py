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
from growixa_api.agency.api import router as agency_router
from growixa_api.ai.api import router as ai_router
from growixa_api.ai.chat import router as chat_router
from growixa_api.analytics.api import router as analytics_router
from growixa_api.analytics_engine.router import router as analytics_engine_router
from growixa_api.approvals.api import router as approvals_router
from growixa_api.audit.api import router as audit_router
from growixa_api.auth.api import router as auth_router
from growixa_api.automations.api import router as automations_router
from growixa_api.billing.api import public_router as billing_public_router
from growixa_api.billing.api import router as billing_router
from growixa_api.billing.scheduler import run_downgrade_loop as run_billing_downgrade_loop
from growixa_api.brand.api import router as brand_router
from growixa_api.calendar.router import router as calendar_router
from growixa_api.campaigns.api import router as campaigns_router
from growixa_api.campaigns.scheduler import run_scheduler_loop
from growixa_api.company.api import router as company_router
from growixa_api.config import get_settings
from growixa_api.contacts.api import router as contacts_router
from growixa_api.dashboard.api import router as dashboard_router
from growixa_api.email_delivery.api import public_router as email_delivery_public_router
from growixa_api.email_delivery.api import router as email_delivery_router
from growixa_api.email_validation.api import router as email_validation_router
from growixa_api.health import router as health_router
from growixa_api.inbox import router as inbox
from growixa_api.integrations.api import router as integrations_router
from growixa_api.jobs.api import router as jobs_router
from growixa_api.media.api import router as media_router
from growixa_api.platform_admin.api import ai_config_router as platform_admin_ai_config_router
from growixa_api.platform_admin.api import billing_router as platform_admin_billing_router
from growixa_api.platform_admin.api import (
    email_config_router as platform_admin_email_config_router,
)
from growixa_api.platform_admin.api import (
    email_validation_config_router as platform_admin_email_validation_config_router,
)
from growixa_api.platform_admin.api import (
    monitoring_router as platform_admin_monitoring_router,
)
from growixa_api.platform_admin.api import router as platform_admin_router
from growixa_api.platform_admin.api import (
    support_session_router as platform_admin_support_session_router,
)
from growixa_api.platform_admin.api import (
    templates_router as platform_admin_templates_router,
)
from growixa_api.platform_admin.api import usage_router as platform_admin_usage_router
from growixa_api.platform_auth.api import router as platform_auth_router
from growixa_api.reports.api import router as reports_router
from growixa_api.roles.api import router as roles_router
from growixa_api.seo import api as seo
from growixa_api.smm import api as smm
from growixa_api.sms.router import router as sms_router
from growixa_api.sms.router import webhook_router as sms_webhook_router
from growixa_api.social.api import channel_oauth_router
from growixa_api.social.api import oauth_router as social_oauth_router
from growixa_api.social.api import router as social_router
from growixa_api.social.scheduler import run_scheduler_loop as run_social_scheduler_loop
from growixa_api.templates.api import router as templates_router
from growixa_api.users.api import router as users_router
from growixa_api.whatsapp.router import router as whatsapp_router
from growixa_api.whatsapp.router import webhook_router as whatsapp_webhook_router
from growixa_api.creative.api import router as creative_router
from growixa_api.ads.api import router as ads_router
from growixa_api.lead_gen.api import router as lead_gen_router
from growixa_api.communications.api import router as communications_router
from growixa_api.planner.api import router as planner_router
from growixa_api.business_presence.api import router as business_presence_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # GRX-SCHED-002: only runs under a real ASGI server (uvicorn) — httpx's
    # ASGITransport used throughout this repo's tests never invokes the lifespan
    # protocol, so no test accidentally spins up a background ticker.
    task = asyncio.create_task(run_scheduler_loop(get_settings().scheduler_poll_interval_seconds))
    social_task = asyncio.create_task(
        run_social_scheduler_loop(get_settings().social_scheduler_poll_interval_seconds)
    )
    billing_downgrade_task = asyncio.create_task(
        run_billing_downgrade_loop(get_settings().billing_downgrade_poll_interval_seconds)
    )
    try:
        yield
    finally:
        task.cancel()
        social_task.cancel()
        billing_downgrade_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        with contextlib.suppress(asyncio.CancelledError):
            await social_task
        with contextlib.suppress(asyncio.CancelledError):
            await billing_downgrade_task


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
    app.include_router(platform_admin_billing_router)
    app.include_router(platform_admin_email_config_router)
    app.include_router(platform_admin_email_validation_config_router)
    app.include_router(platform_admin_monitoring_router)
    app.include_router(platform_admin_templates_router)
    app.include_router(accounts_router)
    app.include_router(agency_router)
    app.include_router(company_router)
    app.include_router(brand_router)
    app.include_router(calendar_router)
    app.include_router(automations_router)
    app.include_router(whatsapp_router)
    app.include_router(whatsapp_webhook_router)
    app.include_router(sms_router)
    app.include_router(sms_webhook_router)
    app.include_router(analytics_engine_router)
    app.include_router(reports_router)
    app.include_router(approvals_router)
    app.include_router(users_router)
    app.include_router(roles_router)
    app.include_router(jobs_router)
    app.include_router(contacts_router)
    app.include_router(email_validation_router)
    app.include_router(dashboard_router)
    app.include_router(audit_router)
    app.include_router(integrations_router)
    app.include_router(social_oauth_router)
    app.include_router(channel_oauth_router)
    app.include_router(social_router)
    app.include_router(media_router)
    app.include_router(templates_router)
    app.include_router(campaigns_router)
    app.include_router(email_delivery_router)
    app.include_router(email_delivery_public_router)
    app.include_router(analytics_router)
    app.include_router(ai_router)
    app.include_router(chat_router)
    app.include_router(billing_router)
    app.include_router(billing_public_router)
    app.include_router(seo.router)
    app.include_router(smm.router)
    app.include_router(inbox.router)
    app.include_router(creative_router)
    app.include_router(ads_router)
    app.include_router(lead_gen_router)
    app.include_router(communications_router)
    app.include_router(planner_router)
    app.include_router(business_presence_router)
    return app
