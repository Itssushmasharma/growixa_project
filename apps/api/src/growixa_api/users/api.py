import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import require_permission
from growixa_api.users.models import User
from growixa_api.users.schemas import (
    AcceptInvitationIn,
    AcceptInvitationOut,
    InviteUserIn,
    InviteUserOut,
    UpdateUserRoleIn,
    UpdateUserStatusIn,
    UserListItemOut,
)
from growixa_api.users.services import (
    EmailAlreadyRegisteredError,
    InvalidInvitationError,
    RoleNotFoundError,
    SelfActionNotAllowedError,
    UserNotFoundError,
)
from growixa_api.users.services import accept_invitation as accept_invitation_service
from growixa_api.users.services import invite_user as invite_user_service
from growixa_api.users.services import list_users_with_roles as list_users_with_roles_service
from growixa_api.users.services import update_user_role as update_user_role_service
from growixa_api.users.services import update_user_status as update_user_status_service

router = APIRouter(prefix="/users", tags=["users"])

_require_manage = require_permission("users.manage")


def _to_list_item(user: User, roles: list[str]) -> UserListItemOut:
    return UserListItemOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        last_login_at=user.last_login_at,
        roles=roles,
    )


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


@router.get("", response_model=list[UserListItemOut])
async def list_users_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> list[UserListItemOut]:
    users_with_roles = await list_users_with_roles_service(session)
    return [_to_list_item(user, roles) for user, roles in users_with_roles]


@router.patch("/{user_id}/status", response_model=UserListItemOut)
async def update_user_status_route(
    user_id: uuid.UUID,
    payload: UpdateUserStatusIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> UserListItemOut:
    try:
        user, roles = await update_user_status_service(
            session, actor_id=actor_id, user_id=user_id, status=payload.status
        )
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from exc
    except SelfActionNotAllowedError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You cannot disable your own account"
        ) from exc

    return _to_list_item(user, roles)


@router.patch("/{user_id}/role", response_model=UserListItemOut)
async def update_user_role_route(
    user_id: uuid.UUID,
    payload: UpdateUserRoleIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> UserListItemOut:
    try:
        user, roles = await update_user_role_service(
            session, actor_id=actor_id, user_id=user_id, role_name=payload.role_name
        )
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from exc
    except RoleNotFoundError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role") from exc

    return _to_list_item(user, roles)
