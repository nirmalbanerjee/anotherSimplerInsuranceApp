# Resource Monitoring Guide

This guide explains the comprehensive resource monitoring setup for the Insurance App running in Docker.

## Monitoring Components

### 1. **cAdvisor** (Container Advisor)
- **Port**: 8080
- **Purpose**: Collects resource metrics from all Docker containers
- **Metrics Collected**:
  - CPU usage per container
  - Memory usage and limits
  - Network I/O (bytes sent/received)
  - Disk I/O (read/write operations)
  - Filesystem usage

### 2. **PostgreSQL Exporter**
- **Port**: 9187
- **Purpose**: Monitors PostgreSQL database performance
- **Metrics Collected**:
  - Active database connections (`pg_stat_database_numbackends`)
  - Transaction rates (commits/rollbacks per second)
  - Database size in bytes
  - Query execution statistics
  - Table and index sizes
  - Lock statistics

### 3. **Prometheus Process Collector** (Backend App)
- **Purpose**: Application-level resource monitoring
- **Metrics Collected**:
  - `process_cpu_seconds_total` - Total CPU time
  - `process_resident_memory_bytes` - Physical memory used
  - `process_virtual_memory_bytes` - Virtual memory used
  - `process_open_fds` - Number of open file descriptors
  - `python_gc_collections_total` - Python garbage collection stats
  - `app_cpu_usage_percent` - Real-time CPU percentage
  - `app_memory_usage_bytes` - Real-time memory usage
  - `app_open_files_count` - Open file descriptor count

## Accessing Monitoring Tools

| Tool | URL | Credentials |
|------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | None |
| **cAdvisor** | http://localhost:8080 | None |
| **Jaeger** | http://localhost:16686 | None |

## Grafana Dashboards

### Resource Monitoring Dashboard
Pre-configured dashboard with the following panels:

1. **Container CPU Usage** - CPU utilization for all containers
2. **Container Memory Usage** - Memory consumption per container
3. **Backend App CPU Usage** - Gauge showing Python app CPU%
4. **Backend App Memory Usage** - Gauge showing Python app memory
5. **Database Connections** - Active PostgreSQL connections
6. **Database Transaction Rate** - Commits and rollbacks per second
7. **Network I/O** - Network traffic for all containers
8. **Disk I/O** - Disk read/write operations
9. **Python GC Collections** - Garbage collection frequency
10. **Open File Descriptors** - Number of open files
11. **Database Size** - Total database size in MB

## Example Prometheus Queries

### Container Metrics
```promql
# CPU usage per container (percentage)
rate(container_cpu_usage_seconds_total{name=~"anothersimplerinsuranceapp.*"}[5m]) * 100

# Memory usage per container (MB)
container_memory_usage_bytes{name=~"anothersimplerinsuranceapp.*"} / 1024 / 1024

# Network receive rate (KB/s)
rate(container_network_receive_bytes_total{name=~"anothersimplerinsuranceapp.*"}[5m]) / 1024
```

### Database Metrics
```promql
# Active connections
pg_stat_database_numbackends{datname="insurance"}

# Transaction commit rate
rate(pg_stat_database_xact_commit{datname="insurance"}[5m])

# Database size (MB)
pg_database_size_bytes{datname="insurance"} / 1024 / 1024
```

### Application Metrics
```promql
# App CPU usage
app_cpu_usage_percent

# App memory usage (MB)
app_memory_usage_bytes / 1024 / 1024

# Python garbage collections
rate(python_gc_collections_total[5m])
```

## Setting Up Alerts (Optional)

You can add alert rules to Prometheus for critical conditions:

```yaml
# Example alert rules (add to prometheus.yml)
groups:
  - name: resource_alerts
    interval: 30s
    rules:
      - alert: HighCPUUsage
        expr: app_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          
      - alert: HighMemoryUsage
        expr: app_memory_usage_bytes > 536870912  # 512MB
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          
      - alert: HighDatabaseConnections
        expr: pg_stat_database_numbackends{datname="insurance"} > 50
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Too many database connections"
```

## Troubleshooting

### cAdvisor not showing metrics
- **Issue**: cAdvisor requires access to Docker socket
- **Solution**: Ensure volumes are correctly mounted in docker-compose.yml
- **macOS Note**: Some metrics may be limited on macOS Docker Desktop

### PostgreSQL Exporter connection errors
- **Issue**: Cannot connect to database
- **Solution**: Check `DATA_SOURCE_NAME` environment variable format
- **Format**: `postgresql://user:password@host:port/database?sslmode=disable`

### Missing Python process metrics
- **Issue**: `process_*` metrics not appearing
- **Solution**: Ensure `psutil` is installed in backend container
- **Fix**: Rebuild backend with `docker compose up -d --build backend`

## Performance Baselines

Typical resource usage for the Insurance App:

| Component | CPU | Memory | Description |
|-----------|-----|--------|-------------|
| Backend | 1-5% | 100-200MB | Normal operation |
| Database | 1-3% | 50-100MB | Light load |
| Frontend | <1% | 30-50MB | Serving static files |
| Prometheus | 2-5% | 100-150MB | Scraping 3 targets |
| Grafana | 1-3% | 50-100MB | 1-2 active dashboards |

## Log Aggregation

Backend logs are available at:
- **Location**: `backend/logs/app.log`
- **Format**: JSON structured logs
- **Fields**: timestamp, level, message, request_id, username, duration_ms

Example log query:
```bash
# View recent errors
docker compose logs backend | grep ERROR

# Follow backend logs
docker compose logs -f backend
```

## Next Steps

1. **Create Custom Dashboards**: Use Grafana Explore to build custom views
2. **Set Up Alerts**: Configure notification channels (email, Slack)
3. **Export Dashboards**: Save custom dashboards for version control
4. **Optimize Queries**: Reduce cardinality for better performance
