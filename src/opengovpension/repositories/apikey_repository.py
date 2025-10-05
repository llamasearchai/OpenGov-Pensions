"""API Key repository."""
from __future__ import annotations

import secrets
from sqlalchemy import select, update
from opengovpension.models.orm import APIKey
from .base import BaseRepository


class APIKeyRepository(BaseRepository):
    model = APIKey

    @staticmethod
    def generate_key() -> str:
        return secrets.token_hex(32)

    async def create(self, user_id: str, name: str) -> APIKey:
        key_value = self.generate_key()
        api_key = APIKey(user_id=user_id, name=name, key=key_value)
        self.session.add(api_key)
        await self.session.flush()
        return api_key

    async def get_by_key(self, key: str) -> APIKey | None:
        stmt = select(APIKey).where(APIKey.key == key, APIKey.revoked.is_(False))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke(self, key: str) -> None:
        stmt = update(APIKey).where(APIKey.key == key).values(revoked=True)
        await self.session.execute(stmt)
"""API Key repository."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from opengovpension.models.domain import APIKey
from typing import Optional

class APIKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_key(self, key: str) -> Optional[APIKey]:
        res = await self.session.execute(select(APIKey).where(APIKey.key == key, APIKey.active == True))  # noqa: E712
        return res.scalar_one_or_none()
