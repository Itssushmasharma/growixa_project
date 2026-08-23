"""Tests for GRX-SCHED-001: Campaign schedule/cancel lifecycle.

Tests cover:
- schedule_campaign: DRAFT → SCHEDULED with a future datetime
- schedule_campaign: CampaignAlreadyScheduledError when not DRAFT
- schedule_campaign: ValueError when scheduled_at is in the past
- schedule_campaign: CampaignNotFoundError for missing campaign
- cancel_campaign:   DRAFT → CANCELLED
- cancel_campaign:   SCHEDULED → CANCELLED
- cancel_campaign:   CampaignNotCancellableError when SENT or DISPATCHING
- cancel_campaign:   CampaignNotFoundError for missing campaign
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from growixa_api.campaigns.schemas import ScheduleCampaignIn
from growixa_api.campaigns.services import (
    CampaignAlreadyScheduledError,
    CampaignNotCancellableError,
    CampaignNotFoundError,
    cancel_campaign,
    schedule_campaign,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


# get_campaign is mocked in every test here, so the real value never matters -- just needs
# to satisfy schedule_campaign/cancel_campaign's account_id parameter (GRX-SAAS-001).
_ACCOUNT_ID = uuid.uuid4()


def _future(minutes: int = 30) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)


def _past(minutes: int = 5) -> datetime:
    return datetime.now(UTC) - timedelta(minutes=minutes)


def _make_campaign(status: str = "DRAFT") -> MagicMock:
    """Return a minimal Campaign ORM mock."""
    campaign = MagicMock()
    campaign.id = uuid.uuid4()
    campaign.status = status
    campaign.scheduled_at = None
    campaign.cancelled_at = None
    campaign.idempotency_key = uuid.uuid4()
    return campaign


def _fake_update(fields: dict[str, Any]) -> Any:
    """Return an async function that applies ``fields`` to the campaign mock."""

    async def _inner(_session: Any, campaign: Any, f: dict[str, Any]) -> Any:
        for k, v in f.items():
            setattr(campaign, k, v)
        return campaign

    return _inner


# ---------------------------------------------------------------------------
# schedule_campaign tests
# ---------------------------------------------------------------------------


class TestScheduleCampaign:
    @pytest.mark.asyncio
    async def test_draft_moves_to_scheduled(self) -> None:
        """A DRAFT campaign with a future scheduled_at becomes SCHEDULED."""
        campaign = _make_campaign(status="DRAFT")
        session = AsyncMock()

        async def _fake_update(s: Any, c: Any, f: dict[str, Any]) -> Any:
            _apply(c, f)
            return c

        with (
            patch(
                "growixa_api.campaigns.services.get_campaign",
                new=AsyncMock(return_value=campaign),
            ),
            patch(
                "growixa_api.campaigns.services.update_campaign_fields",
                new=AsyncMock(side_effect=_fake_update),
            ),
        ):
            scheduled_at = _future()
            result = await schedule_campaign(
                session, _ACCOUNT_ID, campaign.id, ScheduleCampaignIn(scheduled_at=scheduled_at)
            )
        assert result.status == "SCHEDULED"
        assert result.scheduled_at == scheduled_at

    @pytest.mark.asyncio
    async def test_already_scheduled_raises(self) -> None:
        """Scheduling a non-DRAFT campaign raises CampaignAlreadyScheduledError."""
        for bad_status in ("SCHEDULED", "DISPATCHING", "SENT", "CANCELLED", "FAILED"):
            campaign = _make_campaign(status=bad_status)
            session = AsyncMock()

            with (
                patch(
                    "growixa_api.campaigns.services.get_campaign",
                    new=AsyncMock(return_value=campaign),
                ),
                pytest.raises(CampaignAlreadyScheduledError),
            ):
                await schedule_campaign(
                    session, _ACCOUNT_ID, campaign.id, ScheduleCampaignIn(scheduled_at=_future())
                )

    @pytest.mark.asyncio
    async def test_past_datetime_raises(self) -> None:
        """scheduled_at in the past raises ValueError."""
        campaign = _make_campaign(status="DRAFT")
        session = AsyncMock()

        with (
            patch(
                "growixa_api.campaigns.services.get_campaign",
                new=AsyncMock(return_value=campaign),
            ),
            pytest.raises(ValueError, match="future"),
        ):
            await schedule_campaign(
                session, _ACCOUNT_ID, campaign.id, ScheduleCampaignIn(scheduled_at=_past())
            )

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        """Scheduling a nonexistent campaign raises CampaignNotFoundError."""
        session = AsyncMock()

        with (
            patch(
                "growixa_api.campaigns.services.get_campaign",
                new=AsyncMock(return_value=None),
            ),
            pytest.raises(CampaignNotFoundError),
        ):
            await schedule_campaign(
                session, _ACCOUNT_ID, uuid.uuid4(), ScheduleCampaignIn(scheduled_at=_future())
            )


# ---------------------------------------------------------------------------
# cancel_campaign tests
# ---------------------------------------------------------------------------


class TestCancelCampaign:
    @pytest.mark.asyncio
    async def test_cancel_draft(self) -> None:
        """A DRAFT campaign can be cancelled."""
        campaign = _make_campaign(status="DRAFT")
        session = AsyncMock()

        async def _fake_update_cancel(s: Any, c: Any, f: dict[str, Any]) -> Any:
            _apply(c, f)
            return c

        with (
            patch(
                "growixa_api.campaigns.services.get_campaign",
                new=AsyncMock(return_value=campaign),
            ),
            patch(
                "growixa_api.campaigns.services.update_campaign_fields",
                new=AsyncMock(side_effect=_fake_update_cancel),
            ),
        ):
            result = await cancel_campaign(session, _ACCOUNT_ID, campaign.id)

        assert result.status == "CANCELLED"
        assert result.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_cancel_scheduled(self) -> None:
        """A SCHEDULED campaign can be cancelled before dispatch."""
        campaign = _make_campaign(status="SCHEDULED")
        campaign.scheduled_at = _future()
        session = AsyncMock()

        async def _fake_update_sched(s: Any, c: Any, f: dict[str, Any]) -> Any:
            _apply(c, f)
            return c

        with (
            patch(
                "growixa_api.campaigns.services.get_campaign",
                new=AsyncMock(return_value=campaign),
            ),
            patch(
                "growixa_api.campaigns.services.update_campaign_fields",
                new=AsyncMock(side_effect=_fake_update_sched),
            ),
        ):
            result = await cancel_campaign(session, _ACCOUNT_ID, campaign.id)

        assert result.status == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_in_flight_emergency_stop(self) -> None:
        """A DISPATCHING or SENDING campaign can be cancelled mid-flight (Emergency Stop)."""
        for in_flight_status in ("DISPATCHING", "SENDING"):
            campaign = _make_campaign(status=in_flight_status)
            session = AsyncMock()

            async def _fake_update_cancel(s: Any, c: Any, f: dict[str, Any]) -> Any:
                _apply(c, f)
                return c

            with (
                patch(
                    "growixa_api.campaigns.services.get_campaign",
                    new=AsyncMock(return_value=campaign),
                ),
                patch(
                    "growixa_api.campaigns.services.update_campaign_fields",
                    new=AsyncMock(side_effect=_fake_update_cancel),
                ),
            ):
                result = await cancel_campaign(session, _ACCOUNT_ID, campaign.id)

            assert result.status == "CANCELLED"
            assert result.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_cancel_non_cancellable_raises(self) -> None:
        """SENT / FAILED campaigns cannot be cancelled."""
        for bad_status in ("SENT", "FAILED"):
            campaign = _make_campaign(status=bad_status)
            session = AsyncMock()

            with (
                patch(
                    "growixa_api.campaigns.services.get_campaign",
                    new=AsyncMock(return_value=campaign),
                ),
                pytest.raises(CampaignNotCancellableError),
            ):
                await cancel_campaign(session, _ACCOUNT_ID, campaign.id)

    @pytest.mark.asyncio
    async def test_cancel_not_found_raises(self) -> None:
        """Cancelling a nonexistent campaign raises CampaignNotFoundError."""
        session = AsyncMock()

        with (
            patch(
                "growixa_api.campaigns.services.get_campaign",
                new=AsyncMock(return_value=None),
            ),
            pytest.raises(CampaignNotFoundError),
        ):
            await cancel_campaign(session, _ACCOUNT_ID, uuid.uuid4())


# ---------------------------------------------------------------------------
# Tiny helper used inside side_effect lambdas
# ---------------------------------------------------------------------------


def _apply(campaign: Any, fields: dict[str, Any]) -> None:
    """Apply a dict of fields to a campaign mock in-place."""
    for k, v in fields.items():
        setattr(campaign, k, v)
