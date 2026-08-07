"""cross-cutting account isolation (GRX-SAAS-001 Phase A, audit_logs + usage_records)

Revision ID: 0d7bf0c46ead
Revises: 76a6d9161aed
Create Date: 2026-08-07 11:38:26.534842

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d7bf0c46ead"
down_revision: str | Sequence[str] | None = "76a6d9161aed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Same seeded account as every prior GRX-SAAS-001 migration.
_SEED_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    """Upgrade schema."""
    # audit_logs.account_id is NULLABLE by design (unlike every other table in this
    # retrofit) -- it mirrors the existing nullable actor_user_id: some events (an
    # unknown-email failed login, a password-reset request for an email that was never
    # registered) have no resolvable account at all. Backfilled from the acting user's
    # own account where one exists; left NULL otherwise -- those rows simply won't surface
    # through the account-scoped GET /audit endpoint, which is correct, since no account
    # owns them.
    op.add_column("audit_logs", sa.Column("account_id", sa.UUID(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE audit_logs SET account_id = users.account_id "
            "FROM users WHERE audit_logs.actor_user_id = users.id"
        )
    )
    op.create_foreign_key(
        "fk_audit_logs_account_id_accounts",
        "audit_logs",
        "accounts",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_audit_logs_account_id", "audit_logs", ["account_id"])

    # usage_records.account_id is NOT NULL -- every row has a real writer (the worker's
    # send_campaign.py, via campaign.account_id) with a resolvable account. Backfilled via
    # the recording user's own account, falling back to the seeded account for any row
    # with no created_by_user_id (matches every other table's backfill in this retrofit).
    op.add_column("usage_records", sa.Column("account_id", sa.UUID(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE usage_records SET account_id = users.account_id "
            "FROM users WHERE usage_records.created_by_user_id = users.id"
        )
    )
    op.execute(
        sa.text(
            "UPDATE usage_records SET account_id = :account_id WHERE account_id IS NULL"  # noqa: S608
        ).bindparams(account_id=_SEED_ACCOUNT_ID)
    )
    op.alter_column("usage_records", "account_id", nullable=False)
    op.create_foreign_key(
        "fk_usage_records_account_id_accounts",
        "usage_records",
        "accounts",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_usage_records_account_id", "usage_records", ["account_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_usage_records_account_id", table_name="usage_records")
    op.drop_constraint("fk_usage_records_account_id_accounts", "usage_records", type_="foreignkey")
    op.drop_column("usage_records", "account_id")

    op.drop_index("ix_audit_logs_account_id", table_name="audit_logs")
    op.drop_constraint("fk_audit_logs_account_id_accounts", "audit_logs", type_="foreignkey")
    op.drop_column("audit_logs", "account_id")
