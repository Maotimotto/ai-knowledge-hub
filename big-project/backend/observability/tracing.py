"""
AI创作工坊 - OpenTelemetry Tracing

Configures distributed tracing with OpenTelemetry.
Creates spans for agent calls, LLM requests, and database queries.
"""

from contextlib import contextmanager
from typing import Any, Optional

from observability.logger import get_logger

logger = get_logger(__name__)

_tracer: Any = None


def setup_tracing(app: object) -> None:
    """
    Configure OpenTelemetry tracing with OTLP exporter.

    Sets up:
    - TracerProvider with resource attributes
    - OTLP exporter (gRPC or HTTP)
    - Span processor (batch for production, simple for dev)
    - FastAPI instrumentation
    """
    global _tracer

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource.create({SERVICE_NAME: "ai-workshop"})
        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("ai-workshop")

        logger.info("OpenTelemetry tracing initialized")
    except ImportError:
        logger.warning("OpenTelemetry packages not installed — tracing disabled")
        _tracer = None
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}")
        _tracer = None


def get_tracer() -> Any:
    """Get the application tracer."""
    global _tracer
    if _tracer is None:
        try:
            from opentelemetry import trace
            _tracer = trace.get_tracer("ai-workshop")
        except ImportError:
            pass
    return _tracer


@contextmanager
def trace_span(name: str, attributes: Optional[dict[str, Any]] = None):
    """
    Context manager to create a tracing span.

    Args:
        name: Span name
        attributes: Optional span attributes

    Usage:
        with trace_span("agent.research", {"query": "RAG"}):
            result = await research_agent(query)
    """
    tracer = get_tracer()
    if tracer is None:
        yield
        return

    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        try:
            yield span
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            raise


def add_span_event(name: str, attributes: Optional[dict[str, Any]] = None) -> None:
    """Add an event to the current active span."""
    tracer = get_tracer()
    if tracer is None:
        return

    from opentelemetry import trace
    span = trace.get_current_span()
    if span.is_recording():
        span.add_event(name, attributes=attributes or {})
