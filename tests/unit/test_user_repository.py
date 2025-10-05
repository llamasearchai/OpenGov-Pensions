import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from opengovpension.db.session import AsyncSessionLocal, engine
from opengovpension.models.domain import Base, User
from opengovpension.repositories.user_repository import UserRepository
from opengovpension.security.auth import hash_password

@pytest.mark.asyncio
async def test_user_repository_crud():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:  # type: ignore
        repo = UserRepository(session)
        user = User(email="test@example.com", hashed_password=hash_password("pass"))
        await repo.create(email="test@example.com", hashed_password=hash_password("pass"))
        fetched = await repo.get_by_email("test@example.com")
        assert fetched is not None
        assert fetched.email == "test@example.com"
