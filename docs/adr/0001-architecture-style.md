# ADR 0001: Adopt Clean Layered Architecture with Async SQLAlchemy

Date: 2025-09-20

## Status
Accepted

## Context
Need a scalable, testable foundation supporting async operations, security, and observability.

## Decision
Use layered approach (API -> Repos -> DB) with Pydantic for validation, async SQLAlchemy + Alembic for persistence, structlog + Prometheus + OTEL for observability.

## Consequences
+ Clear separation of concerns
+ Easier future domain expansion
- Additional boilerplate
