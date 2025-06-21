"""
OpenTelemetry instrumentation for monitoring and observability.
"""

import os
from fastapi import FastAPI

# Check if we're in test mode or if telemetry is disabled
TELEMETRY_ENABLED = os.getenv("ENABLE_TELEMETRY", "false").lower() == "true"
TESTING = os.getenv("TESTING", "false").lower() == "true"

if TELEMETRY_ENABLED and not TESTING:
    try:
        from opentelemetry import trace, metrics
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from azure.monitor.opentelemetry import configure_azure_monitor

        TELEMETRY_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: OpenTelemetry dependencies not available: {e}")
        TELEMETRY_AVAILABLE = False

        # Set up mock implementations
        class MockTrace:
            def get_tracer(self, name):
                return None

        class MockMetrics:
            def get_meter(self, name):
                return None

        trace = MockTrace()
        metrics = MockMetrics()
        FastAPIInstrumentor = None
        SQLAlchemyInstrumentor = None
        HTTPXClientInstrumentor = None
else:
    # Mock implementations for testing or when telemetry is disabled
    TELEMETRY_AVAILABLE = False

    class MockTrace:
        def get_tracer(self, name):
            return None

    class MockMetrics:
        def get_meter(self, name):
            return None

    trace = MockTrace()
    metrics = MockMetrics()
    FastAPIInstrumentor = None
    SQLAlchemyInstrumentor = None
    HTTPXClientInstrumentor = None

import time
import logging
from typing import Dict, Any

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Global tracer and meter instances
tracer = None
meter = None

# Custom metrics
request_duration = None
ai_generation_duration = None
database_operation_duration = None
cost_tracking_counter = None


def setup_opentelemetry(app: FastAPI, sqlalchemy_engine=None):
    """
    Setup OpenTelemetry instrumentation for the application.
    Uses Azure Monitor if configured, or default exporter otherwise.
    """
    global tracer, meter, request_duration, ai_generation_duration, database_operation_duration, cost_tracking_counter

    # Skip telemetry setup during testing or if telemetry is not available
    if TESTING or not TELEMETRY_AVAILABLE:
        logger.info("Skipping OpenTelemetry setup (testing or telemetry not available)")
        return app

    try:
        # Get the Azure Monitor connection string from environment
        app_insights_conn_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        service_name = os.getenv("SERVICE_NAME", "pathfinder-api")
        environment = os.getenv("ENVIRONMENT", "development")

        # Configure resources
        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                "environment": environment,
                "service.namespace": "pathfinder",
                "service.version": "1.0.0",
            }
        )

        if app_insights_conn_string:
            logger.info("Setting up Azure Monitor OpenTelemetry instrumentation")
            configure_azure_monitor(connection_string=app_insights_conn_string, resource=resource)
        else:
            logger.info("Setting up default OpenTelemetry instrumentation")
            # Setup tracer provider with a default exporter (console)
            tracer_provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(OTLPSpanExporter())
            tracer_provider.add_span_processor(processor)
            trace.set_tracer_provider(tracer_provider)

        # Initialize global tracer and meter
        tracer = trace.get_tracer(__name__)
        meter = metrics.get_meter(__name__)

        # Create custom metrics
        request_duration = meter.create_histogram(
            "http_request_duration_seconds", description="Duration of HTTP requests"
        )

        ai_generation_duration = meter.create_histogram(
            "ai_generation_duration_seconds", description="Time taken for AI operations"
        )

        database_operation_duration = meter.create_histogram(
            "database_operation_duration_seconds", description="Time taken for database operations"
        )

        cost_tracking_counter = meter.create_counter(
            "cost_tracking_total", description="Track various cost-related metrics"
        )

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())

        # Instrument HTTPX for outgoing requests
        HTTPXClientInstrumentor().instrument()

        # Instrument SQLAlchemy if an engine is provided
        if sqlalchemy_engine:
            SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)

        logger.info("OpenTelemetry instrumentation setup complete")

    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry instrumentation: {str(e)}")
        # Continue application startup even if instrumentation fails

    return app


class EnhancedMonitoring:
    """Enhanced monitoring class for Application Insights integration."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def track_ai_operation(self, operation_type: str, tokens_used: int, model: str = "gpt-4o-mini"):
        """Track AI operation with detailed metrics."""
        if not tracer:
            return

        start_time = time.time()
        try:
            with tracer.start_as_current_span("ai_operation") as span:
                span.set_attributes(
                    {
                        "ai.operation_type": operation_type,
                        "ai.tokens_used": tokens_used,
                        "ai.model": model,
                    }
                )

                # Track costs
                if cost_tracking_counter:
                    cost_tracking_counter.add(
                        tokens_used, {"operation": operation_type, "model": model}
                    )

        finally:
            duration = time.time() - start_time
            if ai_generation_duration:
                ai_generation_duration.record(
                    duration, {"operation": operation_type, "model": model}
                )

    def track_database_operation(self, operation: str, table: str):
        """Track database operation performance."""
        if not tracer:
            return

        start_time = time.time()
        try:
            with tracer.start_as_current_span("database_operation") as span:
                span.set_attributes({"db.operation": operation, "db.table": table})
        finally:
            duration = time.time() - start_time
            if database_operation_duration:
                database_operation_duration.record(
                    duration, {"operation": operation, "table": table}
                )

    def track_custom_event(self, event_name: str, properties: Dict[str, Any] = None):
        """Track custom events for business metrics."""
        if not tracer:
            return

        with tracer.start_as_current_span(event_name) as span:
            if properties:
                span.set_attributes(properties)

    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track errors with context information."""
        if not tracer:
            return

        with tracer.start_as_current_span("error_occurred") as span:
            span.set_attributes(
                {
                    "error.type": type(error).__name__,
                    "error.message": str(error),
                    "error.context": str(context) if context else "",
                }
            )
            span.record_exception(error)


# Global monitoring instance
monitoring = EnhancedMonitoring()
