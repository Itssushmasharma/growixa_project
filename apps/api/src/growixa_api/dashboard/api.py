import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.dashboard.schemas import DashboardOverviewOut
from growixa_api.dashboard.services import get_dashboard_overview
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewOut)
async def get_dashboard_overview_route(
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> DashboardOverviewOut:
    """No extra RBAC permission gate -- an account-wide rollup of things every logged-in
    member of the account can already see individually (own campaigns, contacts, quota),
    same auth-only shape as GET /auth/me, not a new visibility surface."""
    return await get_dashboard_overview(session, account_id)
