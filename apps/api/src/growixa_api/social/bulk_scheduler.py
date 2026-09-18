from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.social import repositories
from growixa_api.social.models import SocialPost
from growixa_api.social.providers.factory import get_social_provider


@dataclass
class BulkScheduleItem:
    social_connection_id: uuid.UUID
    caption: str
    scheduled_at: datetime
    media_items: list[dict[str, object]] = field(default_factory=list)
    campaign_id: uuid.UUID | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None


@dataclass
class BulkScheduleResult:
    total_requested: int
    scheduled_count: int
    failed_count: int
    scheduled_posts: list[uuid.UUID] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


async def bulk_schedule_posts_service(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    items: list[BulkScheduleItem],
    stagger_interval_minutes: int = 15,
) -> BulkScheduleResult:
    """Schedules a batch of social posts across multiple channels.
    Enforces minimum spacing per connection to avoid provider rate limit bursts."""
    scheduled_posts: list[uuid.UUID] = []
    errors: list[dict[str, str]] = []

    # Track last scheduled time per connection to enforce rate-limit staggering
    connection_last_time: dict[uuid.UUID, datetime] = {}

    for idx, item in enumerate(items):
        # 1. Fetch and validate social connection
        connection = await repositories.get_connection(
            session, account_id, item.social_connection_id
        )
        if connection is None or not connection.is_active:
            errors.append(
                {
                    "item_index": str(idx),
                    "error": f"Social connection {item.social_connection_id} not found or inactive",
                }
            )
            continue

        # 2. Validate content against official provider capabilities
        provider = get_social_provider(connection.provider)
        validation_errors = provider.validate_post(item.caption, item.media_items)
        if validation_errors:
            errors.append(
                {
                    "item_index": str(idx),
                    "error": "; ".join(validation_errors),
                }
            )
            continue

        # 3. Calculate staggered scheduled_at time
        req_time = (
            item.scheduled_at.astimezone(UTC)
            if item.scheduled_at.tzinfo
            else item.scheduled_at.replace(tzinfo=UTC)
        )
        now_utc = datetime.now(UTC)
        if req_time <= now_utc:
            req_time = now_utc + timedelta(minutes=5)

        last_time = connection_last_time.get(connection.id)
        if last_time is not None:
            min_next = last_time + timedelta(minutes=stagger_interval_minutes)
            if req_time < min_next:
                req_time = min_next

        connection_last_time[connection.id] = req_time

        # 4. Create scheduled post
        post = SocialPost(
            account_id=account_id,
            social_connection_id=connection.id,
            caption=item.caption,
            status="SCHEDULED",
            scheduled_at=req_time,
            campaign_id=item.campaign_id,
            utm_source=item.utm_source,
            utm_medium=item.utm_medium,
            utm_campaign=item.utm_campaign,
            utm_content=item.utm_content,
            created_by_user_id=actor_id,
            idempotency_key=uuid.uuid4(),
        )
        session.add(post)
        await session.flush()
        scheduled_posts.append(post.id)

    await session.commit()

    return BulkScheduleResult(
        total_requested=len(items),
        scheduled_count=len(scheduled_posts),
        failed_count=len(errors),
        scheduled_posts=scheduled_posts,
        errors=errors,
    )
