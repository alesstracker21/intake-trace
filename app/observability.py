from __future__ import annotations

import os
import uuid
from typing import Final

# ADK's legacy span attributes capture message content by default. These must be
# set before ADK is imported anywhere in the process.
os.environ.setdefault("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "false")
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "")

from opentelemetry import trace  # noqa: E402
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # noqa: E402
from opentelemetry.sdk.resources import Resource  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: E402

from app import __version__  # noqa: E402
from app.config import Settings  # noqa: E402


TRACER_NAME: Final = "intake_trace.pipeline"
_provider: TracerProvider | None = None


def configure_telemetry(settings: Settings) -> TracerProvider:
    """Install one SDK provider; exporting remains opt-in."""

    global _provider
    if _provider is not None:
        return _provider

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": settings.otel_service_name,
                "service.version": __version__,
                "deployment.environment.name": settings.app_env,
                "service.namespace": "intake-trace",
            }
        )
    )
    if settings.otel_enabled:
        exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint, timeout=5)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _provider = provider
    return provider


def shutdown_telemetry() -> None:
    if _provider is not None:
        _provider.force_flush(timeout_millis=5000)
        _provider.shutdown()


def current_trace_id() -> str:
    context = trace.get_current_span().get_span_context()
    return f"{context.trace_id:032x}" if context.is_valid else uuid.uuid4().hex


def get_tracer():
    return trace.get_tracer(TRACER_NAME, __version__)
