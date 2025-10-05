"""Audit logging utilities."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from opengovpension.models.domain import AuditLog
from datetime import datetime
from uuid import uuid4

async def audit(session: AsyncSession, *, entity: str, entity_id: str, action: str, actor_id: str | None):
    log = AuditLog(id=str(uuid4()), entity=entity, entity_id=entity_id, action=action, actor_id=actor_id)
    session.add(log)
    await session.flush()
