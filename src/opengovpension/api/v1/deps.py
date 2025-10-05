"""Common dependencies for API v1."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from opengovpension.db.session import get_async_session
from opengovpension.repositories.user_repository import UserRepository
from opengovpension.repositories.role_repository import RoleRepository
from opengovpension.security.auth import decode_token

auth_scheme = HTTPBearer(auto_error=False)


async def get_db(session: AsyncSession = Depends(get_async_session)) -> AsyncSession:  # pragma: no cover simple wrapper
    return session


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
    session: AsyncSession = Depends(get_db),
):
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    repo = UserRepository(session)
    user = await repo.get(payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


def require_roles(*roles: str):
    async def checker(user=Depends(get_current_user)):
        user_roles = {r.name for r in user.roles}
        if not user_roles.intersection(roles):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker

"""Common dependencies for API v1."""
from __future__ import annotations
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from opengovpension.db.session import get_session
from opengovpension.repositories.user_repository import UserRepository
from opengovpension.repositories.role_repository import RoleRepository
from opengovpension.repositories.apikey_repository import APIKeyRepository
from opengovpension.security.auth import decode_token, TokenError
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
from fastapi import Header

async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        repo = UserRepository(session)
        user = await repo.get_by_id(sub)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except TokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_roles(*roles: str):
    async def checker(user=Depends(get_current_user)):
        user_role_names = {r.name for r in getattr(user, 'roles', [])}
        if not set(roles).issubset(user_role_names):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker

async def get_api_key(x_api_key: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    repo = APIKeyRepository(session)
    key_obj = await repo.get_by_key(x_api_key)
    if not key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key_obj
