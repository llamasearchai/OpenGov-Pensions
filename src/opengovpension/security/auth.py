"""Authentication and token utilities."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt, JWTError
from passlib.context import CryptContext

from opengovpension.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str, additional_claims: Dict[str, Any] | None = None) -> str:
    to_encode: Dict[str, Any] = {"sub": subject, "type": "access"}
    if additional_claims:
        to_encode.update(additional_claims)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes)
    to_encode: Dict[str, Any] = {"sub": subject, "type": "refresh", "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:  # pragma: no cover simple error path
        raise ValueError("Invalid token") from e
