import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission
from growixa_api.redis import get_redis
from growixa_api.social.instagram_client import InstagramApiError
from growixa_api.social.services import (
    OAuthStateInvalidError,
    build_authorize_url,
    complete_oauth_callback,
)

oauth_router = APIRouter(prefix="/integrations/instagram/oauth", tags=["social"])

_require_manage = require_permission("integrations.manage")


@oauth_router.get("/authorize")
async def authorize_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
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
    actor_id: uuid.UUID = Depends(_require_manage),
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

    return RedirectResponse(f"{integrations_url}?instagram=connected", status_code=302)
