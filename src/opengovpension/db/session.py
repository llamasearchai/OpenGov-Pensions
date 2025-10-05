"""Async database session and engine configuration."""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from opengovpension.core.config import get_settings

settings = get_settings()

# Use NullPool for SQLite to avoid locking issues; otherwise configure pool.
engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    poolclass=NullPool if settings.database_url.startswith("sqlite") else None,  # type: ignore[arg-type]
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover - simple dependency
    async with AsyncSessionLocal() as session:  # noqa: SIM117
        yield session
