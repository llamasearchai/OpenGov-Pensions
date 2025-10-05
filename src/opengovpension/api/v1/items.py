"""Item endpoints (protected, cached, rate limited)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from opengovpension.api.v1.deps import get_db, get_current_user, require_roles
from opengovpension.repositories.item_repository import ItemRepository
from opengovpension.utils.audit import audit
from opengovpension.utils.cache import cache_get, cache_set, cache_invalidate
from opengovpension.security.middleware import limiter
from opengovpension.web.app import active_connections  # circular import acceptable

router = APIRouter(prefix="/items", tags=["items"])


class ItemCreate(BaseModel):
    name: str
    description: str | None = None


class ItemOut(BaseModel):
    id: str
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


@router.get('/', response_model=list[ItemOut])
@limiter.limit("60/minute")
async def list_items(skip: int = 0, limit: int = Query(50, le=100), search: str | None = None, session: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    cache_key = f"items:{skip}:{limit}:{search or ''}:{user.id}"
    cached = await cache_get(cache_key)
    if cached:
        return [ItemOut(**c) for c in cached]
    repo = ItemRepository(session)
    items = await repo.list(skip=skip, limit=limit, search=search)
    serial = [ItemOut.model_validate(i).model_dump() for i in items]
    await cache_set(cache_key, serial, ttl=30)
    return serial


@router.post('/', response_model=ItemOut, status_code=201, dependencies=[Depends(require_roles("admin"))])
@limiter.limit("30/minute")
async def create_item(data: ItemCreate, session: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    repo = ItemRepository(session)
    item = await repo.create(data.name, data.description, user.id)
    await audit(session, "item.create", "item", item.id, user.id, {"name": item.name})
    await session.commit()
    await cache_invalidate("items:")
    # Broadcast (best effort)
    for ws in list(active_connections):  # pragma: no cover
        try:
            await ws.send_json({"event": "item_created", "id": item.id, "name": item.name})
        except Exception:
            pass
    return ItemOut.model_validate(item)


@router.get('/{item_id}', response_model=ItemOut)
async def get_item(item_id: str, session: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    repo = ItemRepository(session)
    item = await repo.get(item_id)
    if not item or item.deleted_at is not None:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemOut.model_validate(item)


@router.delete('/{item_id}', dependencies=[Depends(require_roles("admin"))])
async def delete_item(item_id: str, session: AsyncSession = Depends(get_db)):
    repo = ItemRepository(session)
    item = await repo.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await repo.soft_delete(item_id)
    await audit(session, "item.delete", "item", item_id, None, None)
    await session.commit()
    await cache_invalidate("items:")
    return {"status": "deleted"}
