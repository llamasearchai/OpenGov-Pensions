"""FastAPI web application for OpenPension."""

from contextlib import asynccontextmanager
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.database import DatabaseManager
from ..services.agent_service import AgentService
from ..storage.item_storage import ItemStorage
from opengovpension.security.middleware import RequestIDMiddleware, SecurityHeadersMiddleware, rate_limit_exception_handler, limiter
from opengovpension.api.v1 import auth as auth_router
from opengovpension.api.v1 import items as items_router
from opengovpension.api.v1 import apikeys as apikeys_router
from opengovpension.utils.observability import (
    router as metrics_router,
    configure_logging,
    MetricsLoggingMiddleware,
)
from opengovpension.utils.tracing import init_tracing
from opengovpension.utils.health import router as health_router
from opengovpension.core.celery_app import celery_app
from celery.result import AsyncResult


# Pydantic models
class ItemCreate(BaseModel):
    name: str
    description: str

class Item(ItemCreate):
    id: str
    created_at: str
    updated_at: str

class AnalysisRequest(BaseModel):
    prompt: str
    model: str = "ollama"

class AnalysisResponse(BaseModel):
    result: dict
    provider: str
    model: str


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"Starting OpenPension FastAPI application...")
    init_tracing()
    yield
    # Shutdown
    print(f"Shutting down OpenPension FastAPI application...")

configure_logging()
app = FastAPI(
    title="OpenPension API",
    description="Domain-specific API for pension management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsLoggingMiddleware)  # metrics & structured access logs
app.state.limiter = limiter
from slowapi.middleware import SlowAPIMiddleware  # type: ignore
app.add_middleware(SlowAPIMiddleware)
from slowapi.errors import RateLimitExceeded  # type: ignore
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

# Include new routers
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(items_router.router, prefix="/api/v1")
app.include_router(apikeys_router.router, prefix="/api/v1")
app.include_router(metrics_router)
app.include_router(health_router)

active_connections: set[WebSocket] = set()

@app.websocket("/ws/notifications")
async def websocket_notifications(ws: WebSocket):  # pragma: no cover simple IO
    await ws.accept()
    active_connections.add(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive / ignore content
    except WebSocketDisconnect:
        active_connections.discard(ws)

# Dependencies
def get_db_manager():
    return DatabaseManager()

def get_item_storage():
    return ItemStorage()

def get_agent_service():
    return AgentService()


# Routes

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "OpenPension",
        "version": "1.0.0",
        "description": "Domain-specific API for pension management",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "OpenPension",
        "version": "1.0.0"
    }

@app.post("/api/tasks/add")
async def trigger_add(a: int, b: int):
    task = celery_app.send_task("sample.add", args=[a, b])
    return {"task_id": task.id, "status": "queued"}

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": res.status, "result": res.result if res.successful() else None}

## Legacy item endpoints removed in favor of versioned /api/v1/items router.

@app.post("/api/analysis", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Run AI analysis on given prompt."""
    try:
        import asyncio
        result = await agent_service.run_analysis(
            request.prompt,
            model=request.model
        )
        return AnalysisResponse(
            result=result,
            provider=result.get("provider", "unknown"),
            model=result.get("model", request.model)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get database and system statistics."""
    try:
        # This would need to be implemented based on specific domain
        return {
            "service": "OpenPension",
            "version": "1.0.0",
            "items_count": 0,
            "last_updated": "2024-01-15T10:00:00"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Development server
if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "opengovpension.web.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info"
    )