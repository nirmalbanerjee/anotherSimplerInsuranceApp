# Grafana Dashboard Setup Guide

The dashboard JSON provisioning may not work perfectly on all systems. Here's how to manually create the monitoring dashboard.

## Access Grafana
1. Open http://localhost:3001
2. Login with: **admin** / **admin**

## Create Dashboard Manually

### Step 1: Create New Dashboard
1. Click **"+"** → **"Create Dashboard"**
2. Click **"Add visualization"**
3. Select **"Prometheus"** as data source

### Step 2: Add Container CPU Panel
1. **Query**: 
   ```promql
   rate(container_cpu_usage_seconds_total{id=~"/docker/.*"}[5m]) * 100
   ```
2. **Legend**: `{{id}}`
3. **Panel Title**: "Docker Container CPU Usage"
4. **Unit**: Percent (0-100)
5. **Visualization**: Time series
6. Click **"Apply"**

### Step 3: Add Container Memory Panel
1. Click **"Add"** → **"Visualization"**
2. **Query**:
   ```promql
   container_memory_usage_bytes{id=~"/docker/.*"} / 1024 / 1024
   ```
3. **Legend**: `{{id}}`
4. **Panel Title**: "Docker Container Memory Usage"
5. **Unit**: megabytes
6. **Visualization**: Time series
7. Click **"Apply"**

### Step 4: Add Backend App CPU Gauge
1. Click **"Add"** → **"Visualization"**
2. **Query**:
   ```promql
   app_cpu_usage_percent
   ```
3. **Panel Title**: "Backend App CPU %"
4. **Visualization**: Gauge
5. **Unit**: Percent (0-100)
6. **Thresholds**:
   - Green: 0-50
   - Yellow: 50-80
   - Red: 80-100
7. Click **"Apply"**

### Step 5: Add Backend App Memory Gauge
1. Click **"Add"** → **"Visualization"**
2. **Query**:
   ```promql
   app_memory_usage_bytes / 1024 / 1024
   ```
3. **Panel Title**: "Backend App Memory (MB)"
4. **Visualization**: Gauge
5. **Unit**: megabytes
6. **Thresholds**:
   - Green: 0-256
   - Yellow: 256-512
   - Red: 512+
7. Click **"Apply"**

### Step 6: Add Database Connections
1. Click **"Add"** → **"Visualization"**
2. **Query**:
   ```promql
   pg_stat_database_numbackends{datname="insurance"}
   ```
3. **Panel Title**: "Database Connections"
4. **Visualization**: Time series
5. **Unit**: short
6. Click **"Apply"**

### Step 7: Add Database Transactions
1. Click **"Add"** → **"Visualization"**
2. **Query A (Commits)**:
   ```promql
   rate(pg_stat_database_xact_commit{datname="insurance"}[5m])
   ```
   **Legend**: "Commits/s"
   
3. **Query B (Rollbacks)**:
   ```promql
   rate(pg_stat_database_xact_rollback{datname="insurance"}[5m])
   ```
   **Legend**: "Rollbacks/s"
   
4. **Panel Title**: "Database Transaction Rate"
5. **Visualization**: Time series
6. **Unit**: ops (operations per second)
7. Click **"Apply"**

### Step 8: Add Database Size
1. Click **"Add"** → **"Visualization"**
2. **Query**:
   ```promql
   pg_database_size_bytes{datname="insurance"} / 1024 / 1024
   ```
3. **Panel Title**: "Database Size (MB)"
4. **Visualization**: Stat
5. **Unit**: megabytes
6. Click **"Apply"**

### Step 9: Add HTTP Requests
1. Click **"Add"** → **"Visualization"**
2. **Query**:
   ```promql
   rate(http_requests_total[5m])
   ```
3. **Legend**: `{{method}} {{endpoint}} ({{status}})`
4. **Panel Title**: "HTTP Request Rate"
5. **Visualization**: Time series
6. **Unit**: requests/sec
7. Click **"Apply"**

### Step 10: Add Auth Events
1. Click **"Add"** → **"Visualization"**
2. **Query**:
   ```promql
   rate(auth_events_total[5m])
   ```
3. **Legend**: `{{event_type}} ({{role}})`
4. **Panel Title**: "Authentication Events"
5. **Visualization**: Time series
6. **Unit**: events/sec
7. Click **"Apply"**

### Step 11: Save Dashboard
1. Click **"Save dashboard"** (disk icon in top right)
2. **Name**: "Insurance App Monitoring"
3. Click **"Save"**

## Dashboard Settings
After saving, you can configure:
- **Auto-refresh**: Set to 10s or 30s (top right)
- **Time range**: Default to "Last 15 minutes"
- **Variables**: Add filters for container names if needed

## Troubleshooting

### No Data in Panels
1. Check Prometheus targets are UP:
   - Go to http://localhost:9090/targets
   - All 3 targets should show "UP" status

2. Verify metrics exist in Prometheus:
   - Go to http://localhost:9090
   - Try querying: `container_cpu_usage_seconds_total`
   - Should see results

3. Check time range:
   - Make sure dashboard time range includes recent data
   - Try "Last 15 minutes" or "Last 1 hour"

### Container Metrics Not Showing
- cAdvisor uses `id` label, not `name`
- Container IDs are hashes like `/docker/13b3f78fe9...`
- Use query: `{id=~"/docker/.*"}` to filter Docker containers

### Database Metrics Empty
- Check postgres_exporter is running: `docker compose ps`
- Verify connection: `docker compose logs postgres_exporter`
- Database must have activity to show transaction rates

### Backend App Metrics Not Updating
- Ensure backend container is running
- Check metrics endpoint: `curl http://localhost:8000/metrics`
- Look for `app_cpu_usage_percent` and `app_memory_usage_bytes`

## Quick Test Queries

Test these in Prometheus (http://localhost:9090) to verify metrics:

```promql
# Container CPU
container_cpu_usage_seconds_total

# Container Memory  
container_memory_usage_bytes

# Backend metrics
app_cpu_usage_percent
app_memory_usage_bytes

# Database metrics
pg_stat_database_numbackends
pg_database_size_bytes

# Application metrics
http_requests_total
auth_events_total
policy_operations_total
```

All queries should return results. If not, check the corresponding service logs.
