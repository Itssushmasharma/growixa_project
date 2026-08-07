import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base

# The five roles a platform_admin.role / platform_role_permissions.role value may hold —
# see DEC-GRX-018 for why this is a plain CHECK-constrained column rather than a separate
# platform_roles table + many-to-many join.
PLATFORM_ROLES = (
    "platform.owner",
    "platform.admin",
    "platform.support",
    "platform.finance",
    "platform.operations",
)


class PlatformAdmin(Base):
    """IITDEVELOPER staff identity -- structurally separate from `users`/`accounts`
    (GRX-SAAS-002 Phase B). No account_id: a platform admin is not scoped to, and does
    not belong to, any customer account."""

    __tablename__ = "platform_admins"
    __table_args__ = (
        CheckConstraint(f"role IN {PLATFORM_ROLES!r}", name="ck_platform_admins_role"),
        CheckConstraint("status IN ('ACTIVE', 'DISABLED')", name="ck_platform_admins_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="ACTIVE")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PlatformPermission(Base):
    """Granular `platform.*`-namespaced permission codes -- structurally parallel to
    `permissions`, but only ever checked by `require_platform_permission()`, never
    `require_permission()`."""

    __tablename__ = "platform_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlatformRolePermission(Base):
    """Role -> permission mapping, keyed by the `role` value directly (not a `role_id`
    FK) since `platform_admins.role` is a plain column, not a row in a separate roles
    table -- see DEC-GRX-018."""

    __tablename__ = "platform_role_permissions"
    __table_args__ = (
        CheckConstraint(f"role IN {PLATFORM_ROLES!r}", name="ck_platform_role_permissions_role"),
    )

    role: Mapped[str] = mapped_column(Text, primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform_permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
