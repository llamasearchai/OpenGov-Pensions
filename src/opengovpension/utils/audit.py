"""Audit logging helper."""
from __future__ import annotations

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from opengovpension.models.orm import AuditLog


async def audit(
    session: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str | None,
    actor_id: str | None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        details=str(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(log)
    # flush at caller discretion
