"""social posts idempotency key db default (Slice 5 GRX-SOCIAL-009 fix)

Revision ID: 5f1e2783a91f
Revises: 1cdd976bbe4e
Create Date: 2026-08-12 15:02:57.109575

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f1e2783a91f"
down_revision: str | Sequence[str] | None = "1cdd976bbe4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    Adds a DB-level server_default to social_posts.idempotency_key, matching
    campaigns.idempotency_key's identical fix-forward pattern
    (4a92b8107c12_scheduled_campaigns_schema.py) -- GRX-SOCIAL-004's original migration
    only relied on the SQLAlchemy model's Python-side `default=uuid.uuid4`, which never
    applies to a row inserted any other way (e.g. a raw INSERT, or a lightweight
    worker-side model in a test fixture that doesn't declare this column). The
    SQLAlchemy model deliberately stays unchanged, matching Campaign.idempotency_key's
    own precedent -- alembic's autogenerate never compares function-call
    server_defaults (`compare_server_default` isn't enabled in env.py), so this doesn't
    introduce `alembic check` drift.
    """
    op.alter_column(
        "social_posts",
        "idempotency_key",
        server_default=sa.text("gen_random_uuid()"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("social_posts", "idempotency_key", server_default=None)
