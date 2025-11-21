# Prometheus & Grafana Setup Guide

## Quick Access

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`

## What's Been Set Up

### 1. Prometheus Configuration ✅
- Scrapes metrics from backend every 15 seconds
- Accessible at http://localhost:9090
- Stores time-series data for your insurance app

### 2. Grafana Configuration ✅
- Auto-configured Prometheus datasource
- Pre-built "Insurance App Dashboard"
- Auto-provisioned on startup

### 3. Metrics Available

Your backend exposes these metrics at http://localhost:8000/metrics:

**HTTP Metrics:**
- `http_requests_total` - Total number of HTTP requests by method, path, status
- `http_request_duration_seconds` - Request latency histogram

**Business Metrics:**
- `auth_events_total` - Authentication events (login, register, success, failure)
- `policy_operations_total` - Policy operations (create, list, update, delete)

## Step-by-Step Usage

### Prometheus (http://localhost:9090)

1. **Open Prometheus**: http://localhost:9090

2. **Query Examples** (paste into the query box):

   **Total requests:**
   ```promql
   http_requests_total
   ```

   **Request rate (per second):**
   ```promql
   rate(http_requests_total[5m])
   ```

   **Requests by status code:**
   ```promql
   sum by(status) (http_requests_total)
   ```

   **95th percentile latency:**
   ```promql
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   ```

   **Failed login attempts:**
   ```promql
   auth_events_total{event="login_failed"}
   ```

   **Policy operations:**
   ```promql
   rate(policy_operations_total[5m])
   ```

3. **Switch Views**:
   - **Graph**: Click "Graph" tab to see time-series visualization
   - **Table**: Click "Table" to see raw values

### Grafana (http://localhost:3001)

1. **Login**:
   - Go to http://localhost:3001
   - Username: `admin`
   - Password: `admin`
   - (You may be asked to change password - you can skip it)

2. **View Dashboard**:
   - Click on "Dashboards" (☰ menu → Dashboards)
   - Click "Insurance App Dashboard"
   - You'll see 6 panels with live data!

3. **Dashboard Panels**:

   **Panel 1: HTTP Request Rate**
   - Shows requests per second by endpoint
   - Helps identify traffic patterns

   **Panel 2: Total HTTP Requests**
   - Gauge showing cumulative request count
   - Quick health check

   **Panel 3: Request Duration (p50, p95)**
   - Shows median and 95th percentile latency
   - Identifies slow endpoints

   **Panel 4: Requests by Status Code**
   - Pie chart of 200, 400, 500 responses
   - Spot error rates quickly

   **Panel 5: Authentication Events Rate**
   - Login/register success/failure trends
   - Security monitoring

   **Panel 6: Policy Operations Rate**
   - Create/list/update/delete operations
   - Business activity tracking

4. **Dashboard Features**:
   - **Auto-refresh**: Dashboard updates every 5 seconds
   - **Time range**: Top-right corner - change from "Last 15 minutes" to any range
   - **Zoom**: Click and drag on any graph to zoom in
   - **Legend**: Click legend items to show/hide series

## Generate Some Data

To see interesting graphs, generate some activity:

```bash
# Register users
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass","role":"user"}'

curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user2","password":"pass","role":"admin"}'

# Try failed login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=wronguser&password=wrongpass'

# Create policies (get token first)
TOKEN=$(curl -s -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testpolicy","password":"pass","role":"user"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X POST http://localhost:8000/policies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Policy 1","details":"Test"}'

# Or just use the frontend!
# Go to http://localhost:3023 and interact with the app
```

## Customizing Dashboards

### Add Your Own Panel in Grafana:

1. Click "Add" → "Visualization"
2. Select "Prometheus" datasource
3. Enter a query (e.g., `rate(http_requests_total[5m])`)
4. Choose visualization type (Graph, Gauge, Table, etc.)
5. Click "Apply"
6. Click "Save dashboard" icon (top right)

### Useful Queries to Add:

**Error rate:**
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m]))
```

**Successful registrations:**
```promql
auth_events_total{event="register_success"}
```

**Policy creation rate by role:**
```promql
sum by(role) (rate(policy_operations_total{operation="create"}[5m]))
```

## Prometheus Advanced Features

### Alerts (in Prometheus UI)

1. Go to http://localhost:9090/alerts
2. View configured alerts (currently none, but you can add them!)

### Service Discovery

1. Go to http://localhost:9090/targets
2. See backend scrape status
3. Should show "UP" for `backend:8000/metrics`

### Configuration

1. Go to http://localhost:9090/config
2. View current Prometheus configuration

## Troubleshooting

**Grafana shows "No Data":**
- Wait 30 seconds for first scrape
- Generate traffic: visit http://localhost:3023
- Check Prometheus is scraping: http://localhost:9090/targets

**Prometheus shows backend as "DOWN":**
```bash
# Restart backend
docker compose restart backend

# Check backend logs
docker compose logs backend --tail 20
```

**Can't access Grafana:**
```bash
# Check Grafana is running
docker compose ps | grep grafana

# Restart Grafana
docker compose restart grafana
```

**Dashboard not showing:**
- Refresh browser (Ctrl+Shift+R / Cmd+Shift+R)
- Check provisioning: `docker compose logs grafana | grep provision`

## Tips

1. **Keep generating data**: The more you use the app, the more interesting the graphs!
2. **Experiment with time ranges**: Try "Last 5 minutes", "Last 1 hour", etc.
3. **Create custom dashboards**: Clone the existing one and modify it
4. **Export dashboards**: Save dashboard JSON for backup/sharing
5. **Set up alerts**: Configure email/Slack notifications for errors

## Next Steps

- Set up Jaeger for distributed tracing: http://localhost:16686
- Create alerts for high error rates
- Add custom business metrics
- Build team-specific dashboards

Enjoy your observability stack! 🚀📊
