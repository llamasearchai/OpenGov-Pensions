# Architecture Overview

## Layers
- API (FastAPI routers in `opengovpension.api.v1`)
- Service / Domain (currently light, expansion planned)
- Repositories (async SQLAlchemy access)
- Database (SQLAlchemy async engine + Alembic)
- Security (JWT auth, rate limiting, security headers)
- Observability (metrics, logging, tracing)

## Data Flow
Client -> FastAPI Router -> Dependencies (auth/session) -> Repository -> DB

## Key Decisions
- Async SQLAlchemy 2.x for scalability
- JWT bearer tokens with refresh rotation
- Prometheus metrics for standard ops visibility
- OpenTelemetry for distributed tracing

See ADRs in `docs/adr` for rationale.
