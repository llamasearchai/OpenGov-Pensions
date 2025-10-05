"""Refresh token repository."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import select, update
from opengovpension.models.orm import RefreshToken
from .base import BaseRepository


class RefreshTokenRepository(BaseRepository):
    model = RefreshToken

    async def create(self, token: str, user_id: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
        self.session.add(rt)
        await self.session.flush()
        return rt

    async def get_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke(self, token: str) -> None:
        stmt = update(RefreshToken).where(RefreshToken.token == token).values(revoked=True)
        await self.session.execute(stmt)
