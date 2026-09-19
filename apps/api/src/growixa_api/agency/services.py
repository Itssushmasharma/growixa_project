import uuid
from collections.abc import Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.agency.models import Agency, AgencyClient, WhiteLabelConfig
from growixa_api.agency.schemas import (
    AgencyClientCreate,
    AgencyCreate,
    WhiteLabelConfigUpdate,
)


async def create_agency(session: AsyncSession, owner_id: uuid.UUID, data: AgencyCreate) -> Agency:
    agency = Agency(name=data.name, owner_id=owner_id)
    session.add(agency)
    await session.commit()
    await session.refresh(agency)

    # Auto-create white label config
    wl = WhiteLabelConfig(agency_id=agency.id, portal_name="Client Portal")
    session.add(wl)
    await session.commit()

    return agency


async def get_agencies_for_user(session: AsyncSession, user_id: uuid.UUID) -> Sequence[Agency]:
    result = await session.execute(select(Agency).where(Agency.owner_id == user_id))
    return result.scalars().all()


async def get_agency(session: AsyncSession, agency_id: uuid.UUID, user_id: uuid.UUID) -> Agency:
    agency = await session.get(Agency, agency_id)
    if not agency or agency.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency


async def create_agency_client(
    session: AsyncSession, agency_id: uuid.UUID, data: AgencyClientCreate, user_id: uuid.UUID
) -> AgencyClient:
    agency = await get_agency(session, agency_id, user_id)

    # Existing accounts require a verified invitation/acceptance flow before linking.
    if data.account_id is not None or data.account_manager_id is not None:
        raise HTTPException(
            409, "Existing account linking and manager assignment are pending verification"
        )

    # Create the isolated account for this client if not provided
    account_id = data.account_id
    if not account_id:
        new_account = Account(name=data.client_name)
        session.add(new_account)
        await session.flush()
        account_id = new_account.id

    client = AgencyClient(
        agency_id=agency.id,
        account_id=account_id,
        client_name=data.client_name,
        account_manager_id=data.account_manager_id,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


async def get_agency_clients(
    session: AsyncSession, agency_id: uuid.UUID, user_id: uuid.UUID
) -> Sequence[AgencyClient]:
    await get_agency(session, agency_id, user_id)
    result = await session.execute(select(AgencyClient).where(AgencyClient.agency_id == agency_id))
    return result.scalars().all()


async def update_white_label_config(
    session: AsyncSession, agency_id: uuid.UUID, data: WhiteLabelConfigUpdate, user_id: uuid.UUID
) -> WhiteLabelConfig:
    await get_agency(session, agency_id, user_id)
    result = await session.execute(
        select(WhiteLabelConfig).where(WhiteLabelConfig.agency_id == agency_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        config = WhiteLabelConfig(agency_id=agency_id)
        session.add(config)

    if data.custom_domain is not None:
        config.custom_domain = data.custom_domain
    if data.portal_name is not None:
        config.portal_name = data.portal_name
    if data.logo_url is not None:
        config.logo_url = data.logo_url
    if data.primary_color is not None:
        config.primary_color = data.primary_color
    if data.secondary_color is not None:
        config.secondary_color = data.secondary_color

    await session.commit()
    await session.refresh(config)
    return config


async def get_white_label_config(
    session: AsyncSession, agency_id: uuid.UUID, user_id: uuid.UUID
) -> WhiteLabelConfig:
    await get_agency(session, agency_id, user_id)
    result = await session.execute(
        select(WhiteLabelConfig).where(WhiteLabelConfig.agency_id == agency_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="White label config not found")
    return config
