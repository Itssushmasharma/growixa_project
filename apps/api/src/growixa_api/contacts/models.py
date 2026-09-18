# ruff: noqa: E501

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class CRMCompany(Base):
    __tablename__ = "crm_companies"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_stage IN ('PROSPECT', 'LEAD', 'QUALIFIED', 'CUSTOMER', 'CHURNED', 'PARTNER', 'OTHER')",
            name="ck_crm_companies_lifecycle_stage",
        ),
        Index(
            "ux_crm_companies_account_id_domain",
            "account_id",
            "domain",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND domain IS NOT NULL"),
        ),
        Index("ix_crm_companies_account_created", "account_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str | None] = mapped_column(CITEXT, nullable=True)
    industry: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(Text, nullable=False, server_default="PROSPECT")
    custom_attributes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_contacts_status"),
        CheckConstraint(
            "lifecycle_stage IN ('SUBSCRIBER', 'LEAD', 'MQL', 'SQL', 'OPPORTUNITY', 'CUSTOMER', 'EVANGELIST', 'OTHER')",
            name="ck_contacts_lifecycle_stage",
        ),
        # GRX-SAAS-001: dedup is per-account, not global -- two different customers may
        # legitimately both have a contact at the same email address (unlike users.email,
        # which stays globally unique because it's a login identity, not audience data).
        # DEC-GRX-034: partial unique index so soft-deleted contacts don't block
        # re-import of the same email
        Index(
            "ux_contacts_account_id_email",
            "account_id",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_contacts_account_lifecycle", "account_id", "lifecycle_stage"),
        Index("ix_contacts_account_phone", "account_id", "phone"),
        Index("ix_contacts_account_company", "account_id", "company_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crm_companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    job_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(Text, nullable=False, server_default="LEAD")
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="ACTIVE")
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_attributes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    whatsapp_opt_out: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sms_opt_out: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ContactCustomField(Base):
    __tablename__ = "contact_custom_fields"
    __table_args__ = (
        CheckConstraint(
            "field_type IN ('TEXT', 'NUMBER', 'DATE', 'BOOLEAN')",
            name="ck_contact_custom_fields_type",
        ),
        # Custom field definitions (the schema, not the values) are per-account.
        UniqueConstraint("account_id", "key", name="ux_contact_custom_fields_account_id_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    field_type: Mapped[str] = mapped_column(Text, nullable=False)
    is_personalization_usable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactFieldValue(Base):
    __tablename__ = "contact_field_values"

    # Denormalized from contact_id's own account_id -- always accessed via an
    # already-account-verified contact_id in practice, but kept for schema consistency
    # with every other account-owned table (GRX-SAAS-001).
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contact_custom_fields.id", ondelete="CASCADE"),
        primary_key=True,
    )
    value: Mapped[str | None] = mapped_column(Text, nullable=True)


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("account_id", "name", name="ux_tags_account_id_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactTag(Base):
    __tablename__ = "contact_tags"

    # Denormalized -- see ContactFieldValue's identical note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class ContactList(Base):
    __tablename__ = "contact_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ContactListMember(Base):
    __tablename__ = "contact_list_members"

    # Denormalized -- see ContactFieldValue's identical note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contact_lists.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Segment(Base):
    __tablename__ = "segments"
    __table_args__ = (
        CheckConstraint("type IN ('DYNAMIC', 'SAVED')", name="ck_segments_type"),
        CheckConstraint("match_type IN ('ALL', 'ANY')", name="ck_segments_match_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    match_type: Mapped[str] = mapped_column(Text, nullable=False, server_default="ALL")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SegmentRule(Base):
    __tablename__ = "segment_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized from segment_id's own account_id -- see ContactFieldValue's note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class SegmentMember(Base):
    __tablename__ = "segment_members"

    # Denormalized -- see ContactFieldValue's identical note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactImport(Base):
    __tablename__ = "contact_imports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
            name="ck_contact_imports_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    column_mapping: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="PENDING")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ContactImportRow(Base):
    __tablename__ = "contact_import_rows"
    __table_args__ = (
        CheckConstraint(
            "status IN ('IMPORTED', 'UPDATED', 'SKIPPED', 'ERROR')",
            name="ck_contact_import_rows_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized from import_id's own account_id -- see ContactFieldValue's note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contact_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ConsentRecord(Base):
    """Insert-only compliance history — never updated after creation, mirroring
    `audit_logs`'s pattern. Current status per channel is derived as "most recent row",
    not stored as separate mutable state."""

    __tablename__ = "consent_records"
    __table_args__ = (
        CheckConstraint("channel IN ('EMAIL', 'SMS')", name="ck_consent_records_channel"),
        CheckConstraint(
            "status IN ('GRANTED', 'WITHDRAWN', 'UNKNOWN')", name="ck_consent_records_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized from contact_id's own account_id -- see ContactFieldValue's note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="UNKNOWN")
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SuppressionEntry(Base):
    """Either an exact-email entry (`email` set, `domain` and `phone` NULL), a whole-domain block
    (`domain` set, `email` and `phone` NULL), or a phone suppression (`phone` set, `email` and `domain` NULL).
    Domain entries are always `reason='MANUAL'`. Email/phone entries can be UNSUBSCRIBED/BOUNCED/COMPLAINED/MANUAL."""

    __tablename__ = "suppression_entries"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('UNSUBSCRIBED', 'BOUNCED', 'COMPLAINED', 'MANUAL')",
            name="ck_suppression_entries_reason",
        ),
        CheckConstraint(
            "(email IS NOT NULL AND domain IS NULL AND phone IS NULL) OR "
            "(email IS NULL AND domain IS NOT NULL AND phone IS NULL) OR "
            "(email IS NULL AND domain IS NULL AND phone IS NOT NULL)",
            name="ck_suppression_entries_target",
        ),
        # Suppression is per-account -- an address/phone suppressed by one customer's sends
        # doesn't suppress it for a different customer's own audience.
        UniqueConstraint("account_id", "email", name="ux_suppression_entries_account_id_email"),
        Index(
            "ux_suppression_entries_account_id_domain",
            "account_id",
            "domain",
            unique=True,
            postgresql_where=text("domain IS NOT NULL"),
        ),
        Index(
            "ux_suppression_entries_account_id_phone",
            "account_id",
            "phone",
            unique=True,
            postgresql_where=text("phone IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(CITEXT, nullable=True)
    domain: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    suppressed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    suppressed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactActivity(Base):
    __tablename__ = "contact_activities"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('NOTE', 'STAGE_CHANGE', 'TAG_ADDED', 'TAG_REMOVED', 'EMAIL_SENT', 'EMAIL_OPENED', 'IMPORT', 'CONSENT_CHANGE', 'TASK', 'CALL')",
            name="ck_contact_activities_type",
        ),
        Index(
            "ix_contact_activities_timeline", "account_id", "contact_id", text("created_at DESC")
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
