"""Users, RBAC, refresh tokens and OTP/verification codes."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    str_enum,
)
from app.models.enums import OtpChannel, OtpPurpose, UserStatus, UserType

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("assigned_by_id", ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Case-insensitive uniqueness among non-deleted users.
        Index(
            "uq_users_email_lower", func.lower(text("email")), unique=True, postgresql_where=text("deleted_at IS NULL")
        ),
        Index(
            "uq_users_mobile", "mobile", unique=True, postgresql_where=text("mobile IS NOT NULL AND deleted_at IS NULL")
        ),
        CheckConstraint("mobile IS NULL OR mobile ~ '^\\+91[6-9][0-9]{9}$'", name="mobile_e164_in"),
    )

    email: Mapped[str] = mapped_column(String(255))
    mobile: Mapped[str | None] = mapped_column(String(15))  # +91XXXXXXXXXX
    password_hash: Mapped[str | None] = mapped_column(String(255))  # null for OTP-only accounts
    user_type: Mapped[UserType] = mapped_column(str_enum(UserType), index=True)
    status: Mapped[UserStatus] = mapped_column(
        str_enum(UserStatus), default=UserStatus.PENDING_VERIFICATION, index=True
    )
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    is_mobile_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    locked_until: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]
    password_changed_at: Mapped[datetime | None]

    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles,
        primaryjoin="User.id == user_roles.c.user_id",
        secondaryjoin="Role.id == user_roles.c.role_id",
        lazy="selectin",
    )
    staff_profile: Mapped[StaffProfile | None] = relationship(back_populates="user", uselist=False)


class StaffProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Admin/pharmacy staff details. Pharmacists must carry a registration number
    (State Pharmacy Council) before they can be granted prescription approval."""

    __tablename__ = "staff_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150))
    designation: Mapped[str | None] = mapped_column(String(100))
    pharmacist_registration_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    pharmacist_registration_state: Mapped[str | None] = mapped_column(String(60))
    pharmacist_registration_valid_until: Mapped[datetime | None]

    user: Mapped[User] = relationship(back_populates="staff_profile")


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    slug: Mapped[str] = mapped_column(String(50), unique=True)  # e.g. "pharmacist"
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    permissions: Mapped[list[Permission]] = relationship(secondary=role_permissions, lazy="selectin")


class Permission(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True)  # e.g. "prescriptions:approve"
    module: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(String(255))


class RefreshToken(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Opaque rotating refresh tokens. Only a SHA-256 hash is stored.

    `family_id` groups a rotation chain; reuse of a revoked token revokes the
    whole family (token-theft detection).
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    family_id: Mapped[uuid.UUID] = mapped_column(index=True)
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("refresh_tokens.id", ondelete="SET NULL"))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(INET)


class OtpVerification(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One-time codes and verification/reset tokens (hashed, never logged)."""

    __tablename__ = "otp_verifications"
    __table_args__ = (
        Index("ix_otp_verifications_lookup", "target", "purpose", "consumed_at"),
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target: Mapped[str] = mapped_column(String(255))  # mobile number or email
    channel: Mapped[OtpChannel] = mapped_column(str_enum(OtpChannel))
    purpose: Mapped[OtpPurpose] = mapped_column(str_enum(OtpPurpose))
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime]
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    consumed_at: Mapped[datetime | None]
    ip_address: Mapped[str | None] = mapped_column(INET)


__all__ = [
    "OtpVerification",
    "Permission",
    "RefreshToken",
    "Role",
    "StaffProfile",
    "User",
    "role_permissions",
    "user_roles",
]
