"""Celery application configuration."""
from __future__ import annotations

from celery import Celery
from opengovpension.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "opengovpension",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.task_soft_time_limit = settings.celery_task_soft_time_limit
celery_app.conf.task_time_limit = settings.celery_task_hard_time_limit


@celery_app.task(name="sample.add")
def add(a: int, b: int) -> int:  # pragma: no cover simple demo
    return a + b
"""Celery application configuration."""
from __future__ import annotations
from celery import Celery
from opengovpension.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    'opengovpension',
    broker=settings.redis_url if hasattr(settings, 'redis_url') else 'redis://localhost:6379/0',
    backend=settings.redis_url if hasattr(settings, 'redis_url') else 'redis://localhost:6379/0'
)

@celery_app.task
def sample_heavy_compute(x: int, y: int) -> int:
    return x * y
