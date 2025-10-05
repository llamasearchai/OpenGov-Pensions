"""Redis caching utilities."""
from __future__ import annotations
import asyncio
import json
from typing import Any, Callable, Awaitable
import aioredis  # type: ignore
from opengovpension.core.config import get_settings

_settings = get_settings()
_redis = None

async def get_redis():  # pragma: no cover simple connection
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(getattr(_settings, 'redis_url', 'redis://localhost:6379/0'))
    return _redis

async def cache_get(key: str):
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None

async def cache_set(key: str, value: Any, ttl: int = 60):
    r = await get_redis()
    await r.set(key, json.dumps(value), ex=ttl)
