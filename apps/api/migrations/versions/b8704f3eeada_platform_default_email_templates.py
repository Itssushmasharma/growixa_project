"""platform-published default email templates (GRX-EMAIL-016)

Adds the platform/global-template concept the customer-owned `email_templates` table
never had: a reserved "platform system account" (`accounts.is_platform_system`, singleton
via a partial unique index) owns every platform-default template, and
`email_templates.is_platform_default` marks which of that account's templates are the
browsable defaults -- a customer "uses" one by cloning it into their own account, never by
editing the platform-owned row directly (clone-not-edit, see the app-layer service).

Also seeds the `platform.templates.manage` permission, granted to platform.owner/
platform.admin only -- same wiring and trust shape as `platform.ai.manage`/
`platform.email.manage`/`platform.validation.manage` (RBAC.md).

Revision ID: b8704f3eeada
Revises: 72e376f46c26
Create Date: 2026-08-30 00:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8704f3eeada"
down_revision: str | Sequence[str] | None = "72e376f46c26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed IDs so upgrade/downgrade and any future migration can reference these rows
# deterministically, same pattern as e926f73f7ece's ROLE_*/PLAN_* constants.
PLATFORM_SYSTEM_ACCOUNT_ID = uuid.UUID("6a6909fd-de57-48ea-b6f1-2f7860af6687")
PLATFORM_SYSTEM_ACCOUNT_SUBSCRIPTION_ID = uuid.UUID("c8695e38-22d0-469d-a35b-765d56db0944")
PLATFORM_PERM_TEMPLATES_MANAGE = uuid.UUID("3d32c194-f672-411f-b943-202bd46654cf")

# From e926f73f7ece_billing_schema_rbac_seed.py -- every account needs exactly one
# account_subscriptions row (BILLING_SYSTEM_ARCHITECTURE.md §3.4), the platform system
# account is no exception even though it's never actually billed.
PLAN_FREE = uuid.UUID("ec6e4dfc-72ed-41a9-b6ba-25b0e77c89af")

GRANTED_ROLES = ("platform.owner", "platform.admin")


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "accounts",
        sa.Column("is_platform_system", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    # Partial unique index on a boolean column filtered to true is the standard
    # singleton-row trick: at most one row can ever satisfy is_platform_system = true.
    op.create_index(
        "ux_accounts_platform_system_singleton",
        "accounts",
        ["is_platform_system"],
        unique=True,
        postgresql_where=sa.text("is_platform_system"),
    )

    op.add_column(
        "email_templates",
        sa.Column("is_platform_default", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index(
        "ix_email_templates_is_platform_default",
        "email_templates",
        ["is_platform_default"],
    )

    op.execute(
        sa.text(
            "INSERT INTO accounts (id, name, status, is_platform_system) "
            "VALUES (:id, 'Growixa Platform', 'ACTIVE', true)"
        ).bindparams(id=PLATFORM_SYSTEM_ACCOUNT_ID)
    )
    op.execute(
        sa.text(
            "INSERT INTO account_subscriptions "
            "(id, account_id, plan_id, status, currency, "
            "current_period_start, current_period_end) "
            "VALUES (:id, :account_id, :plan_id, 'ACTIVE', 'USD', "
            "now(), now() + interval '3650 days')"
        ).bindparams(
            id=PLATFORM_SYSTEM_ACCOUNT_SUBSCRIPTION_ID,
            account_id=PLATFORM_SYSTEM_ACCOUNT_ID,
            plan_id=PLAN_FREE,
        )
    )

    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.templates.manage', "
            "'Create/update/retire platform-published default email templates every "
            "account can browse and clone') "
            "ON CONFLICT (id) DO NOTHING"
        ).bindparams(id=PLATFORM_PERM_TEMPLATES_MANAGE)
    )
    for role in GRANTED_ROLES:
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id) "
                "ON CONFLICT DO NOTHING"
            ).bindparams(role=role, permission_id=PLATFORM_PERM_TEMPLATES_MANAGE)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("DELETE FROM platform_role_permissions WHERE permission_id = :id").bindparams(
            id=PLATFORM_PERM_TEMPLATES_MANAGE
        )
    )
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE id = :id").bindparams(
            id=PLATFORM_PERM_TEMPLATES_MANAGE
        )
    )

    op.execute(
        sa.text("DELETE FROM email_templates WHERE account_id = :account_id").bindparams(
            account_id=PLATFORM_SYSTEM_ACCOUNT_ID
        )
    )
    op.execute(
        sa.text("DELETE FROM account_subscriptions WHERE id = :id").bindparams(
            id=PLATFORM_SYSTEM_ACCOUNT_SUBSCRIPTION_ID
        )
    )
    op.execute(
        sa.text("DELETE FROM accounts WHERE id = :id").bindparams(id=PLATFORM_SYSTEM_ACCOUNT_ID)
    )

    op.drop_index("ix_email_templates_is_platform_default", table_name="email_templates")
    op.drop_column("email_templates", "is_platform_default")

    op.drop_index("ux_accounts_platform_system_singleton", table_name="accounts")
    op.drop_column("accounts", "is_platform_system")
