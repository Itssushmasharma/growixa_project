"""oauth identities table and nullable password (GRX-AUTH-006)

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-08-23 00:22:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Allow nullable password_hash on users table for passwordless OAuth users
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.Text(),
        nullable=True,
    )

    # 2. Create oauth_identities table
    op.create_table(
        "oauth_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_user_id", sa.Text(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False, index=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "provider", "provider_user_id", name="ux_oauth_identities_provider_uid"
        ),
    )

    op.create_index(
        "ix_oauth_identities_user_provider",
        "oauth_identities",
        ["user_id", "provider"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_oauth_identities_user_provider", table_name="oauth_identities")
    op.drop_table("oauth_identities")
    op.execute(
        sa.text(
            "UPDATE users SET password_hash = '$argon2id$v=19$m=65536,t=3,p=4$disabled$disabled' "
            "WHERE password_hash IS NULL"
        )
    )
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.Text(),
        nullable=False,
    )
