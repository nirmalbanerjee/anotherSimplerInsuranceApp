# Telemetry Architecture

## Overview

The application uses a **split observability architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                    Backend Application                  │
│                                                         │
│  ┌──────────────────┐        ┌──────────────────┐       │
│  │  OpenTelemetry   │        │   Prometheus     │       │
│  │   Instrumentation│        │   Metrics        │       │
│  └────────┬─────────┘        └─────────┬────────┘       │
└───────────┼────────────────────────────┼────────────────┘
            │                            │
            │ OTLP/gRPC                  │ HTTP /metrics
            │ (Traces only)              │ (Scrape)
            ▼                            ▼
   ┌────────────────┐          ┌────────────────┐
   │     Jaeger     │          │   Prometheus   │
   │   (Tracing)    │          │   (Metrics)    │
   │   Port 16686   │          │   Port 9090    │
   └────────────────┘          └────────┬───────┘
                                        │
                                        │ Query
                                        ▼
                               ┌────────────────┐
                               │    Grafana     │
                               │ (Dashboards)   │
                               │   Port 3001    │
                               └────────────────┘
```

## Why Split Architecture?

**Jaeger** is optimized for **distributed tracing** (OTLP traces):
- Request flow visualization
- Span timing & dependencies
- Error stack traces
- Service topology

**Prometheus** is optimized for **time-series metrics**:
- Counters (total requests, auth events)
- Histograms (latency percentiles)
- Gauges (active connections)
- Alerting & long-term storage

**Grafana** provides unified visualization for both.

## Data Flow

### Traces (OpenTelemetry → Jaeger)
1. FastAPI request arrives
2. OpenTelemetry auto-instruments creates span
3. SQLAlchemy queries create child spans
4. Span data batched and sent to Jaeger via OTLP gRPC (port 4317)
5. View in Jaeger UI (port 16686)

### Metrics (Prometheus Client → Prometheus)
1. Business events recorded (auth, policy ops)
2. HTTP request metrics collected (count, duration)
3. Prometheus scrapes `/metrics` endpoint every 15s
4. Data stored in Prometheus TSDB
5. Query via PromQL or visualize in Grafana

### Logs (Structured JSON → File)
1. Every request logged with `request_id`
2. JSON format includes trace context
3. Written to `backend/logs/app.log` (rotating)
4. `request_id` correlates with Jaeger trace ID

## Why Not Send Metrics to Jaeger?

**Jaeger does not support OTLP metrics** - it only accepts traces.

Attempting to export metrics to Jaeger causes:
```
StatusCode.UNIMPLEMENTED: Jaeger does not implement OTLP metrics
```

**Solution**: Use Prometheus for metrics (industry standard).

## Environment Variables

```bash
# Traces → Jaeger
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317  # OTLP gRPC endpoint

# Metrics → Prometheus (auto-discovered via scraping)
# No explicit endpoint needed - Prometheus scrapes /metrics

# Service identification
SERVICE_NAME=insurance-api
```

## Key Endpoints

| Endpoint | Purpose | Consumer |
|----------|---------|----------|
| `/health` | Health check | Load balancer |
| `/metrics` | Prometheus metrics | Prometheus scraper |
| `/docs` | OpenAPI schema | Developers |
| `4317` (OTLP gRPC) | Trace export | Jaeger collector |

## Example Correlation

When you make a request:

1. **Log entry** (`app.log`):
```json
{
  "ts": "2025-11-20T12:00:00",
  "request_id": "abc123",
  "method": "POST",
  "path": "/policies",
  "username": "alice",
  "status_code": 200,
  "duration_ms": 45
}
```

2. **Trace in Jaeger** (search by `abc123`):
```
POST /policies [45ms]
  ├─ auth.verify_token [5ms]
  ├─ db.query [30ms]
  └─ response.serialize [10ms]
```

3. **Metrics in Prometheus**:
```promql
http_requests_total{method="POST",path="/policies",status="200"} = 1
http_request_duration_seconds{path="/policies"} = 0.045
policy_operations_total{operation="create",role="admin"} = 1
```

4. **Grafana Dashboard**: Shows all three combined!

## Production Considerations

### Cloud-Native Alternatives

Instead of self-hosted Jaeger/Prometheus:

**AWS**:
- Traces: AWS X-Ray (OpenTelemetry compatible)
- Metrics: CloudWatch + Prometheus (via EKS)
- Logs: CloudWatch Logs

**Datadog / New Relic**:
- Send OTLP traces to their collectors
- Use their metric agents
- Unified platform

**Honeycomb / Lightstep**:
- Full OpenTelemetry support
- Both traces & metrics
- Advanced querying

### Migration Path

Current setup makes migration easy:

```bash
# Switch from Jaeger to Datadog
export OTEL_EXPORTER_OTLP_ENDPOINT=https://trace.agent.datadoghq.com:4317

# Switch from Prometheus to CloudWatch
# Replace prometheus-client with cloudwatch metric publisher
```

## Performance Impact

**Traces**:
- ~1-2ms overhead per request
- Batched export (minimal network impact)
- Sampling recommended in production (e.g., 10%)

**Metrics**:
- Negligible (in-memory counters)
- Scrape endpoint cached
- No per-request overhead

**Logs**:
- Async writing (non-blocking)
- Rotating to prevent disk fill
- ~0.5ms per request

## Troubleshooting

**"UNIMPLEMENTED" error in logs**:
✅ Fixed! Metrics no longer exported to Jaeger.

**Traces not appearing**:
- Check `OTEL_EXPORTER_OTLP_ENDPOINT` points to Jaeger
- Verify port 4317 accessible
- Wait 10-15s for batch export

**Metrics endpoint empty**:
- Generate traffic first: `curl http://localhost:8000/health`
- Check `TELEMETRY_ENABLED=True` in logs
- Verify prometheus-client installed

**High memory usage**:
- Reduce trace batch size in production
- Enable sampling
- Set shorter metric retention
