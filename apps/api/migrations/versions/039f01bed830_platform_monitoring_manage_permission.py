"""platform.monitoring.manage permission (GRX-SAAS-009)

Data-only migration -- infra monitoring (RabbitMQ queue depth) and the financial
dashboard (MRR/ARR/churn) are computed on the fly from existing tables, no new table
needed. Granted to platform.owner/admin (general oversight), platform.operations
(the queue-depth half), and platform.finance (the MRR/ARR/churn half) -- this one
permission code covers both halves of the single GRX-SAAS-009 panel.

Revision ID: 039f01bed830
Revises: fa291f6b37ca
Create Date: 2026-08-15 22:10:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "039f01bed830"
down_revision: str | Sequence[str] | None = "fa291f6b37ca"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLATFORM_PERM_MONITORING_MANAGE = uuid.UUID("863dd676-096c-4e5b-a4ae-b6feb7f0dd47")
GRANTED_ROLES = ("platform.owner", "platform.admin", "platform.operations", "platform.finance")


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.monitoring.manage', "
            "'View RabbitMQ queue depths and the MRR/ARR/churn financial dashboard')"
        ).bindparams(id=PLATFORM_PERM_MONITORING_MANAGE)
    )
    for role in GRANTED_ROLES:
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=PLATFORM_PERM_MONITORING_MANAGE)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("DELETE FROM platform_role_permissions WHERE permission_id = :id").bindparams(
            id=PLATFORM_PERM_MONITORING_MANAGE
        )
    )
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE id = :id").bindparams(
            id=PLATFORM_PERM_MONITORING_MANAGE
        )
    )
