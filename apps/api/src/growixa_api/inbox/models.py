import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from growixa_api.db import Base

class InboxConversation(Base):
    __tablename__ = "inbox_conversations"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('WHATSAPP', 'IG_DM', 'FB_COMMENT', 'EMAIL', 'TWITTER_DM')",
            name="ck_inbox_conversations_channel",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'CLOSED', 'SNOOZED')",
            name="ck_inbox_conversations_status",
        ),
        Index("ix_inbox_conversations_account_status", "account_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Platform-specific identifier (e.g., WA Phone Number, IG Username)
    channel_identity_id: Mapped[str] = mapped_column(Text, nullable=False)
    
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="OPEN")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class InboxMessage(Base):
    __tablename__ = "inbox_messages"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('INBOUND', 'OUTBOUND')",
            name="ck_inbox_messages_direction",
        ),
        Index("ix_inbox_messages_conversation_id", "conversation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inbox_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    direction: Mapped[str] = mapped_column(Text, nullable=False)
    
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_urls: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    
    provider_message_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
