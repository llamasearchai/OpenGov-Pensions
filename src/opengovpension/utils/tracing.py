"""OpenTelemetry tracing initialization for FastAPI."""
from __future__ import annotations
from opengovpension.core.config import get_settings

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

_tracing_initialized = False

def init_tracing():  # pragma: no cover network export optional
    global _tracing_initialized
    if _tracing_initialized:
        return
    settings = get_settings()
    resource = Resource.create({
        "service.name": settings.app_name,
        "service.version": settings.version,
    })
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint if hasattr(settings, 'otel_exporter_otlp_endpoint') else 'http://localhost:4318')
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _tracing_initialized = True
