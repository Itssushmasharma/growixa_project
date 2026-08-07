"""seed platform.accounts.manage permission (GRX-SAAS-005 Phase E)

Revision ID: f1a2b3c4d5e6
Revises: 3186b6c66a6d
Create Date: 2026-08-07 15:10:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "3186b6c66a6d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Per DEC-GRX-020: only platform.owner/platform.admin get this code -- matches
# platform.admin's own stated scope in RBAC.md's Phase B role table ("Account/user
# management... day-to-day operations").
_GRANTED_ROLES = ("platform.owner", "platform.admin")

_PERMISSION_ID = uuid.uuid4()


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.accounts.manage', "
            "'List every customer account, view its users and login/security activity, "
            "activate/suspend/close an account')"
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
    op.execute(sa.text("DELETE FROM platform_permissions WHERE code = 'platform.accounts.manage'"))
