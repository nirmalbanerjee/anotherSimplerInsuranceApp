# Quick Resource Monitoring Setup

## ✅ What's Been Added

### 1. Container Metrics (cAdvisor)
- **Container**: `cadvisor`
- **Port**: 8080
- **Dashboard**: http://localhost:8080
- **Metrics**: CPU, Memory, Network, Disk I/O for all containers

### 2. Database Metrics (PostgreSQL Exporter)
- **Container**: `anothersimplerinsuranceapp-postgres_exporter-1`
- **Port**: 9187
- **Metrics**: Connections, transactions, database size, query stats

### 3. Application Metrics (Backend)
- **Process metrics**: CPU, memory, file descriptors
- **Python GC metrics**: Garbage collection stats
- **Custom metrics**: Real-time app CPU/memory usage

## 🚀 Quick Start

### View All Metrics
```bash
# Container metrics (cAdvisor)
curl http://localhost:8080/metrics

# Database metrics
curl http://localhost:9187/metrics

# Backend app metrics
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | python3 -m json.tool
```

### Access Dashboards
1. **Grafana**: http://localhost:3001 (admin/admin)
2. **Prometheus**: http://localhost:9090
3. **cAdvisor**: http://localhost:8080
4. **Jaeger Tracing**: http://localhost:16686

## 📊 Key Metrics to Monitor

### Container Resources
```promql
# CPU usage per container (%)
rate(container_cpu_usage_seconds_total{name=~"anothersimplerinsuranceapp.*"}[5m]) * 100

# Memory usage per container (MB)
container_memory_usage_bytes{name=~"anothersimplerinsuranceapp.*"} / 1024 / 1024

# Network I/O (KB/s)
rate(container_network_receive_bytes_total{name=~"anothersimplerinsuranceapp.*"}[5m]) / 1024
rate(container_network_transmit_bytes_total{name=~"anothersimplerinsuranceapp.*"}[5m]) / 1024
```

### Database Performance
```promql
# Active connections
pg_stat_database_numbackends{datname="insurance"}

# Transaction rate (commits/sec)
rate(pg_stat_database_xact_commit{datname="insurance"}[5m])

# Database size (MB)
pg_database_size_bytes{datname="insurance"} / 1024 / 1024
```

### Application Resources
```promql
# App CPU usage (%)
app_cpu_usage_percent

# App memory usage (MB)
app_memory_usage_bytes / 1024 / 1024

# Process CPU seconds
process_cpu_seconds_total

# Process memory (MB)
process_resident_memory_bytes / 1024 / 1024

# Open file descriptors
app_open_files_count

# Python GC rate
rate(python_gc_collections_total[5m])
```

## 🎯 Create Grafana Dashboard

### Manual Method (Recommended)
1. Go to http://localhost:3001
2. Login with admin/admin
3. Click **Explore** (compass icon)
4. Select **Prometheus** datasource
5. Enter a query from above
6. Click **Add to dashboard**
7. Repeat for other metrics
8. Save dashboard

### Example Panels

**Panel 1: Container CPU**
- Type: Time series
- Query: `rate(container_cpu_usage_seconds_total{name=~"anothersimplerinsuranceapp.*"}[5m]) * 100`
- Legend: `{{name}}`

**Panel 2: Database Connections**
- Type: Gauge
- Query: `pg_stat_database_numbackends{datname="insurance"}`
- Threshold: Green (0-10), Yellow (10-50), Red (>50)

**Panel 3: App Memory**
- Type: Time series
- Query: `app_memory_usage_bytes / 1024 / 1024`
- Unit: MB

## 🔍 Verify Setup

```bash
# Check all containers are running
docker compose ps

# Verify metrics endpoints
curl -s http://localhost:8000/metrics | grep "^app_" | head -5
curl -s http://localhost:9187/metrics | grep "^pg_" | head -5
curl -s http://localhost:8080/metrics | grep "^container_" | head -5

# Test Prometheus scraping
curl -s http://localhost:9090/api/v1/targets | grep "health"
```

Expected output:
- ✅ All containers in "Up" status
- ✅ Metrics endpoints return data
- ✅ Prometheus shows all targets as "up"

## 📈 Performance Baselines

| Component | CPU | Memory | Normal Behavior |
|-----------|-----|--------|-----------------|
| Backend | 1-5% | 100-200MB | Low with spikes on requests |
| Database | 1-3% | 50-100MB | Steady with transaction bursts |
| Frontend | <1% | 30-50MB | Very low, static files |
| cAdvisor | 1-2% | 20-40MB | Constant monitoring overhead |
| Prometheus | 2-5% | 100-150MB | Increases with more metrics |
| Grafana | 1-3% | 50-100MB | Increases with dashboards |
| Jaeger | 1-2% | 50-80MB | Increases with trace volume |
| postgres_exporter | <1% | 10-20MB | Minimal overhead |

## 🛠 Troubleshooting

### cAdvisor not showing container metrics
**macOS Issue**: Some metrics are limited on Docker Desktop
**Solution**: Container-level metrics still work, but host-level may be limited

### Backend metrics not updating
```bash
# Check backend logs
docker compose logs backend --tail 50

# Verify psutil is installed
docker compose exec backend pip list | grep psutil

# Rebuild if needed
docker compose up -d --build backend
```

### Database metrics show zero connections
```bash
# Generate test data
./generate-metrics-data.sh

# Check connections
curl -s http://localhost:9187/metrics | grep numbackends
```

## 📖 Full Documentation

See `RESOURCE_MONITORING.md` for:
- Complete metric descriptions
- Alert rule examples
- Advanced queries
- Performance tuning tips
