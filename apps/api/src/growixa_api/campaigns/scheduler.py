import asyncio
import logging
from collections.abc import Sequence

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from growixa_api.campaigns.models import Campaign
from growixa_api.db import async_session_factory
from growixa_api.jobs.producer import publish_job
from growixa_api.jobs.schemas import JobEnvelope

logger = logging.getLogger("growixa_api")

# GRX-SCHED-002/003: the worker's own queue, consumed by growixa_worker.consumer's
# dispatch handler. Distinct from email_delivery's SEND_CAMPAIGN_QUEUE (the immediate
# "Send now" path, GRX-EMAIL-004) so scheduled dispatch can carry its own retry/DLQ
# policy without changing the immediate-send path's behavior.
DISPATCH_QUEUE = "grx.campaigns.dispatch"


async def claim_due_campaigns(session: AsyncSession) -> Sequence[Campaign]:
    """Atomically claims every SCHEDULED campaign whose scheduled_at has passed,
    flipping it to DISPATCHING in the same statement. A single UPDATE...RETURNING is
    safe under concurrent tickers (e.g. a rolling deploy briefly running two API
    instances) — Postgres row locks make each row claimable by exactly one caller,
    unlike a SELECT-then-UPDATE which could double-claim between the two statements."""
    result = await session.execute(
        update(Campaign)
        .where(Campaign.status == "SCHEDULED", Campaign.scheduled_at <= func.now())
        .values(status="DISPATCHING")
        .returning(Campaign)
    )
    return result.scalars().all()


async def run_scheduler_tick(session: AsyncSession) -> int:
    """One poll: claim due campaigns, commit the status change, then enqueue one
    dispatch job per campaign. Enqueuing happens after commit so a publish failure
    never leaves a campaign claimed (DISPATCHING) with no job ever published for it."""
    campaigns = await claim_due_campaigns(session)
    await session.commit()

    for campaign in campaigns:
        envelope = JobEnvelope(
            idempotency_key=str(campaign.idempotency_key),
            job_type=DISPATCH_QUEUE,
            payload={"campaign_id": str(campaign.id)},
        )
        await publish_job(DISPATCH_QUEUE, envelope)

    return len(campaigns)


async def run_scheduler_loop(interval_seconds: float) -> None:
    """Runs forever inside the API process (started from app.py's lifespan) — per
    BACKGROUND_JOB_ARCHITECTURE.md, "a backend API request or scheduler enqueues a
    job," never performs the side-effecting send inline. One bad tick (a transient DB
    or RabbitMQ blip) is logged and skipped rather than crashing the whole API process."""
    logger.info("campaign scheduler ticker starting (interval=%ss)", interval_seconds)
    while True:
        try:
            async with async_session_factory() as session:
                claimed = await run_scheduler_tick(session)
                if claimed:
                    logger.info("campaign scheduler: dispatched %s campaign(s)", claimed)
        except Exception:
            logger.exception("campaign scheduler tick failed")
        await asyncio.sleep(interval_seconds)
