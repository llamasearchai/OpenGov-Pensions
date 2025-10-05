"""Custom FastAPI middlewares for request ID, rate limiting, and security headers.

Enhancements:
 - Rate limiter now configurable via application settings (requests/minute)
 - Comprehensive security headers (HSTS, CSP, Referrer-Policy, Permissions-Policy, COEP/COOP/CORP)
 - Removed deprecated X-XSS-Protection header
 - Unified 429 JSON format including request ID (if available)
"""
from __future__ import annotations

import time
import uuid
from typing import Callable, Iterable

from fastapi import Request as FastAPIRequest
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from opengovpension.core.config import get_settings

_settings = get_settings()

# Default / global limiter; per-endpoint limits can still override via decorator.
_default_limit = f"{_settings.rate_limit_per_minute}/minute"
limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,
    default_limits=[_default_limit],
)

def rate_limit_exception_handler(request: FastAPIRequest, exc: RateLimitExceeded):  # pragma: no cover - thin wrapper
    # Try to surface a request ID if it has been set by earlier middleware.
    request_id = request.headers.get("X-Request-ID") or request.state.__dict__.get("request_id") if hasattr(request, "state") else None
    payload = {
        "detail": "Rate limit exceeded",
        "error": str(exc),
    }
    if request_id:
        payload["request_id"] = request_id
    return JSONResponse(status_code=429, content=payload)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add a hardened set of security & privacy-related headers.

    Notes:
      * HSTS enabled only when environment is not local and debug is False.
      * CSP kept intentionally strict/minimal; expand when adding external origins.
    """

    def __init__(self, app, csp: str | None = None):  # type: ignore[override]
        super().__init__(app)
        # Build a default CSP if one not supplied.
        self.csp = csp or (
            "default-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "img-src 'self' data:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "  # inline styles sometimes needed for docs; revisit to tighten.
            "connect-src 'self'"
        )

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]):  # type: ignore[override]
        response: Response = await call_next(request)
        # Core protections
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = self.csp
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        # Cross-origin isolation / embedding controls
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Embedding-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        # Cache control for dynamic API responses
        response.headers.setdefault('Cache-Control', 'no-store')
        # Strict Transport Security (only in non-local + not debug)
        if _settings.environment not in {"local", "dev"} and not _settings.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID and timing header to each response."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]):  # type: ignore[override]
        request_id = str(uuid.uuid4())
        # Expose the ID on request.state so downstream code can reference it (e.g., logging).
        request.state.request_id = request_id  # type: ignore[attr-defined]
        start = time.time()
        response: Response = await call_next(request)
        duration = (time.time() - start) * 1000
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Process-Time-ms'] = f"{duration:.2f}"
        return response
