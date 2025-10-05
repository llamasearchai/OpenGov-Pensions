"""User repository."""
from __future__ import annotations

from typing import Sequence
from sqlalchemy import select

from opengovpension.models.domain import User, Role, UserRole
from .base import BaseRepository


class UserRepository(BaseRepository):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str, is_superuser: bool = False) -> User:
        user = User(email=email, hashed_password=hashed_password, is_superuser=is_superuser)
        self.session.add(user)
        await self.session.flush()
        return user

    async def add_role(self, user: User, role: Role) -> None:
        if role not in user.roles:
            user.roles.append(role)
            await self.session.flush()

    async def remove_role(self, user: User, role: Role) -> None:
        if role in user.roles:
            user.roles.remove(role)
            await self.session.flush()
