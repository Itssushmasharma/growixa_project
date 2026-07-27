import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import require_permission
from growixa_api.users.schemas import (
    AcceptInvitationIn,
    AcceptInvitationOut,
    InviteUserIn,
    InviteUserOut,
)
from growixa_api.users.services import (
    EmailAlreadyRegisteredError,
    InvalidInvitationError,
    RoleNotFoundError,
)
from growixa_api.users.services import accept_invitation as accept_invitation_service
from growixa_api.users.services import invite_user as invite_user_service

router = APIRouter(prefix="/users", tags=["users"])

_require_manage = require_permission("users.manage")


@router.post("/invitations", response_model=InviteUserOut, status_code=status.HTTP_201_CREATED)
async def create_invitation_route(
    payload: InviteUserIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> InviteUserOut:
    try:
        invitation, raw_token = await invite_user_service(
            session,
            email=payload.email,
            role_name=payload.role_name,
            invited_by_user_id=actor_id,
        )
    except RoleNotFoundError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role") from exc
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A user with this email already exists"
        ) from exc

    return InviteUserOut(
        id=invitation.id,
        email=invitation.email,
        expires_at=invitation.expires_at,
        token=raw_token,
    )


@router.post("/invitations/accept", response_model=AcceptInvitationOut)
async def accept_invitation_route(
    payload: AcceptInvitationIn,
    session: AsyncSession = Depends(get_session),
) -> AcceptInvitationOut:
    try:
        user = await accept_invitation_service(
            session,
            raw_token=payload.token,
            password=payload.password,
            full_name=payload.full_name,
        )
    except InvalidInvitationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired invitation") from exc
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A user with this email already exists"
        ) from exc

    return AcceptInvitationOut.model_validate(user)
