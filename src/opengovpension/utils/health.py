"""Health check utilities for OpenPension application.

This module provides comprehensive health checking capabilities including
liveness, readiness, and startup probes for production deployments.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from contextlib import asynccontextmanager

import structlog
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import DatabaseManager
from ..utils.cache import get_cache
from ..utils.circuit_breaker import get_all_circuit_breaker_stats

logger = structlog.get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/health", tags=["health"])


class HealthCheck(Protocol):
    """Protocol for health check implementations."""

    async def check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        ...


@dataclass
class HealthStatus:
    """Health status information."""
    name: str
    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    response_time_ms: float = 0.0


@dataclass
class HealthReport:
    """Comprehensive health report."""
    overall_status: str  # "healthy", "unhealthy", "degraded"
    timestamp: float = field(default_factory=time.time)
    checks: List[HealthStatus] = field(default_factory=list)
    version: str = "1.0.0"


class DatabaseHealthCheck:
    """Database connectivity health check."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        start_time = time.time()
        try:
            # Try to get a session and execute a simple query
            async with self.db_manager.session() as session:
                result = await session.execute("SELECT 1 as health_check")
                row = result.fetchone()

                if row and row[0] == 1:
                    response_time = (time.time() - start_time) * 1000
                    return {
                        "status": "healthy",
                        "message": "Database connection successful",
                        "response_time_ms": response_time
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": "Database query returned unexpected result"
                    }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "response_time_ms": response_time
            }


class RedisHealthCheck:
    """Redis connectivity health check."""

    def __init__(self, cache_client):
        self.cache_client = cache_client

    async def check(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        start_time = time.time()
        try:
            # Simple ping/pong test
            await self.cache_client.ping()
            response_time = (time.time() - start_time) * 1000
            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "response_time_ms": response_time
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "response_time_ms": response_time
            }


class ExternalServiceHealthCheck:
    """External service health check using circuit breaker stats."""

    def __init__(self, service_name: str):
        self.service_name = service_name

    async def check(self) -> Dict[str, Any]:
        """Check external service health via circuit breaker."""
        try:
            stats = get_all_circuit_breaker_stats()
            service_stats = stats.get(self.service_name)

            if not service_stats:
                return {
                    "status": "degraded",
                    "message": f"No circuit breaker stats available for {self.service_name}"
                }

            state = service_stats.get("state")
            consecutive_failures = service_stats.get("stats", {}).get("consecutive_failures", 0)

            if state == "open":
                return {
                    "status": "unhealthy",
                    "message": f"{self.service_name} circuit breaker is open"
                }
            elif state == "half_open":
                return {
                    "status": "degraded",
                    "message": f"{self.service_name} circuit breaker is half-open"
                }
            elif consecutive_failures > 0:
                return {
                    "status": "degraded",
                    "message": f"{self.service_name} has {consecutive_failures} consecutive failures"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"{self.service_name} is operating normally"
                }
        except Exception as e:
            logger.error(f"External service health check failed for {self.service_name}", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Failed to check {self.service_name} health: {str(e)}"
            }


