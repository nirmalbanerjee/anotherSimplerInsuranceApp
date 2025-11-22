"""
OpenTelemetry and Prometheus instrumentation for Insurance API
"""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from fastapi import Response
import psutil
import os as system_os

# Service name for traces
SERVICE_NAME = os.getenv("SERVICE_NAME", "insurance-api")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")

# Configure OpenTelemetry tracing (Jaeger)
resource = Resource(attributes={"service.name": SERVICE_NAME})
trace_provider = TracerProvider(resource=resource)
otlp_span_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_span_exporter))
trace.set_tracer_provider(trace_provider)

# Note: ProcessCollector and GCCollector are automatically registered by prometheus_client
# No need to explicitly register them again

# Note: Metrics are handled by Prometheus only (not OTLP)
# Jaeger does not support OTLP metrics, only traces

# Prometheus custom metrics
prom_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
prom_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)
prom_auth_events = Counter(
    'auth_events_total',
    'Authentication events',
    ['event_type', 'role']
)
prom_policy_operations = Counter(
    'policy_operations_total',
    'Policy CRUD operations',
    ['operation', 'user_role']
)

# Application-level resource metrics
app_memory_bytes = Gauge(
    'app_memory_usage_bytes',
    'Application memory usage in bytes'
)
app_cpu_percent = Gauge(
    'app_cpu_usage_percent',
    'Application CPU usage percentage'
)
app_open_files = Gauge(
    'app_open_files_count',
    'Number of open file descriptors'
)

def update_resource_metrics():
    """Update application resource metrics"""
    try:
        process = psutil.Process(system_os.getpid())
        app_memory_bytes.set(process.memory_info().rss)
        app_cpu_percent.set(process.cpu_percent(interval=None))
        app_open_files.set(process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files()))
    except Exception:
        pass  # Ignore errors in metrics collection

def instrument_app(app):
    """Auto-instrument FastAPI and SQLAlchemy"""
    FastAPIInstrumentor.instrument_app(app)
    from db.database import engine
    SQLAlchemyInstrumentor().instrument(engine=engine)

def get_metrics_endpoint():
    """Returns Prometheus metrics endpoint handler"""
    def metrics():
        update_resource_metrics()  # Update app-level metrics before serving
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    return metrics

def record_auth_event(event_type: str, role: str = "unknown"):
    """Record authentication event"""
    prom_auth_events.labels(event_type=event_type, role=role).inc()

def record_policy_operation(operation: str, user_role: str):
    """Record policy operation"""
    prom_policy_operations.labels(operation=operation, user_role=user_role).inc()

def record_http_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    prom_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    prom_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
