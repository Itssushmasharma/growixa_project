import uuid
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id
from growixa_api.campaigns.models import Campaign
from growixa_api.social.models import SocialPost
from growixa_api.whatsapp.models import WhatsAppCampaign
from growixa_api.sms.models import SMSCampaign
from .schemas import CalendarEvent

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.get("/events", response_model=list[CalendarEvent])
async def get_calendar_events(
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    # Fetch Campaigns
    campaigns_result = await session.execute(
        select(Campaign).where(
            Campaign.account_id == account_id,
            Campaign.scheduled_at.isnot(None)
        )
    )
    campaigns = campaigns_result.scalars().all()
    
    # Fetch Social Posts
    posts_result = await session.execute(
        select(SocialPost).where(
            SocialPost.account_id == account_id,
            SocialPost.scheduled_at.isnot(None)
        )
    )
    posts = posts_result.scalars().all()
    
    # Fetch Whatsapp Campaigns
    wa_result = await session.execute(
        select(WhatsAppCampaign).where(
            WhatsAppCampaign.account_id == account_id,
            WhatsAppCampaign.scheduled_at.isnot(None)
        )
    )
    wa_campaigns = wa_result.scalars().all()
    
    # Fetch SMS Campaigns
    sms_result = await session.execute(
        select(SMSCampaign).where(
            SMSCampaign.account_id == account_id,
            SMSCampaign.scheduled_at.isnot(None)
        )
    )
    sms_campaigns = sms_result.scalars().all()
    
    events = []
    
    for c in campaigns:
        events.append(
            CalendarEvent(
                id=c.id,
                channel="EMAIL",
                title=c.name,
                status=c.status,
                scheduled_at=c.scheduled_at,
                assignee_id=c.created_by_user_id,
            )
        )
        
    for p in posts:
        title = (p.caption[:30] + "...") if p.caption and len(p.caption) > 30 else (p.caption or "Untitled Post")
        events.append(
            CalendarEvent(
                id=p.id,
                channel="SOCIAL",
                title=title,
                status=p.status,
                scheduled_at=p.scheduled_at,
                assignee_id=p.created_by_user_id,
            )
        )
        
    for w in wa_campaigns:
        events.append(
            CalendarEvent(
                id=w.id,
                channel="WHATSAPP",
                title=w.name,
                status=w.status,
                scheduled_at=w.scheduled_at,
                assignee_id=None,
            )
        )
        
    for s in sms_campaigns:
        events.append(
            CalendarEvent(
                id=s.id,
                channel="SMS",
                title=s.name,
                status=s.status,
                scheduled_at=s.scheduled_at,
                assignee_id=None,
            )
        )
        
    # Sort events by scheduled_at
    events.sort(key=lambda x: x.scheduled_at.timestamp() if x.scheduled_at else 0.0)
    
    return events
