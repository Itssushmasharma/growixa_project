# ruff: noqa: E501
"""Phase 2 CRM and audience platform schema migration

Revision ID: c7d8e9f0a1b2
Revises: b8704f3eeada
Create Date: 2026-09-15 16:30:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: str | Sequence[str] | None = "b8704f3eeada"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create crm_companies
    op.create_table(
        "crm_companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("domain", postgresql.CITEXT(), nullable=True),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("lifecycle_stage", sa.Text(), nullable=False, server_default="PROSPECT"),
        sa.Column(
            "custom_attributes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "lifecycle_stage IN ('PROSPECT', 'LEAD', 'QUALIFIED', 'CUSTOMER', 'CHURNED', 'PARTNER', 'OTHER')",
            name="ck_crm_companies_lifecycle_stage",
        ),
    )
    op.create_index(
        "ux_crm_companies_account_id_domain",
        "crm_companies",
        ["account_id", "domain"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND domain IS NOT NULL"),
    )
    op.create_index(
        "ix_crm_companies_account_created",
        "crm_companies",
        ["account_id", "created_at"],
    )

    # 2. Add CRM fields to contacts
    op.add_column(
        "contacts",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crm_companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("contacts", sa.Column("job_title", sa.Text(), nullable=True))
    op.add_column(
        "contacts",
        sa.Column("lifecycle_stage", sa.Text(), nullable=False, server_default="LEAD"),
    )
    op.add_column(
        "contacts",
        sa.Column(
            "custom_attributes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_check_constraint(
        "ck_contacts_lifecycle_stage",
        "contacts",
        "lifecycle_stage IN ('SUBSCRIBER', 'LEAD', 'MQL', 'SQL', 'OPPORTUNITY', 'CUSTOMER', 'EVANGELIST', 'OTHER')",
    )
    op.create_index("ix_contacts_account_lifecycle", "contacts", ["account_id", "lifecycle_stage"])
    op.create_index("ix_contacts_account_phone", "contacts", ["account_id", "phone"])
    op.create_index("ix_contacts_account_company", "contacts", ["account_id", "company_id"])

    # 3. Create contact_activities
    op.create_table(
        "contact_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("activity_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "activity_type IN ('NOTE', 'STAGE_CHANGE', 'TAG_ADDED', 'TAG_REMOVED', 'EMAIL_SENT', 'EMAIL_OPENED', 'IMPORT', 'CONSENT_CHANGE', 'TASK', 'CALL')",
            name="ck_contact_activities_type",
        ),
    )
    op.create_index(
        "ix_contact_activities_timeline",
        "contact_activities",
        ["account_id", "contact_id", sa.text("created_at DESC")],
    )

    # 4. Add match_type to segments
    op.add_column(
        "segments",
        sa.Column("match_type", sa.Text(), nullable=False, server_default="ALL"),
    )
    op.create_check_constraint(
        "ck_segments_match_type",
        "segments",
        "match_type IN ('ALL', 'ANY')",
    )

    # 5. Add phone to suppression_entries and update constraints
    op.add_column("suppression_entries", sa.Column("phone", sa.Text(), nullable=True))
    op.drop_constraint(
        "ck_suppression_entries_email_xor_domain", "suppression_entries", type_="check"
    )
    op.create_check_constraint(
        "ck_suppression_entries_target",
        "suppression_entries",
        "(email IS NOT NULL AND domain IS NULL AND phone IS NULL) OR "
        "(email IS NULL AND domain IS NOT NULL AND phone IS NULL) OR "
        "(email IS NULL AND domain IS NULL AND phone IS NOT NULL)",
    )
    op.create_index(
        "ux_suppression_entries_account_id_phone",
        "suppression_entries",
        ["account_id", "phone"],
        unique=True,
        postgresql_where=sa.text("phone IS NOT NULL"),
    )


def downgrade() -> None:
    # 5. Reverse suppression_entries changes
    op.drop_index("ux_suppression_entries_account_id_phone", table_name="suppression_entries")
    op.drop_constraint("ck_suppression_entries_target", "suppression_entries", type_="check")
    op.create_check_constraint(
        "ck_suppression_entries_email_xor_domain",
        "suppression_entries",
        "(email IS NOT NULL AND domain IS NULL) OR (email IS NULL AND domain IS NOT NULL)",
    )
    op.drop_column("suppression_entries", "phone")

    # 4. Reverse segments changes
    op.drop_constraint("ck_segments_match_type", "segments", type_="check")
    op.drop_column("segments", "match_type")

    # 3. Drop contact_activities
    op.drop_index("ix_contact_activities_timeline", table_name="contact_activities")
    op.drop_table("contact_activities")

    # 2. Reverse contacts additions
    op.drop_index("ix_contacts_account_company", table_name="contacts")
    op.drop_index("ix_contacts_account_phone", table_name="contacts")
    op.drop_index("ix_contacts_account_lifecycle", table_name="contacts")
    op.drop_constraint("ck_contacts_lifecycle_stage", "contacts", type_="check")
    op.drop_column("contacts", "custom_attributes")
    op.drop_column("contacts", "lifecycle_stage")
    op.drop_column("contacts", "job_title")
    op.drop_column("contacts", "company_id")

    # 1. Drop crm_companies
    op.drop_index("ix_crm_companies_account_created", table_name="crm_companies")
    op.drop_index("ux_crm_companies_account_id_domain", table_name="crm_companies")
    op.drop_table("crm_companies")
