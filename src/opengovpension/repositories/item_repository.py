"""Item repository (async) providing CRUD and search with soft delete filtering."""
from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from opengovpension.models.orm import Item
from .base import BaseRepository


class ItemRepository(BaseRepository):
    model = Item

    async def create(self, name: str, description: str | None, owner_id: str | None) -> Item:
        item = Item(name=name, description=description, owner_id=owner_id)
        self.session.add(item)
        await self.session.flush()
        return item

    async def list(self, skip: int = 0, limit: int = 50, search: str | None = None) -> Sequence[Item]:
        stmt = select(Item).where(Item.deleted_at.is_(None)).offset(skip).limit(limit)
        if search:
            stmt = stmt.where(Item.name.ilike(f"%{search}%"))
        res = await self.session.execute(stmt)
        return res.scalars().all()
