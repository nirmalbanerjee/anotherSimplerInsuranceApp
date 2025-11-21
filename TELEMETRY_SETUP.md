# Telemetry Setup - Quick Start

## Installation

```bash
# Install dependencies
pip install -r backend/requirements.txt
```

## Verification

```bash
# Test imports
python3 -c "from opentelemetry import trace, metrics; print('✓ OpenTelemetry installed')"
python3 -c "from prometheus_client import Counter; print('✓ Prometheus client installed')"
```

## Running with Docker (Recommended)

```bash
# Build and start all services including observability stack
docker compose build
docker compose up -d

# Verify services
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## Access Observability Tools

- **Jaeger UI**: http://localhost:16686 - View distributed traces
- **Prometheus**: http://localhost:9090 - Query metrics  
- **Grafana**: http://localhost:3000 - Dashboards (login: admin/admin)
- **Backend Metrics**: http://localhost:8000/metrics

## Testing Telemetry

```bash
# Generate test traffic
for i in {1..10}; do
  curl -X POST http://localhost:8000/register \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"user$i\",\"password\":\"pass\",\"role\":\"user\"}"
done

# View metrics
curl http://localhost:8000/metrics | grep auth_events

# Check Jaeger traces
open http://localhost:16686
# Select service: insurance-api
# Click "Find Traces"
```

## Custom Metrics Available

1. **`http_requests_total`** - Total requests by method/endpoint/status
2. **`http_request_duration_seconds`** - Request latency histogram
3. **`auth_events_total`** - Auth events (register_success, login_failed, etc.)
4. **`policy_operations_total`** - Policy CRUD by role

## Prometheus Example Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
sum(rate(http_requests_total{status=~"4..|5.."}[5m])) / sum(rate(http_requests_total[5m]))

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Auth success rate
sum(auth_events_total{event_type="login_success"}) / sum(auth_events_total{event_type=~"login.*"})
```

## Troubleshooting

**Traces not appearing in Jaeger:**
- Ensure `OTEL_EXPORTER_OTLP_ENDPOINT` is set correctly
- Check Jaeger container logs: `docker compose logs jaeger`
- Verify backend can reach Jaeger on port 4317

**Metrics not showing in Prometheus:**
- Check Prometheus targets: http://localhost:9090/targets
- Backend should be listed as `UP`
- Verify `/metrics` endpoint: `curl http://localhost:8000/metrics`

**App crashes with import errors:**
```bash
pip install --upgrade -r backend/requirements.txt
```

## Graceful Degradation

If telemetry dependencies are not installed or OTLP endpoint is unreachable, the app will:
- Set `TELEMETRY_ENABLED = False`
- Skip instrumentation
- Continue serving requests normally
- Still provide JSON structured logging

This allows local development without full observability stack.
