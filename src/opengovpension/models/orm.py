"""SQLAlchemy ORM models for OpenPension domain."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    DateTime,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opengovpension.db.base import Base
from opengovpension.db.mixins import TimestampMixin, SoftDeleteMixin, VersionedMixin


def _uuid() -> str:
    return str(uuid4())


class User(Base, TimestampMixin, SoftDeleteMixin, VersionedMixin):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=lambda: UserRole.__table__,
        back_populates="users",
        lazy="joined",
    )
    api_keys: Mapped[list[APIKey]] = relationship("APIKey", back_populates="user")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user")


class Role(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list[User]] = relationship(
        "User",
        secondary=lambda: UserRole.__table__,
        back_populates="roles",
    )


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_role"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id", ondelete="CASCADE"), index=True)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)


class Item(Base, TimestampMixin, SoftDeleteMixin, VersionedMixin):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text())
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    owner: Mapped[User | None] = relationship("User")


class RefreshToken(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")


class APIKey(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="api_keys")


class AuditLog(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[str | None] = mapped_column(Text())
