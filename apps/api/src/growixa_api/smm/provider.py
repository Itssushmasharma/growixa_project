import asyncio
import uuid
from datetime import datetime

from pydantic import BaseModel


class SMMService(BaseModel):
    id: str
    name: str
    platform: str
    rate: float  # Cost per 1000
    min_quantity: int
    max_quantity: int


class MockSMMProvider:
    """Mock integration with an external SMM Panel API (e.g., HQ SmartPanel)."""

    def __init__(self):
        self.services = [
            SMMService(
                id="tg_members_1",
                name="Telegram Members [Real/Active]",
                platform="Telegram",
                rate=2.50,
                min_quantity=100,
                max_quantity=100000,
            ),
            SMMService(
                id="tg_views_1",
                name="Telegram Post Views",
                platform="Telegram",
                rate=0.10,
                min_quantity=500,
                max_quantity=1000000,
            ),
            SMMService(
                id="ig_followers_1",
                name="Instagram Followers [Non-Drop]",
                platform="Instagram",
                rate=3.00,
                min_quantity=50,
                max_quantity=50000,
            ),
            SMMService(
                id="ig_likes_1",
                name="Instagram Likes [Instant]",
                platform="Instagram",
                rate=0.50,
                min_quantity=50,
                max_quantity=20000,
            ),
        ]

    async def get_services(self) -> list[SMMService]:
        """Fetch available services from the mock SMM provider."""
        await asyncio.sleep(0.5)  # Simulate network latency
        return self.services

    async def create_order(self, service_id: str, link: str, quantity: int) -> dict:
        """Place an order with the mock SMM provider."""
        await asyncio.sleep(1)  # Simulate network latency
        
        # Verify service exists
        service = next((s for s in self.services if s.id == service_id), None)
        if not service:
            raise ValueError(f"Service ID {service_id} not found")
            
        if quantity < service.min_quantity or quantity > service.max_quantity:
            raise ValueError(f"Quantity must be between {service.min_quantity} and {service.max_quantity}")

        return {
            "external_order_id": f"mock_ext_{uuid.uuid4().hex[:8]}",
            "status": "PROCESSING",
        }

    async def check_order_status(self, external_order_id: str) -> str:
        """Check the status of an existing order."""
        await asyncio.sleep(0.5)
        # Mocking logic: randomly return COMPLETED or PROCESSING
        import random
        return random.choice(["PROCESSING", "PROCESSING", "COMPLETED"])

smm_provider = MockSMMProvider()
