"""Observability setup: logging, metrics, tracing instrumentation helpers.

Provides:
 - Prometheus counters/histograms
 - Instrumentation middleware for request timing & structured access logs
 - Logging configuration (structlog JSON)
"""
from __future__ import annotations

import time
import logging
from typing import Callable

import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response, Request
from starlette.middleware.base import BaseHTTPMiddleware

from opengovpension.core.config import get_settings

REQUEST_COUNT = Counter(
    'opengov_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'opengov_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

settings = get_settings()

router = APIRouter(tags=["metrics"])

@router.get('/metrics')
async def metrics():  # pragma: no cover - simple exposition
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def configure_logging():  # pragma: no cover - formatting / side effects only
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


class MetricsLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to record Prometheus metrics and structured access logs.

    Excludes the /metrics endpoint from metrics collection to avoid recursion.
    """

    def __init__(self, app):  # type: ignore[override]
        super().__init__(app)
        self.logger = structlog.get_logger("access")

    async def dispatch(self, request: Request, call_next: Callable):  # type: ignore[override]
        path = request.url.path
        if path == '/metrics':  # don't self-instrument
            return await call_next(request)
        start = time.time()
        try:
            response = await call_next(request)
        except Exception as exc:  # capture exceptions as 500s
            duration = time.time() - start
            REQUEST_COUNT.labels(request.method, path, 500).inc()
            REQUEST_LATENCY.labels(path).observe(duration)
            self.logger.error(
                "request.error",
                method=request.method,
                path=path,
                status=500,
                duration_ms=round(duration * 1000, 2),
                error=str(exc),
            )
            raise
        duration = time.time() - start
        status_code = response.status_code
        REQUEST_COUNT.labels(request.method, path, status_code).inc()
        REQUEST_LATENCY.labels(path).observe(duration)
        request_id = getattr(request.state, 'request_id', None)
        self.logger.info(
            "request.access",
            method=request.method,
            path=path,
            status=status_code,
            duration_ms=round(duration * 1000, 2),
            request_id=request_id,
        )
        return response
