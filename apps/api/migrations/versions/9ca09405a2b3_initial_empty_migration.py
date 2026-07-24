"""initial empty migration

Revision ID: 9ca09405a2b3
Revises:
Create Date: 2026-07-24 20:04:02.720953

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "9ca09405a2b3"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
