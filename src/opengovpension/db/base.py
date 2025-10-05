"""Declarative Base and common SQLAlchemy metadata for OpenPension."""

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class with automatic __tablename__ generation."""

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore[override]
        return cls.__name__.lower()
