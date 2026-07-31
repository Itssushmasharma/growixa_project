import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import CITEXT, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_contacts_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="ACTIVE")
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
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
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    field_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactFieldValue(Base):
    __tablename__ = "contact_field_values"

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

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactTag(Base):
    __tablename__ = "contact_tags"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class ContactList(Base):
    __tablename__ = "contact_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    __table_args__ = (CheckConstraint("type IN ('DYNAMIC', 'SAVED')", name="ck_segments_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
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
    __tablename__ = "suppression_entries"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('UNSUBSCRIBED', 'BOUNCED', 'COMPLAINED', 'MANUAL')",
            name="ck_suppression_entries_reason",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True
    )
    suppressed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    suppressed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
