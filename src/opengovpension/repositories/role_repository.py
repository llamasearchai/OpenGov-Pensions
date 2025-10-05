"""Role repository."""
from __future__ import annotations

from sqlalchemy import select
from opengovpension.models.orm import Role
from .base import BaseRepository


class RoleRepository(BaseRepository):
    model = Role

    async def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_or_create(self, name: str, description: str | None = None) -> Role:
        role = await self.get_by_name(name)
        if role:
            return role
        role = Role(name=name, description=description)
        self.session.add(role)
        await self.session.flush()
        return role
"""Role repository."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from opengovpension.models.domain import Role
from typing import Optional, Sequence

class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(self, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.flush()
        return role

    async def list(self) -> Sequence[Role]:
        res = await self.session.execute(select(Role))
        return res.scalars().all()
