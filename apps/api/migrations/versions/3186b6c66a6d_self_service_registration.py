"""self-service registration (GRX-SAAS-003 Phase C)

Revision ID: 3186b6c66a6d
Revises: a7222bcce561
Create Date: 2026-08-07 16:15:08.314502

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3186b6c66a6d"
down_revision: str | Sequence[str] | None = "a7222bcce561"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # users.status gains PENDING_VERIFICATION -- see DEC-GRX-019: reuses login()'s
    # existing status == "ACTIVE" check with zero new login-path code.
    op.drop_constraint("ck_users_status", "users", type_="check")
    op.create_check_constraint(
        "ck_users_status", "users", "status IN ('ACTIVE', 'DISABLED', 'PENDING_VERIFICATION')"
    )

    # accounts.selected_plan_slug -- recorded only, no FK (no plans table until Phase D).
    op.add_column("accounts", sa.Column("selected_plan_slug", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_accounts_selected_plan_slug", "accounts", "selected_plan_slug IN ('starter', 'growth')"
    )

    op.create_table(
        "account_verification_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_verification_tokens_account_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_account_verification_tokens_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_account_verification_tokens_account_id",
        "account_verification_tokens",
        ["account_id"],
    )
    op.create_index(
        "ix_account_verification_tokens_user_id", "account_verification_tokens", ["user_id"]
    )
    op.create_index(
        "ix_account_verification_tokens_expires_at",
        "account_verification_tokens",
        ["expires_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("account_verification_tokens")

    op.drop_constraint("ck_accounts_selected_plan_slug", "accounts", type_="check")
    op.drop_column("accounts", "selected_plan_slug")

    op.drop_constraint("ck_users_status", "users", type_="check")
    op.execute(
        sa.text("UPDATE users SET status = 'ACTIVE' WHERE status NOT IN ('ACTIVE', 'DISABLED')")
    )
    op.create_check_constraint("ck_users_status", "users", "status IN ('ACTIVE', 'DISABLED')")