class HealthChecker:
    """Main health checker orchestrator."""

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self._setup_default_checks()

    def _setup_default_checks(self):
        """Setup default health checks."""
        # These will be initialized when the app starts
        self.checks["database"] = None  # Will be set by dependency injection
        self.checks["redis"] = None     # Will be set by dependency injection
        self.checks["openai"] = ExternalServiceHealthCheck("openai")
        self.checks["ollama"] = ExternalServiceHealthCheck("ollama")

    def register_check(self, name: str, check: HealthCheck):
        """Register a custom health check."""
        self.checks[name] = check

    async def check_all(self) -> HealthReport:
        """Run all health checks and return comprehensive report."""
        report = HealthReport()
        overall_status = "healthy"
        degraded_checks = 0

        for name, check in self.checks.items():
            if check is None:
                # Skip uninitialized checks
                continue

            try:
                start_time = time.time()
                result = await check.check()
                response_time = (time.time() - start_time) * 1000

                status = result.get("status", "unhealthy")
                message = result.get("message", "Unknown status")

                health_status = HealthStatus(
                    name=name,
                    status=status,
                    message=message,
                    details=result,
                    response_time_ms=response_time
                )

                report.checks.append(health_status)

                if status == "unhealthy":
                    overall_status = "unhealthy"
                elif status == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
                    degraded_checks += 1

            except Exception as e:
                logger.error(f"Health check failed for {name}", error=str(e))
                health_status = HealthStatus(
                    name=name,
                    status="unhealthy",
                    message=f"Health check failed: {str(e)}"
                )
                report.checks.append(health_status)
                overall_status = "unhealthy"

        report.overall_status = overall_status
        return report

    async def check_liveness(self) -> HealthReport:
        """Liveness probe - checks if the application is running."""
        # For liveness, we only check basic application health
        # This should be lightweight and rarely fail
        return HealthReport(
            overall_status="healthy",
            checks=[
                HealthStatus(
                    name="application",
                    status="healthy",
                    message="Application is running"
                )
            ]
        )

    async def check_readiness(self) -> HealthReport:
        """Readiness probe - checks if the application is ready to serve traffic."""
        # For readiness, we check all critical dependencies
        return await self.check_all()

    async def check_startup(self) -> HealthReport:
        """Startup probe - checks if the application has started successfully."""
        # For startup, we check essential services only
        startup_checks = {
            "database": self.checks.get("database"),
            "redis": self.checks.get("redis")
        }

        report = HealthReport()
        overall_status = "healthy"

        for name, check in startup_checks.items():
            if check is None:
                continue

            try:
                result = await check.check()
                status = result.get("status", "unhealthy")

                health_status = HealthStatus(
                    name=name,
                    status=status,
                    message=result.get("message", "Unknown status"),
                    details=result
                )

                report.checks.append(health_status)

                if status == "unhealthy":
                    overall_status = "unhealthy"

            except Exception as e:
                logger.error(f"Startup health check failed for {name}", error=str(e))
                health_status = HealthStatus(
                    name=name,
                    status="unhealthy",
                    message=f"Startup check failed: {str(e)}"
                )
                report.checks.append(health_status)
                overall_status = "unhealthy"

        report.overall_status = overall_status
        return report


# Global health checker instance
health_checker = HealthChecker()


# FastAPI endpoints
@router.get("/", summary="Overall health status")
async def health_check():
    """Get overall health status of the application."""
    report = await health_checker.check_all()

    status_code = status.HTTP_200_OK
    if report.overall_status == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif report.overall_status == "degraded":
        status_code = status.HTTP_200_OK  # Still serve traffic but indicate issues

    return {
        "status": report.overall_status,
        "timestamp": report.timestamp,
        "version": report.version,
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "message": check.message,
                "response_time_ms": check.response_time_ms,
                "details": check.details
            }
            for check in report.checks
        ]
    }


@router.get("/liveness", summary="Liveness probe")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    report = await health_checker.check_liveness()

    return {
        "status": report.overall_status,
        "timestamp": report.timestamp,
        "checks": report.checks
    }


@router.get("/readiness", summary="Readiness probe")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    report = await health_checker.check_readiness()

    status_code = status.HTTP_200_OK
    if report.overall_status == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": report.overall_status,
        "timestamp": report.timestamp,
        "checks": report.checks
    }


@router.get("/startup", summary="Startup probe")
async def startup_check():
    """Kubernetes startup probe endpoint."""
    report = await health_checker.check_startup()

    status_code = status.HTTP_200_OK
    if report.overall_status == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": report.overall_status,
        "timestamp": report.timestamp,
        "checks": report.checks
    }


@router.get("/detailed", summary="Detailed health report")
async def detailed_health_check():
    """Get detailed health information including metrics."""
    report = await health_checker.check_all()

    # Add additional system information
    detailed_report = {
        "status": report.overall_status,
        "timestamp": report.timestamp,
        "version": report.version,
        "system": {
            "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
            "environment": settings.environment,
            "debug": settings.debug
        },
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "message": check.message,
                "response_time_ms": check.response_time_ms,
                "details": check.details,
                "timestamp": check.timestamp
            }
            for check in report.checks
        ]
    }

    return detailed_report


# Dependency injection helpers
def get_database_health_check() -> DatabaseHealthCheck:
    """Get database health check instance."""
    db_manager = DatabaseManager()
    return DatabaseHealthCheck(db_manager)


def get_redis_health_check() -> RedisHealthCheck:
    """Get Redis health check instance."""
    cache_client = get_cache()
    return RedisHealthCheck(cache_client)


# Initialize health checks when module is imported
async def initialize_health_checks():
    """Initialize health check dependencies."""
    try:
        health_checker.register_check("database", get_database_health_check())
        health_checker.register_check("redis", get_redis_health_check())
        logger.info("Health checks initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize health checks", error=str(e))
        raise