"""customer accounts + user/auth isolation (GRX-SAAS-001 Phase A, users/auth slice)

Revision ID: 5e4d9cd719da
Revises: caf1c42204c9
Create Date: 2026-08-07 00:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5e4d9cd719da"
down_revision: str | Sequence[str] | None = "caf1c42204c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed so upgrade() and the (rare, dev-only) manual backfill reference the same row;
# generated once here rather than left to server_default, since downgrade() needs to
# delete this exact row and nothing else.
_SEED_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')", name="ck_accounts_status"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed one account and backfill every existing row into it -- this migration retrofits
    # isolation onto data that predates the concept of an account entirely, it does not
    # reset it. Real self-service-registered accounts (GRX-SAAS-003) are created after this.
    op.execute(
        sa.text("INSERT INTO accounts (id, name, status) VALUES (:id, :name, 'ACTIVE')").bindparams(
            id=_SEED_ACCOUNT_ID, name="Default Account"
        )
    )

    for table in (
        "users",
        "user_roles",
        "user_invitations",
        "refresh_tokens",
        "password_reset_tokens",
    ):
        op.add_column(table, sa.Column("account_id", sa.UUID(), nullable=True))
        op.execute(
            sa.text(f"UPDATE {table} SET account_id = :account_id").bindparams(  # noqa: S608
                account_id=_SEED_ACCOUNT_ID
            )
        )
        op.alter_column(table, "account_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table}_account_id_accounts",
            table,
            "accounts",
            ["account_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_account_id", table, ["account_id"])


def downgrade() -> None:
    """Downgrade schema."""
    for table in (
        "users",
        "user_roles",
        "user_invitations",
        "refresh_tokens",
        "password_reset_tokens",
    ):
        op.drop_index(f"ix_{table}_account_id", table_name=table)
        op.drop_constraint(f"fk_{table}_account_id_accounts", table, type_="foreignkey")
        op.drop_column(table, "account_id")

    op.execute(sa.text("DELETE FROM accounts WHERE id = :id").bindparams(id=_SEED_ACCOUNT_ID))
    op.drop_table("accounts")
