"""Authentication endpoints (deduplicated and hardened)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from opengovpension.api.v1.deps import get_db, get_current_user, require_roles
from opengovpension.repositories.user_repository import UserRepository
from opengovpension.repositories.role_repository import RoleRepository
from opengovpension.repositories.token_repository import RefreshTokenRepository
from opengovpension.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from opengovpension.utils.audit import audit
from opengovpension.core.config import get_settings
from opengovpension.security.middleware import limiter

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201, response_model=TokenResponse)
@limiter.limit("3/hour")  # Prevent mass account creation attempts
async def register(data: RegisterRequest, session: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(session)
    role_repo = RoleRepository(session)
    existing = await user_repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    is_first_user = False
    first_user = await session.execute("SELECT 1 FROM user LIMIT 1")
    if first_user.first() is None:
        is_first_user = True

    user = await user_repo.create(
        email=data.email,
        hashed_password=hash_password(data.password),
        is_superuser=is_first_user,
    )
    if is_first_user:
        admin_role = await role_repo.get_or_create("admin", "Administrator role")
        await user_repo.add_role(user, admin_role)

    access = create_access_token(user.id, {"roles": [r.name for r in user.roles]})
    refresh = create_refresh_token(user.id)
    rt_repo = RefreshTokenRepository(session)
    await rt_repo.create(
        refresh,
        user.id,
        datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes),
    )
    await audit(session, "user.register", "user", user.id, user.id, {"email": user.email})
    await session.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Basic brute force protection
async def login(data: LoginRequest, session: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access = create_access_token(user.id, {"roles": [r.name for r in user.roles]})
    refresh = create_refresh_token(user.id)
    rt_repo = RefreshTokenRepository(session)
    await rt_repo.create(
        refresh,
        user.id,
        datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes),
    )
    await audit(session, "user.login", "user", user.id, user.id, {"email": user.email})
    await session.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")  # Limit refresh churn
async def refresh_token(data: RefreshRequest, session: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token") from None
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_repo = UserRepository(session)
    user = await user_repo.get(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access = create_access_token(user.id, {"roles": [r.name for r in user.roles]})
    new_refresh = create_refresh_token(user.id)
    rt_repo = RefreshTokenRepository(session)
    await rt_repo.create(
        new_refresh,
        user.id,
        datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes),
    )
    await audit(session, "token.refresh", "user", user.id, user.id, None)
    await session.commit()
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "roles": [r.name for r in user.roles]}


class RoleAssignRequest(BaseModel):
    email: EmailStr
    role: str


@router.post("/roles/assign")
@limiter.limit("20/minute")
async def assign_role(
    req: RoleAssignRequest,
    session: AsyncSession = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    user_repo = UserRepository(session)
    role_repo = RoleRepository(session)
    user = await user_repo.get_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = await role_repo.get_or_create(req.role)
    await user_repo.add_role(user, role)
    await audit(session, "role.assign", "user", user.id, user.id, {"role": req.role})
    await session.commit()
    return {"id": user.id, "roles": [r.name for r in user.roles]}
