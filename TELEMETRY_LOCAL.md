# Running Telemetry Locally (Without Docker)

## Option 1: Full Stack with Docker Compose (Recommended)

This gives you the complete observability experience with minimal setup.

```bash
# Start all services (backend, frontend, DB, Jaeger, Prometheus, Grafana)
docker compose up -d

# Access services:
# - Backend API: http://localhost:8000/docs
# - Frontend: http://localhost:3023
# - Jaeger Traces: http://localhost:16686
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3001 (admin/admin)
# - Metrics endpoint: http://localhost:8000/metrics

# Stop when done
docker compose down
```

---

## Option 2: Backend Only with Local Observability Tools

### Step 1: Install Dependencies

```bash
# Create/activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows

# Install all dependencies including telemetry
pip install -r backend/requirements.txt
```

### Step 2: Start Jaeger Locally (for traces)

```bash
# Run Jaeger all-in-one (easiest option)
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Verify: http://localhost:16686
```

### Step 3: Start Backend with Local DB

```bash
cd backend

# Set environment variables (optional - defaults work)
export DB_URL="sqlite:///./app.db"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export SERVICE_NAME="insurance-api"

# Start backend
uvicorn main:app --reload --port 8000

# Backend will be available at http://localhost:8000
```

### Step 4: Access Telemetry

```bash
# Health check
curl http://localhost:8000/health

# Prometheus metrics
curl http://localhost:8000/metrics

# View traces in Jaeger
open http://localhost:16686
# Select service: "insurance-api"
# Click "Find Traces"
```

### Step 5: Generate Test Traffic

```bash
# Register a user
curl -X POST http://localhost:8000/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass","role":"admin"}'

# Login
curl -X POST http://localhost:8000/login-json \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass"}'

# Extract token and create policy
TOKEN=$(curl -s -X POST http://localhost:8000/login-json \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/policies \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Life Insurance","details":"Comprehensive coverage"}'

# Check metrics
curl http://localhost:8000/metrics | grep -E '(auth_events|policy_operations)'
```

### Step 6: View in Jaeger

1. Open http://localhost:16686
2. Select **Service**: `insurance-api`
3. Click **Find Traces**
4. You'll see traces for:
   - POST /register
   - POST /login-json
   - POST /policies
5. Click any trace to see:
   - Request timing
   - Database queries
   - Auth token generation
   - HTTP status codes

---

## Option 3: Backend Without Telemetry (Lightweight)

If you don't need tracing/metrics right now:

```bash
# The app detects missing telemetry and runs normally
cd backend
uvicorn main:app --reload

# You still get:
# - Full API functionality
# - JSON structured logging in backend/logs/app.log
# - Swagger docs at http://localhost:8000/docs
```

---

## Option 4: Prometheus Locally (for metrics only)

### Start Prometheus

```bash
# Create prometheus config
cat > /tmp/prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'insurance-backend'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
EOF

# Run Prometheus
docker run -d --name prometheus \
  -p 9090:9090 \
  -v /tmp/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Access: http://localhost:9090
```

### Query Metrics in Prometheus

1. Go to http://localhost:9090
2. Try these queries:
   ```promql
   # Total requests
   http_requests_total
   
   # Request rate (last 5 min)
   rate(http_requests_total[5m])
   
   # Auth events
   auth_events_total
   
   # P95 latency
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   ```

---

## File Locations for Local Development

```
Project Root/
├── backend/
│   ├── main.py                  # Main app with telemetry integration
│   ├── telemetry.py            # OpenTelemetry setup
│   ├── requirements.txt        # All dependencies
│   ├── logs/
│   │   └── app.log            # JSON structured logs
│   └── app.db                 # SQLite database (auto-created)
├── prometheus.yml              # Prometheus scrape config
├── TELEMETRY.md               # Full telemetry guide
└── TELEMETRY_SETUP.md         # Quick start guide
```

---

## Environment Variables Reference

```bash
# Database
DB_URL=sqlite:///./app.db                    # or postgresql://...

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317  # Jaeger/OTLP collector
SERVICE_NAME=insurance-api                    # Service name in traces

# Logging
LOG_DIR=./logs                               # Log file directory

# Auth
SECRET_KEY=supersecretkey                    # JWT secret (change in prod)

# Backend port
PORT=8000                                    # API listen port
```

---

## Viewing Logs Locally

### Real-time log streaming:
```bash
tail -f backend/logs/app.log | jq '.'
```

### Filter error logs:
```bash
cat backend/logs/app.log | jq 'select(.level=="ERROR")'
```

### Search by user:
```bash
cat backend/logs/app.log | jq 'select(.username=="alice")'
```

### Trace a specific request:
```bash
# Get request_id from first log, then filter
cat backend/logs/app.log | jq 'select(.request_id=="<REQUEST_ID>")'
```

---

## Troubleshooting Local Setup

### "Module not found: opentelemetry"
```bash
pip install -r backend/requirements.txt
```

### "Connection refused to Jaeger"
```bash
# Check if Jaeger is running
docker ps | grep jaeger

# Restart Jaeger
docker restart jaeger

# Or check endpoint
curl http://localhost:4317  # Should connect (may show empty response)
```

### "Metrics endpoint returns error"
Check that telemetry dependencies are installed:
```bash
python3 -c "from prometheus_client import Counter; print('OK')"
```

### "No traces in Jaeger"
1. Generate traffic: `curl http://localhost:8000/health`
2. Wait 10-15 seconds (batch export delay)
3. Refresh Jaeger UI
4. Check backend logs: `tail backend/logs/app.log`

### "App works but no telemetry"
This is normal! App has graceful degradation:
```python
# In backend/main.py
TELEMETRY_ENABLED = True  # if all imports succeed
TELEMETRY_ENABLED = False # if imports fail - app still works
```

---

## Minimal Quick Start (TL;DR)

```bash
# 1. Install deps
pip install -r backend/requirements.txt

# 2. Start Jaeger (one-liner)
docker run -d -p 16686:16686 -p 4317:4317 -e COLLECTOR_OTLP_ENABLED=true jaegertracing/all-in-one

# 3. Start backend
cd backend && uvicorn main:app --reload

# 4. Test
curl http://localhost:8000/health
curl http://localhost:8000/metrics

# 5. View traces
open http://localhost:16686
```

Done! You now have full telemetry running locally. 🎉
