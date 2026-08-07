"""seed platform.usage.manage permission (GRX-SAAS-008 Phase E)

Revision ID: a3b4c5d6e7f8
Revises: f1a2b3c4d5e6
Create Date: 2026-08-07 16:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Per DEC-GRX-021: usage/campaign oversight is support-facing, not billing/infra-facing --
# platform.owner (full control), platform.admin (day-to-day ops), and platform.support
# (the tracker's own stated actor) get this code; finance/operations do not.
_GRANTED_ROLES = ("platform.owner", "platform.admin", "platform.support")

_PERMISSION_ID = uuid.uuid4()


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.usage.manage', "
            "'View per-account usage summaries and cross-account campaign oversight; "
            "pause a suspicious campaign')"
        ).bindparams(id=_PERMISSION_ID)
    )
    for role in _GRANTED_ROLES:
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=_PERMISSION_ID)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DELETE FROM platform_permissions WHERE code = 'platform.usage.manage'"))
