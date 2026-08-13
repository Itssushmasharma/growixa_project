"""credit_packs table (Slice 7 GRX-BILL-004)

Revision ID: b6eed962fd56
Revises: 60f7c30ff18a
Create Date: 2026-08-13 00:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6eed962fd56"
down_revision: str | Sequence[str] | None = "60f7c30ff18a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PACK_AI_RUNS_250 = uuid.UUID("2f6a2a8e-9d1a-4e3a-8b7c-3f1a6c2d4e5f")
PACK_AI_RUNS_1000 = uuid.UUID("3a7b3b9f-ae2b-4f4b-9c8d-4a2b7d3e5f6a")
PACK_EMAIL_SENDS_10000 = uuid.UUID("4b8c4cae-bf3c-4a5c-ad9e-5b3c8e4f6a7b")
PACK_CONTACT_SLOTS_2500 = uuid.UUID("5c9d5dbf-ca4d-4b6d-be0f-6c4d9f5a7b8c")
PACK_SOCIAL_POSTS_50 = uuid.UUID("6dae6eca-db5e-4c7e-cf1a-7d5eaa6b8c9d")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "credit_packs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("credit_type", sa.Text(), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("price_usd", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_inr", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "credit_type IN ('AI_RUNS', 'EMAIL_SENDS', 'CONTACT_SLOTS', 'SOCIAL_POSTS')",
            name="ck_credit_packs_credit_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    _seed_default_packs()


def _seed_default_packs() -> None:
    """Working-draft prices per BILLING_SYSTEM_ARCHITECTURE.md §2/
    subscription_plans_matrix.csv, same "accepted as a starting point, editable later
    via platform.billing.manage" status as the subscription_plans rows. USD left NULL
    for now -- international payments aren't yet approved on the Razorpay account
    (found live, GRX-BILL-002's plan-sync follow-up); set once that's resolved."""
    credit_packs_table = sa.table(
        "credit_packs",
        sa.column("id", sa.UUID()),
        sa.column("slug", sa.Text()),
        sa.column("name", sa.Text()),
        sa.column("credit_type", sa.Text()),
        sa.column("credits", sa.Integer()),
        sa.column("price_usd", sa.Numeric(10, 2)),
        sa.column("price_inr", sa.Numeric(10, 2)),
    )
    op.bulk_insert(
        credit_packs_table,
        [
            {
                "id": PACK_AI_RUNS_250,
                "slug": "ai_runs_250",
                "name": "250 AI Runs",
                "credit_type": "AI_RUNS",
                "credits": 250,
                "price_usd": None,
                "price_inr": 400,
            },
            {
                "id": PACK_AI_RUNS_1000,
                "slug": "ai_runs_1000",
                "name": "1,000 AI Runs",
                "credit_type": "AI_RUNS",
                "credits": 1000,
                "price_usd": None,
                "price_inr": 1200,
            },
            {
                "id": PACK_EMAIL_SENDS_10000,
                "slug": "email_sends_10000",
                "name": "10,000 Email Sends",
                "credit_type": "EMAIL_SENDS",
                "credits": 10000,
                "price_usd": None,
                "price_inr": 800,
            },
            {
                "id": PACK_CONTACT_SLOTS_2500,
                "slug": "contact_slots_2500",
                "name": "2,500 Extra Contacts",
                "credit_type": "CONTACT_SLOTS",
                "credits": 2500,
                "price_usd": None,
                "price_inr": 800,
            },
            {
                "id": PACK_SOCIAL_POSTS_50,
                "slug": "social_posts_50",
                "name": "50 Extra Social Posts",
                "credit_type": "SOCIAL_POSTS",
                "credits": 50,
                "price_usd": None,
                "price_inr": 400,
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("credit_packs")
