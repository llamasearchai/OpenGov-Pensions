"""Alembic environment configuration (async)."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from opengovpension.core.config import get_settings
from opengovpension.db.base import Base
from opengovpension.models import orm  # noqa: F401 ensure model import

config = context.config
settings = get_settings()

# Override URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:  # pragma: no cover
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():  # pragma: no cover - offline rarely used in tests
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:  # type: ignore[arg-type]
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():  # pragma: no cover
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
from __future__ import annotations
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy import engine_from_config
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
import os
import sys

# Add src to path
sys.path.append(os.path.abspath("."))
from opengovpension.core.config import get_settings  # noqa
from opengovpension.db.base import Base  # noqa

config = context.config
fileConfig(config.config_file_name)  # type: ignore[arg-type]

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata

async def run_migrations_online() -> None:
    connectable = AsyncEngine(engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    ))

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async():
    await run_migrations_online()

if context.is_offline_mode():
    raise SystemExit("Offline mode not configured for async migrations")
else:
    asyncio.run(run_async())
