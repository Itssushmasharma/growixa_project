import asyncio
import logging
from collections.abc import Sequence

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from growixa_api.db import async_session_factory
from growixa_api.jobs.producer import publish_job
from growixa_api.jobs.schemas import JobEnvelope
from growixa_api.social.models import SocialPost

logger = logging.getLogger("growixa_api")

# Mirrors growixa_api.campaigns.scheduler.DISPATCH_QUEUE — its own queue, distinct from
# PUBLISH_NOW_QUEUE (GRX-SOCIAL-006's immediate "Publish now" path), so scheduled
# dispatch can carry its own retry/DLQ policy without changing that path's behavior.
DISPATCH_QUEUE = "grx.social.dispatch"


async def claim_due_posts(session: AsyncSession) -> Sequence[SocialPost]:
    """Atomically claims every SCHEDULED post whose scheduled_at has passed, flipping
    it to DISPATCHING in the same statement — identical rationale to
    campaigns.scheduler.claim_due_campaigns (safe under concurrent tickers)."""
    result = await session.execute(
        update(SocialPost)
        .where(SocialPost.status == "SCHEDULED", SocialPost.scheduled_at <= func.now())
        .values(status="DISPATCHING")
        .returning(SocialPost)
    )
    return result.scalars().all()


async def run_scheduler_tick(session: AsyncSession) -> int:
    """One poll: claim due posts, commit the status change, then enqueue one dispatch
    job per post. Enqueuing happens after commit so a publish failure never leaves a
    post claimed (DISPATCHING) with no job ever published for it."""
    posts = await claim_due_posts(session)
    await session.commit()

    for post in posts:
        envelope = JobEnvelope(
            idempotency_key=str(post.idempotency_key),
            job_type=DISPATCH_QUEUE,
            payload={"social_post_id": str(post.id)},
        )
        await publish_job(DISPATCH_QUEUE, envelope)

    return len(posts)


async def run_scheduler_loop(interval_seconds: float) -> None:
    """Runs forever inside the API process (started from app.py's lifespan), alongside
    campaigns' own scheduler loop. One bad tick (a transient DB or RabbitMQ blip) is
    logged and skipped rather than crashing the whole API process."""
    logger.info("social post scheduler ticker starting (interval=%ss)", interval_seconds)
    while True:
        try:
            async with async_session_factory() as session:
                claimed = await run_scheduler_tick(session)
                if claimed:
                    logger.info("social post scheduler: dispatched %s post(s)", claimed)
        except Exception:
            logger.exception("social post scheduler tick failed")
        await asyncio.sleep(interval_seconds)
