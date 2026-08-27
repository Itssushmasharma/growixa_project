"""company/brand AI Brand Control Center fields (GRX-COMPANY-003)

Revision ID: 72e376f46c26
Revises: f2a3b4c5d6e7
Create Date: 2026-08-26 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "72e376f46c26"
down_revision: str | Sequence[str] | None = "f2a3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("company_profile", sa.Column("support_email", sa.Text(), nullable=True))
    op.add_column("company_profile", sa.Column("sender_name", sa.Text(), nullable=True))
    op.add_column("company_profile", sa.Column("business_address", sa.Text(), nullable=True))
    op.add_column("company_profile", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "brand_profiles",
        sa.Column(
            "persona_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "brand_profiles",
        sa.Column(
            "voice_settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("brand_profiles", "voice_settings")
    op.drop_column("brand_profiles", "persona_tags")
    op.drop_column("company_profile", "description")
    op.drop_column("company_profile", "business_address")
    op.drop_column("company_profile", "sender_name")
    op.drop_column("company_profile", "support_email")
