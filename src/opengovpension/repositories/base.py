"""Base repository with shared helpers."""
from __future__ import annotations

from typing import Any, Sequence
from sqlalchemy import select, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    model = None  # override

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id_: Any):  # noqa: D401
        stmt = select(self.model).where(self.model.id == id_)  # type: ignore[attr-defined]
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[Any]:
        if hasattr(self.model, "deleted_at"):
            stmt = (
                select(self.model)
                .where(or_(self.model.deleted_at.is_(None)))  # type: ignore[attr-defined]
                .offset(offset)
                .limit(limit)
            )
        else:
            stmt = select(self.model).offset(offset).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def soft_delete(self, id_: Any) -> bool:
        if not hasattr(self.model, "deleted_at"):
            return False
        stmt = (
            update(self.model)
            .where(self.model.id == id_)  # type: ignore[attr-defined]
            .values(deleted_at=func.now())
        )
        await self.session.execute(stmt)
        return True
