# Telemetry & Observability

This application includes comprehensive observability through OpenTelemetry, Prometheus, and Jaeger.

## Components

### 1. Distributed Tracing (Jaeger)
- **URL**: http://localhost:16686
- Auto-instrumented FastAPI endpoints
- SQLAlchemy query tracing
- End-to-end request tracking with trace IDs
- **Exports**: OpenTelemetry traces via OTLP (port 4317)

### 2. Metrics (Prometheus + Grafana)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Metrics Endpoint**: http://localhost:8000/metrics
- **Exports**: Prometheus format metrics (scraped by Prometheus)
- **Note**: Metrics are NOT sent to Jaeger (Jaeger only supports traces)

#### Available Metrics:
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram
- `auth_events_total` - Authentication events (register_success, login_failed, etc.)
- `policy_operations_total` - Policy CRUD operations by role

### 3. Structured Logging
- JSON format with correlation IDs
- Fields: ts, level, request_id, path, method, status_code, status_text, duration_ms, username, role, client_ip, user_agent
- Log file: `backend/logs/app.log`
- Error-level logging for HTTP status >= 400

### 4. Health Endpoints
- `/health` - Liveness check
- `/metrics` - Prometheus metrics scraping

## Running with Observability

### Start Full Stack:
```bash
docker compose up -d
```

### Access Services:
- **Frontend**: http://localhost:3023
- **Backend API**: http://localhost:8000/docs
- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

### Grafana Setup:
1. Login: admin/admin
2. Add Prometheus data source: `http://prometheus:9090`
3. Add Jaeger data source: `http://jaeger:16686`
4. Import dashboards or create custom visualizations

### Example Queries (Prometheus):
```promql
# Request rate by endpoint
rate(http_requests_total[5m])

# Auth success rate
sum(rate(auth_events_total{event_type="login_success"}[5m])) / sum(rate(auth_events_total{event_type=~"login.*"}[5m]))

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Policy operations by role
sum by(user_role) (policy_operations_total)
```

### Viewing Traces:
1. Open Jaeger UI (http://localhost:16686)
2. Select service: `insurance-api`
3. Click "Find Traces"
4. Drill into individual requests to see:
   - Request span with timing
   - DB query spans
   - Auth dependency calls
   - Error stack traces (if any)

### Log Correlation:
Every log entry includes `request_id` which matches the trace ID in Jaeger for end-to-end correlation.

## Local Development (without Docker)

If running locally without observability stack:
```bash
# Backend will detect missing OTLP endpoint and disable telemetry gracefully
cd backend
python -m uvicorn main:app --reload
```

Metrics and traces won't be exported but app continues to function normally with JSON logging.

## Production Recommendations
1. Use managed observability (AWS X-Ray, Datadog, New Relic, Honeycomb)
2. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to your collector
3. Enable sampling for high-traffic endpoints
4. Secure Grafana with proper authentication
5. Set retention policies for metrics & traces
6. Add alerting rules in Prometheus

## Environment Variables
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317  # OTLP collector endpoint
SERVICE_NAME=insurance-api                       # Service identifier for traces
```

## Testing Telemetry
```bash
# Generate traffic
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/register -H 'Content-Type: application/json' \
  -d '{"username":"test","password":"test","role":"user"}'

# Check metrics
curl http://localhost:8000/metrics

# View in Jaeger
open http://localhost:16686
```
