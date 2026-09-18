import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.services import PlanLimitExceededError
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.files.storage_client import StorageError
from growixa_api.permissions.dependencies import get_current_account_id, require_permission
from growixa_api.redis import get_redis
from growixa_api.social.bulk_scheduler import BulkScheduleItem, bulk_schedule_posts_service
from growixa_api.social.instagram_client import InstagramApiError
from growixa_api.social.models import SocialPost, SocialPostMedia
from growixa_api.social.providers.factory import list_available_channels
from growixa_api.social.schemas import (
    BulkScheduleIn,
    BulkScheduleOut,
    ChannelCapabilityOut,
    ScheduleSocialPostIn,
    SocialConnectionOut,
    SocialPostIn,
    SocialPostJobOut,
    SocialPostMediaOut,
    SocialPostOut,
    SocialPostUpdateIn,
)
from growixa_api.social.services import (
    InvalidMediaTypeError,
    MediaTooLargeError,
    OAuthStateInvalidError,
    PostAlreadyScheduledError,
    PostHasNoMediaError,
    PostNotCancellableError,
    PostNotPublishableError,
    PostNotRetryableError,
    SocialConnectionNotFoundError,
    SocialPostMediaNotFoundError,
    SocialPostNotEditableError,
    SocialPostNotFoundError,
    TooManyMediaItemsError,
    add_media,
    build_authorize_url,
    build_provider_authorize_url,
    cancel_post,
    complete_oauth_callback,
    complete_provider_oauth_callback,
    create_post,
    disconnect_connection,
    get_post_or_raise,
    list_all_connections,
    list_all_posts,
    list_media_for_post,
    publish_now,
    remove_media,
    retry_post,
    schedule_post,
    update_post,
)

oauth_router = APIRouter(prefix="/integrations/instagram/oauth", tags=["social"])
channel_oauth_router = APIRouter(prefix="/integrations", tags=["social"])
router = APIRouter(prefix="/social", tags=["social"])

_require_integrations_manage = require_permission("integrations.manage")
_require_social_manage = require_permission("social.manage")
_require_social_publish = require_permission("social.publish")
_require_social_view = require_permission("social.view")


def _post_to_out(post: SocialPost, media: list[SocialPostMedia]) -> SocialPostOut:
    out = SocialPostOut.model_validate(post)
    return out.model_copy(
        update={"media": [SocialPostMediaOut.model_validate(item) for item in media]}
    )


