"""Add agency permissions

Revision ID: a00000000000
Revises: 99af1457f402
Create Date: 2026-09-17 12:35:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a00000000000"
down_revision: str | Sequence[str] | None = "99af1457f402"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles).
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"
ROLE_ANALYST = "6ab3fff0-9fcb-46e0-9cdb-0c54c7032ab3"

PERM_CLIENT_VIEW = uuid.UUID("c1a2c3d4-e5f6-7890-abcd-ef1234567890")
PERM_CLIENT_APPROVE = uuid.UUID("c2a2c3d4-e5f6-7890-abcd-ef1234567891")


def upgrade() -> None:
    """Seed client.view and client.approve permissions."""
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.Text()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    op.bulk_insert(
        permissions_table,
        [
            {
                "id": PERM_CLIENT_VIEW,
                "code": "client.view",
                "description": "View client portals and agency workspace data.",
            },
            {
                "id": PERM_CLIENT_APPROVE,
                "code": "client.approve",
                "description": "Approve content within the client portal approval workflow.",
            },
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_CLIENT_VIEW},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_CLIENT_VIEW},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_CLIENT_VIEW},
            {"role_id": ROLE_ANALYST, "permission_id": PERM_CLIENT_VIEW},
            
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_CLIENT_APPROVE},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_CLIENT_APPROVE},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_CLIENT_APPROVE},
        ],
    )


def downgrade() -> None:
    """Remove client permissions."""
    op.execute(
        sa.text("DELETE FROM role_permissions WHERE permission_id IN (:p1, :p2)").bindparams(
            p1=PERM_CLIENT_VIEW, p2=PERM_CLIENT_APPROVE
        )
    )
    op.execute(
        sa.text("DELETE FROM permissions WHERE id IN (:p1, :p2)").bindparams(
            p1=PERM_CLIENT_VIEW, p2=PERM_CLIENT_APPROVE
        )
    )
