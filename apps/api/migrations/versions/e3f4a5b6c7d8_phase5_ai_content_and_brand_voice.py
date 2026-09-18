"""Phase 5 AI content engine, brand voice & safety, human approval, and telemetry

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-09-16 15:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: str | Sequence[str] | None = "d2e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update ai_generations capability check constraint
    op.drop_constraint("ck_ai_generations_capability", "ai_generations", type_="check")
    op.create_check_constraint(
        "ck_ai_generations_capability",
        "ai_generations",
        "capability IN ("
        "'SUBJECT_LINE', 'BODY_COPY', 'SOCIAL_CAPTION', 'REWRITE', 'HASHTAGS', 'POSTING_TIME', "
        "'CTA', 'TONE_REWRITE', 'CONTENT_IDEAS', 'PLATFORM_REWRITE', 'CONTENT_REPURPOSE'"
        ")",
    )

    # 2. Add approval workflow columns to ai_generations
    op.add_column(
        "ai_generations",
        sa.Column(
            "approval_status",
            sa.Text(),
            nullable=False,
            server_default="PENDING_APPROVAL",
        ),
    )
    op.create_check_constraint(
        "ck_ai_generations_approval_status",
        "ai_generations",
        "approval_status IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'EDITED')",
    )
    op.add_column(
        "ai_generations",
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_generations",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("review_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("edited_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # 3. Add telemetry metadata columns to ai_generations
    op.add_column(
        "ai_generations",
        sa.Column("prompt_version", sa.Text(), nullable=False, server_default="v1.0.0"),
    )
    op.add_column(
        "ai_generations",
        sa.Column("input_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("output_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ai_generations",
        sa.Column("total_tokens", sa.Integer(), nullable=True),
    )

    # 4. Create indexes for approval queries and telemetry aggregation
    op.create_index(
        "ix_ai_generations_approval_status",
        "ai_generations",
        ["account_id", "approval_status"],
    )
    op.create_index(
        "ix_ai_generations_telemetry",
        "ai_generations",
        ["account_id", "provider", "model", "created_at"],
    )

    # 5. Add Brand Voice & Safety fields to brand_profiles
    op.add_column(
        "brand_profiles",
        sa.Column("brand_tone", sa.Text(), nullable=True),
    )
    op.add_column(
        "brand_profiles",
        sa.Column("target_audience", sa.Text(), nullable=True),
    )
    op.add_column(
        "brand_profiles",
        sa.Column(
            "preferred_vocabulary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "brand_profiles",
        sa.Column(
            "avoid_vocabulary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "brand_profiles",
        sa.Column(
            "compliance_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    # Drop Brand Voice columns
    op.drop_column("brand_profiles", "compliance_rules")
    op.drop_column("brand_profiles", "avoid_vocabulary")
    op.drop_column("brand_profiles", "preferred_vocabulary")
    op.drop_column("brand_profiles", "target_audience")
    op.drop_column("brand_profiles", "brand_tone")

    # Drop indexes
    op.drop_index("ix_ai_generations_telemetry", table_name="ai_generations")
    op.drop_index("ix_ai_generations_approval_status", table_name="ai_generations")

    # Drop telemetry columns
    op.drop_column("ai_generations", "total_tokens")
    op.drop_column("ai_generations", "output_tokens")
    op.drop_column("ai_generations", "input_tokens")
    op.drop_column("ai_generations", "prompt_version")

    # Drop approval columns
    op.drop_column("ai_generations", "edited_output")
    op.drop_column("ai_generations", "review_notes")
    op.drop_column("ai_generations", "reviewed_at")
    op.drop_column("ai_generations", "reviewed_by_user_id")
    op.drop_constraint("ck_ai_generations_approval_status", "ai_generations", type_="check")
    op.drop_column("ai_generations", "approval_status")

    # Revert capability constraint
    op.drop_constraint("ck_ai_generations_capability", "ai_generations", type_="check")
    op.create_check_constraint(
        "ck_ai_generations_capability",
        "ai_generations",
        "capability IN ("
        "'SUBJECT_LINE', 'BODY_COPY', 'SOCIAL_CAPTION', 'REWRITE', 'HASHTAGS', 'POSTING_TIME'"
        ")",
    )
