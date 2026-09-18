import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id
from growixa_api.smm.models import SMMOrder
from growixa_api.smm.provider import smm_provider

router = APIRouter(prefix="/smm", tags=["smm"])


class SMMServiceOut(BaseModel):
    id: str
    name: str
    platform: str
    rate: float
    min_quantity: int
    max_quantity: int


class OrderCreateIn(BaseModel):
    service_id: str
    target_url: str
    quantity: int


class SMMOrderOut(BaseModel):
    id: uuid.UUID
    service_name: str
    platform: str
    target_url: str
    quantity: int
    status: str
    external_order_id: str | None


@router.get("/services", response_model=List[SMMServiceOut])
async def list_services() -> List[SMMServiceOut]:
    """Get list of available SMM services."""
    services = await smm_provider.get_services()
    return [
        SMMServiceOut(
            id=s.id,
            name=s.name,
            platform=s.platform,
            rate=s.rate,
            min_quantity=s.min_quantity,
            max_quantity=s.max_quantity,
        )
        for s in services
    ]


@router.post("/orders", response_model=SMMOrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateIn,
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SMMOrderOut:
    """Place a new SMM order."""
    services = await smm_provider.get_services()
    service = next((s for s in services if s.id == payload.service_id), None)
    if not service:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid service_id")

    try:
        response = await smm_provider.create_order(
            service_id=payload.service_id,
            link=payload.target_url,
            quantity=payload.quantity,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    order = SMMOrder(
        account_id=account_id,
        service_id=service.id,
        service_name=service.name,
        platform=service.platform,
        target_url=payload.target_url,
        quantity=payload.quantity,
        external_order_id=response.get("external_order_id"),
        status=response.get("status", "PENDING"),
    )
    
    session.add(order)
    await session.commit()
    await session.refresh(order)
    
    return SMMOrderOut(
        id=order.id,
        service_name=order.service_name,
        platform=order.platform,
        target_url=order.target_url,
        quantity=order.quantity,
        status=order.status,
        external_order_id=order.external_order_id,
    )


@router.get("/orders", response_model=List[SMMOrderOut])
async def list_orders(
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> List[SMMOrderOut]:
    """Get list of past SMM orders."""
    stmt = select(SMMOrder).where(SMMOrder.account_id == account_id).order_by(SMMOrder.created_at.desc())
    result = await session.execute(stmt)
    orders = result.scalars().all()
    
    return [
        SMMOrderOut(
            id=o.id,
            service_name=o.service_name,
            platform=o.platform,
            target_url=o.target_url,
            quantity=o.quantity,
            status=o.status,
            external_order_id=o.external_order_id,
        )
        for o in orders
    ]
