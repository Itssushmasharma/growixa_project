"""Add ai.review permission for human manager approval workflow (Phase 5)

Revision ID: f5a6b7c8d9e0
Revises: e3f4a5b6c7d8
Create Date: 2026-09-16 16:00:00.000000

Adds the `ai.review` permission required by the human-manager approval workflow
introduced in Phase 5 (DEC-GRX-006). Granted to Super Admin, Admin, and
Marketing Manager roles — the same roles with oversight responsibility for
published content. Content Creators and Analysts do not get this permission;
they generate content but cannot self-approve it (GRX-AI-006).
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5a6b7c8d9e0"
down_revision: str | Sequence[str] | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles).
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"

PERM_AI_REVIEW = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def upgrade() -> None:
    """Seed ai.review permission and grant to manager-level roles."""
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
                "id": PERM_AI_REVIEW,
                "code": "ai.review",
                "description": (
                    "Approve, reject, or edit AI-generated content before it is used "
                    "in campaigns or social posts (human-in-the-loop gate, DEC-GRX-006)"
                ),
            },
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            # Super Admin and Admin have full oversight.
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_AI_REVIEW},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_AI_REVIEW},
            # Marketing Manager approves/edits content before publishing.
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_AI_REVIEW},
            # Content Creator and Analyst intentionally excluded:
            # creators generate content but cannot self-approve it (GRX-AI-006).
        ],
    )


def downgrade() -> None:
    """Remove ai.review permission and its role grants."""
    op.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id = :id"
        ).bindparams(id=PERM_AI_REVIEW)
    )
    op.execute(
        sa.text(
            "DELETE FROM permissions WHERE id = :id"
        ).bindparams(id=PERM_AI_REVIEW)
    )
