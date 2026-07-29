import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import require_permission
from growixa_api.roles.repositories import list_roles
from growixa_api.roles.schemas import RoleOut

router = APIRouter(prefix="/roles", tags=["roles"])

# Gated by users.manage, not roles.manage: this exists to populate a role-selection
# dropdown for inviting/reassigning users, not to view the permission matrix itself
# (roles.manage's actual purpose per RBAC.md) — both permissions have identical
# Super Admin/Admin-only grants in Sprint 1, so this is a scope choice, not a security gap.
_require_manage = require_permission("users.manage")


@router.get("", response_model=list[RoleOut])
async def list_roles_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> list[RoleOut]:
    roles = await list_roles(session)
    return [RoleOut.model_validate(role) for role in roles]
