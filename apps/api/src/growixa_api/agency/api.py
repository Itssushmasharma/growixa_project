import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.agency import services
from growixa_api.agency.schemas import (
    AgencyClientCreate,
    AgencyClientOut,
    AgencyCreate,
    AgencyOut,
    WhiteLabelConfigOut,
    WhiteLabelConfigUpdate,
)
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_user_id

router = APIRouter(prefix="/agencies", tags=["agencies"])


@router.post("", response_model=AgencyOut)
async def create_agency(
    data: AgencyCreate,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new agency workspace."""
    return await services.create_agency(session, user_id, data)


@router.get("", response_model=list[AgencyOut])
async def list_agencies(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """List agencies owned by the current user."""
    return await services.get_agencies_for_user(session, user_id)


@router.get("/{agency_id}", response_model=AgencyOut)
async def get_agency(
    agency_id: uuid.UUID,
    user_id: Annotated[
        uuid.UUID, Depends(get_current_user_id)
    ],  # Security: Should verify ownership
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get details of a specific agency."""
    # Note: In a real app we'd verify user_id is the owner or a team member.
    return await services.get_agency(session, agency_id)


@router.post("/{agency_id}/clients", response_model=AgencyClientOut)
async def create_agency_client(
    agency_id: uuid.UUID,
    data: AgencyClientCreate,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Onboard a new client for the agency."""
    return await services.create_agency_client(session, agency_id, data)


@router.get("/{agency_id}/clients", response_model=list[AgencyClientOut])
async def list_agency_clients(
    agency_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """List all clients under this agency."""
    return await services.get_agency_clients(session, agency_id)


@router.put("/{agency_id}/white-label", response_model=WhiteLabelConfigOut)
async def update_white_label(
    agency_id: uuid.UUID,
    data: WhiteLabelConfigUpdate,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Update white label settings for the agency portal."""
    return await services.update_white_label_config(session, agency_id, data)


@router.get("/{agency_id}/white-label", response_model=WhiteLabelConfigOut)
async def get_white_label(
    agency_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get white label configuration."""
    return await services.get_white_label_config(session, agency_id)
