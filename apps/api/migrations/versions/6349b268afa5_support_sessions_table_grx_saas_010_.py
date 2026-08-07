"""support sessions table (GRX-SAAS-010 Phase E)

Revision ID: 6349b268afa5
Revises: a3b4c5d6e7f8
Create Date: 2026-08-07 21:33:50.520225

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6349b268afa5"
down_revision: str | Sequence[str] | None = "a3b4c5d6e7f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Per DEC-GRX-022: platform.support_session.create is granted to owner/admin/support
# (matching platform.support's stated scope); platform.support_session.write is
# owner/admin only -- the "separate permission gate for write access" the tracker's own
# wording asks for.
_CREATE_ROLES = ("platform.owner", "platform.admin", "platform.support")
_WRITE_ROLES = ("platform.owner", "platform.admin")

_CREATE_PERMISSION_ID = uuid.uuid4()
_WRITE_PERMISSION_ID = uuid.uuid4()


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "support_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("platform_admin_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("ticket_number", sa.Text(), nullable=False),
        sa.Column("access_level", sa.Text(), nullable=False, server_default="READ"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
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
            "access_level IN ('READ', 'WRITE')", name="ck_support_sessions_access_level"
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_support_sessions_account_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["platform_admin_id"],
            ["platform_admins.id"],
            name="fk_support_sessions_platform_admin_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_support_sessions_account_id", "support_sessions", ["account_id"])
    op.create_index(
        "ix_support_sessions_platform_admin_id", "support_sessions", ["platform_admin_id"]
    )
    # Partial index for the customer-facing "is a session currently active on my
    # account" check (THREAT_MODEL.md T42) -- cheap even as the table grows, since it
    # only ever indexes the (small) set of not-yet-ended sessions.
    op.create_index(
        "ix_support_sessions_active",
        "support_sessions",
        ["account_id"],
        postgresql_where=sa.text("ended_at IS NULL"),
    )

    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.support_session.create', "
            "'Start an audited, time-limited support session into a customer account; "
            "view its data; end it early')"
        ).bindparams(id=_CREATE_PERMISSION_ID)
    )
    for role in _CREATE_ROLES:
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=_CREATE_PERMISSION_ID)
        )

    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.support_session.write', "
            "'Start a support session with write access, and perform the gated write "
            "action through an active one')"
        ).bindparams(id=_WRITE_PERMISSION_ID)
    )
    for role in _WRITE_ROLES:
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=_WRITE_PERMISSION_ID)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE code = 'platform.support_session.write'")
    )
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE code = 'platform.support_session.create'")
    )
    op.drop_index("ix_support_sessions_active", table_name="support_sessions")
    op.drop_index("ix_support_sessions_platform_admin_id", table_name="support_sessions")
    op.drop_index("ix_support_sessions_account_id", table_name="support_sessions")
    op.drop_table("support_sessions")
