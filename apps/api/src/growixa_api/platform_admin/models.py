import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class SupportSession(Base):
    """An audited, time-limited platform-admin support session into one customer
    account (GRX-SAAS-010 / DEC-GRX-022). Not an impersonation token -- every
    session-scoped read/write route derives its account_id from this row and requires
    the caller's own platform_admin_id to match platform_admin_id, never from a
    client-supplied value."""

    __tablename__ = "support_sessions"
    __table_args__ = (
        CheckConstraint(
            "access_level IN ('READ', 'WRITE')", name="ck_support_sessions_access_level"
        ),
        # Must match the migration's create_index(..., postgresql_where=...) exactly --
        # otherwise --autogenerate sees a phantom drop/recreate on every future revision.
        Index(
            "ix_support_sessions_active",
            "account_id",
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform_admins.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_number: Mapped[str] = mapped_column(Text, nullable=False)
    access_level: Mapped[str] = mapped_column(Text, nullable=False, server_default="READ")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
