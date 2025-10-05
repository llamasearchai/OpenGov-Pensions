"""Reusable ORM mixins."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func, Integer
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Soft delete support via deleted_at timestamp."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VersionedMixin:
    """Optimistic locking using a version integer."""

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
