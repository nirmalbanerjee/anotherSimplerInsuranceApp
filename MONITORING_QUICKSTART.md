# Resource Monitoring - Quick Start

## ✅ All Monitoring Components Are Running

Your Docker-based Insurance App now has comprehensive resource monitoring:

### 🎯 Access Points
| Service | URL | Purpose |
|---------|-----|---------|
| **Grafana** | http://localhost:3001 | Dashboards & Visualization |
| **Prometheus** | http://localhost:9090 | Metrics Database |
| **cAdvisor** | http://localhost:8080 | Container Stats |
| **Jaeger** | http://localhost:16686 | Distributed Tracing |

**Grafana Login**: admin / admin

---

## 📊 Available Metrics

### 1. Container Metrics (via cAdvisor)
Monitor all Docker containers:
```promql
# CPU Usage (%) - All containers
rate(container_cpu_usage_seconds_total[5m]) * 100

# CPU Usage (%) - Only Docker containers (exclude system)
rate(container_cpu_usage_seconds_total{id=~"/docker/[^/]+"}[5m]) * 100

# Memory Usage (MB) - All containers
container_memory_usage_bytes / 1024 / 1024

# Memory Usage (MB) - Only Docker containers
container_memory_usage_bytes{id=~"/docker/[^/]+"} / 1024 / 1024

# Network I/O (KB/s) - All containers
rate(container_network_receive_bytes_total[5m]) / 1024
rate(container_network_transmit_bytes_total[5m]) / 1024

# Network I/O (KB/s) - Only Docker containers
rate(container_network_receive_bytes_total{id=~"/docker/[^/]+"}[5m]) / 1024
rate(container_network_transmit_bytes_total{id=~"/docker/[^/]+"}[5m]) / 1024
```

### 2. Database Metrics (via postgres_exporter)
Monitor PostgreSQL performance:
```promql
# Active Connections
pg_stat_database_numbackends{datname="insurance"}

# Transaction Rate (per second)
rate(pg_stat_database_xact_commit{datname="insurance"}[5m])
rate(pg_stat_database_xact_rollback{datname="insurance"}[5m])

# Database Size (MB)
pg_database_size_bytes{datname="insurance"} / 1024 / 1024
```

### 3. Application Metrics (Backend Python App)
Monitor backend application:
```promql
# App CPU Usage (%)
app_cpu_usage_percent

# App Memory Usage (MB)
app_memory_usage_bytes / 1024 / 1024

# Open File Descriptors
app_open_files_count

# Python Garbage Collection
rate(python_gc_collections_total[5m])

# HTTP Requests
rate(http_requests_total[5m])

# Auth Events
rate(auth_events_total[5m])

# Policy Operations
rate(policy_operations_total[5m])
```

---

## 🚀 Quick Start - Create Dashboard in Grafana

### Option 1: Use Prometheus Explore (Easiest)
1. Go to http://localhost:3001
2. Click **Explore** (compass icon in sidebar)
3. Paste any query from above
4. Click **Run query**
5. See instant results!

### Option 2: Create Custom Dashboard
1. Follow the step-by-step guide in `GRAFANA_DASHBOARD_SETUP.md`
2. Build panels one by one with the queries above
3. Save your custom dashboard

---

## 🔍 Verify Everything Is Working

Run these commands to test:

```bash
# Check all containers are running
docker compose ps

# Test container metrics
curl -s http://localhost:8080/metrics | grep container_cpu_usage_seconds_total | head -3

# Test database metrics
curl -s http://localhost:9187/metrics | grep pg_stat_database | head -5

# Test backend metrics
curl -s http://localhost:8000/metrics | grep app_cpu_usage_percent
```

All commands should return data.

---

## 📈 What Each Tool Does

### cAdvisor (Port 8080)
- Monitors **all Docker containers**
- Tracks: CPU, Memory, Network, Disk I/O
- Updates: Every few seconds
- No configuration needed

### PostgreSQL Exporter (Port 9187)
- Monitors **PostgreSQL database**
- Tracks: Connections, Transactions, Table sizes
- Connects to: `db:5432/insurance`
- Auto-configured

### Backend Metrics (Port 8000/metrics)
- Monitors **Python application**
- Tracks: App-level CPU/Memory, HTTP requests, Auth events
- Updates: On every scrape (15s)
- Uses: Prometheus Python client + psutil

### Prometheus (Port 9090)
- **Scrapes all 3 exporters** every 15 seconds
- Stores time-series data
- Provides query interface (PromQL)
- Powers Grafana dashboards

### Grafana (Port 3001)
- **Visualizes** Prometheus data
- Creates dashboards with charts/graphs
- Sends alerts (can be configured)
- User-friendly interface

---

## 🎨 Dashboard Ideas

Create panels to track:
- 📊 **Resource Usage**: CPU/Memory per container over time
- 🗄️ **Database Health**: Connection count, transaction rate
- 🌐 **HTTP Traffic**: Requests per endpoint, error rates
- 🔐 **Security**: Failed login attempts, auth events
- 📝 **Business Metrics**: Policies created, user registrations

---

## 🐛 Troubleshooting

### Dashboard Shows "No Data"
1. **Check time range**: Set to "Last 15 minutes"
2. **Verify targets**: http://localhost:9090/targets (all should be UP)
3. **Test query**: Use Prometheus Explore first
4. **Check syntax**: Container metrics use `id` label, not `name`

### Metrics Not Updating
```bash
# Restart Prometheus to reload config
docker compose restart prometheus

# Restart backend to reload metrics
docker compose restart backend

# Check logs for errors
docker compose logs prometheus
docker compose logs backend
```

### Want More Metrics?
Edit `backend/telemetry.py` to add custom metrics:
```python
from prometheus_client import Counter, Gauge, Histogram

my_metric = Counter('my_custom_metric', 'Description', ['label1'])
my_metric.labels(label1='value').inc()
```

---

## 📚 Full Documentation

- **Detailed Setup**: `GRAFANA_DASHBOARD_SETUP.md`
- **Metrics Guide**: `RESOURCE_MONITORING.md`
- **Prometheus Config**: `prometheus.yml`
- **Dashboard JSON**: `grafana/provisioning/dashboards/resource-monitoring.json`

---

## ✨ Next Steps

1. **Open Grafana**: http://localhost:3001 (admin/admin)
2. **Try Explore**: Click compass icon, paste a query, run it
3. **Build Dashboard**: Add panels for the metrics you care about
4. **Set Alerts**: Configure notifications for critical thresholds
5. **Export**: Save your dashboard JSON for version control

Happy monitoring! 🎉
