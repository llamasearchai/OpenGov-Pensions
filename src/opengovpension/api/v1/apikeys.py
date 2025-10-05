"""API key management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from opengovpension.api.v1.deps import get_db, get_current_user, require_roles
from opengovpension.repositories.apikey_repository import APIKeyRepository

router = APIRouter(prefix="/keys", tags=["api-keys"]) 


class APIKeyCreate(BaseModel):
    name: str


@router.post("/", dependencies=[Depends(require_roles("admin"))])
async def create_key(payload: APIKeyCreate, session: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    repo = APIKeyRepository(session)
    key = await repo.create(user_id=user.id, name=payload.name)
    await session.commit()
    return {"id": key.id, "key": key.key, "name": key.name}


@router.post("/{key}/revoke", dependencies=[Depends(require_roles("admin"))])
async def revoke_key(key: str, session: AsyncSession = Depends(get_db)):
    repo = APIKeyRepository(session)
    await repo.revoke(key)
    await session.commit()
    return {"status": "revoked"}


async def api_key_auth(x_api_key: str | None = Header(default=None, alias="X-API-Key"), session: AsyncSession = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    repo = APIKeyRepository(session)
    key = await repo.get_by_key(x_api_key)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key