@oauth_router.get("/authorize")
async def authorize_route(
    _actor_id: uuid.UUID = Depends(_require_integrations_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    redis_client: Redis = Depends(get_redis),
) -> RedirectResponse:
    """Redirects the browser to Meta's own OAuth consent dialog. A plain top-level
    navigation (the frontend links here with a bare `<a href>`, never `apiFetch`) —
    the user must interact with Meta's own login/consent screen, which a fetch/XHR
    call cannot do."""
    url = await build_authorize_url(redis_client, account_id)
    return RedirectResponse(url, status_code=302)


@oauth_router.get("/callback")
async def callback_route(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    actor_id: uuid.UUID = Depends(_require_integrations_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    redis_client: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Meta redirects the browser here directly, so this route redirects back to the
    frontend on every outcome — success or failure — rather than ever returning a raw
    JSON error a browser navigation can't do anything useful with."""
    frontend_url = get_settings().frontend_base_url
    integrations_url = f"{frontend_url}/dashboard/integrations"

    if error is not None or code is None or state is None:
        return RedirectResponse(
            f"{integrations_url}?instagram=error&reason=denied", status_code=302
        )

    try:
        await complete_oauth_callback(
            session, redis_client, account_id=account_id, actor_id=actor_id, code=code, state=state
        )
    except OAuthStateInvalidError:
        return RedirectResponse(
            f"{integrations_url}?instagram=error&reason=invalid_state", status_code=302
        )
    except InstagramApiError:
        return RedirectResponse(
            f"{integrations_url}?instagram=error&reason=graph_api_error", status_code=302
        )
    except PlanLimitExceededError:
        return RedirectResponse(
            f"{integrations_url}?instagram=error&reason=plan_limit_reached", status_code=302
        )

    return RedirectResponse(f"{integrations_url}?instagram=connected", status_code=302)


@channel_oauth_router.get("/{provider}/oauth/authorize")
async def provider_authorize_route(
    provider: str,
    _actor_id: uuid.UUID = Depends(_require_integrations_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    redis_client: Redis = Depends(get_redis),
) -> RedirectResponse:
    url = await build_provider_authorize_url(provider, redis_client, account_id)
    return RedirectResponse(url, status_code=302)


@channel_oauth_router.get("/{provider}/oauth/callback")
async def provider_callback_route(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    actor_id: uuid.UUID = Depends(_require_integrations_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    redis_client: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    frontend_url = get_settings().frontend_base_url
    social_url = f"{frontend_url}/dashboard/social"

    if error is not None or code is None or state is None:
        return RedirectResponse(
            f"{social_url}?channel={provider.lower()}&error=denied", status_code=302
        )

    try:
        await complete_provider_oauth_callback(
            provider,
            session,
            redis_client,
            account_id=account_id,
            actor_id=actor_id,
            code=code,
            state=state,
        )
    except OAuthStateInvalidError:
        return RedirectResponse(
            f"{social_url}?channel={provider.lower()}&error=invalid_state", status_code=302
        )
    except PlanLimitExceededError:
        return RedirectResponse(
            f"{social_url}?channel={provider.lower()}&error=plan_limit_reached", status_code=302
        )
    except Exception:
        return RedirectResponse(
            f"{social_url}?channel={provider.lower()}&error=auth_failed", status_code=302
        )

    return RedirectResponse(
        f"{social_url}?channel={provider.lower()}&connected=true", status_code=302
    )


@router.get("/channels", response_model=list[ChannelCapabilityOut])
async def list_channels_route(
    _actor_id: uuid.UUID = Depends(_require_social_view),
) -> list[ChannelCapabilityOut]:
    caps = list_available_channels()
    return [ChannelCapabilityOut.model_validate(c) for c in caps]


@router.get("/connections", response_model=list[SocialConnectionOut])
async def list_connections_route(
    _actor_id: uuid.UUID = Depends(_require_social_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[SocialConnectionOut]:
    connections = await list_all_connections(session, account_id)
    return [SocialConnectionOut.model_validate(connection) for connection in connections]


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_connection_route(
    connection_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await disconnect_connection(session, account_id, connection_id)
    except SocialConnectionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Social connection not found") from exc


@router.post("/bulk-schedule", response_model=BulkScheduleOut)
async def bulk_schedule_route(
    payload: BulkScheduleIn,
    actor_id: uuid.UUID = Depends(_require_social_publish),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> BulkScheduleOut:
    items = [
        BulkScheduleItem(
            social_connection_id=item.social_connection_id,
            caption=item.caption,
            scheduled_at=item.scheduled_at,
            media_items=item.media_items,
            campaign_id=item.campaign_id,
            utm_source=item.utm_source,
            utm_medium=item.utm_medium,
            utm_campaign=item.utm_campaign,
            utm_content=item.utm_content,
        )
        for item in payload.items
    ]
    result = await bulk_schedule_posts_service(
        session,
        account_id=account_id,
        actor_id=actor_id,
        items=items,
        stagger_interval_minutes=payload.stagger_interval_minutes,
    )
    return BulkScheduleOut(
        total_requested=result.total_requested,
        scheduled_count=result.scheduled_count,
        failed_count=result.failed_count,
        scheduled_posts=result.scheduled_posts,
        errors=result.errors,
    )


@router.get("/posts", response_model=list[SocialPostOut])
async def list_posts_route(
    _actor_id: uuid.UUID = Depends(_require_social_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[SocialPostOut]:
    posts = await list_all_posts(session, account_id)
    out = []
    for post in posts:
        media = await list_media_for_post(session, account_id, post.id)
        out.append(_post_to_out(post, list(media)))
    return out


@router.post("/posts", response_model=SocialPostOut, status_code=status.HTTP_201_CREATED)
async def create_post_route(
    payload: SocialPostIn,
    actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostOut:
    try:
        post = await create_post(session, account_id, payload, actor_id)
    except SocialConnectionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Social connection not found") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _post_to_out(post, [])


@router.get("/posts/{post_id}", response_model=SocialPostOut)
async def get_post_route(
    post_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_social_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostOut:
    try:
        post = await get_post_or_raise(session, account_id, post_id)
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    media = await list_media_for_post(session, account_id, post_id)
    return _post_to_out(post, list(media))


@router.patch("/posts/{post_id}", response_model=SocialPostOut)
async def update_post_route(
    post_id: uuid.UUID,
    payload: SocialPostUpdateIn,
    _actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostOut:
    try:
        post = await update_post(session, account_id, post_id, payload)
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    except SocialPostNotEditableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post is no longer a draft") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    media = await list_media_for_post(session, account_id, post_id)
    return _post_to_out(post, list(media))


@router.post(
    "/posts/{post_id}/media", response_model=SocialPostMediaOut, status_code=status.HTTP_201_CREATED
)
async def add_media_route(
    post_id: uuid.UUID,
    file: UploadFile = File(...),
    _actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostMediaOut:
    content = await file.read()
    try:
        media = await add_media(
            session,
            account_id,
            post_id,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    except SocialPostNotEditableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post is no longer a draft") from exc
    except InvalidMediaTypeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except MediaTooLargeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except TooManyMediaItemsError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except StorageError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Media upload failed: {exc}") from exc
    return SocialPostMediaOut.model_validate(media)


@router.delete("/posts/{post_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_media_route(
    post_id: uuid.UUID,
    media_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await remove_media(session, account_id, post_id, media_id)
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    except SocialPostNotEditableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post is no longer a draft") from exc
    except SocialPostMediaNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found") from exc
    except StorageError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Media removal failed: {exc}") from exc


@router.post(
    "/posts/{post_id}/publish",
    response_model=SocialPostJobOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def publish_post_route(
    post_id: uuid.UUID,
    actor_id: uuid.UUID = Depends(_require_social_publish),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostJobOut:
    try:
        envelope = await publish_now(session, account_id, post_id, actor_id)
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    except PostNotPublishableError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Post is not in a publishable (DRAFT) state"
        ) from exc
    except PostHasNoMediaError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post has no media to publish") from exc
    return SocialPostJobOut(job_id=str(envelope.job_id))


@router.post("/posts/{post_id}/schedule", response_model=SocialPostOut)
async def schedule_post_route(
    post_id: uuid.UUID,
    payload: ScheduleSocialPostIn,
    _actor_id: uuid.UUID = Depends(_require_social_publish),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostOut:
    try:
        post = await schedule_post(session, account_id, post_id, payload)
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    except PostAlreadyScheduledError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except PostHasNoMediaError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post has no media to publish") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    media = await list_media_for_post(session, account_id, post_id)
    return _post_to_out(post, list(media))


@router.post("/posts/{post_id}/cancel", response_model=SocialPostOut)
async def cancel_post_route(
    post_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_social_publish),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostOut:
    try:
        post = await cancel_post(session, account_id, post_id)
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    except PostNotCancellableError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    media = await list_media_for_post(session, account_id, post_id)
    return _post_to_out(post, list(media))


@router.post(
    "/posts/{post_id}/retry", response_model=SocialPostJobOut, status_code=status.HTTP_202_ACCEPTED
)
async def retry_post_route(
    post_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_social_publish),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SocialPostJobOut:
    try:
        envelope = await retry_post(session, account_id, post_id)
    except SocialPostNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found") from exc
    except PostNotRetryableError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return SocialPostJobOut(job_id=str(envelope.job_id))
