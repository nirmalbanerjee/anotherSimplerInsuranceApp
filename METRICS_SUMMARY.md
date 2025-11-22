# Insurance App Metrics Summary

## 🎯 Available Metrics Overview

This document provides a quick reference of ALL metrics available for monitoring the Insurance App.

---

## 📦 Container Metrics (cAdvisor - Port 8080)

### CPU Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `container_cpu_usage_seconds_total` | Total CPU time consumed | Counter |
| `container_cpu_user_seconds_total` | User CPU time | Counter |
| `container_cpu_system_seconds_total` | System CPU time | Counter |

### Memory Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `container_memory_usage_bytes` | Current memory usage | Gauge |
| `container_memory_max_usage_bytes` | Maximum memory usage | Gauge |
| `container_memory_cache` | Cache memory | Gauge |
| `container_memory_rss` | Resident set size | Gauge |
| `container_memory_swap` | Swap usage | Gauge |

### Network Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `container_network_receive_bytes_total` | Total bytes received | Counter |
| `container_network_transmit_bytes_total` | Total bytes transmitted | Counter |
| `container_network_receive_packets_total` | Total packets received | Counter |
| `container_network_transmit_packets_total` | Total packets transmitted | Counter |
| `container_network_receive_errors_total` | Receive errors | Counter |
| `container_network_transmit_errors_total` | Transmit errors | Counter |

### Disk I/O Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `container_fs_reads_bytes_total` | Bytes read from disk | Counter |
| `container_fs_writes_bytes_total` | Bytes written to disk | Counter |
| `container_fs_reads_total` | Number of read operations | Counter |
| `container_fs_writes_total` | Number of write operations | Counter |

---

## 🗄️ Database Metrics (PostgreSQL Exporter - Port 9187)

### Connection Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `pg_stat_database_numbackends` | Active connections | Gauge |
| `pg_settings_max_connections` | Maximum allowed connections | Gauge |
| `pg_stat_activity_count` | Current activity count | Gauge |

### Transaction Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `pg_stat_database_xact_commit` | Total committed transactions | Counter |
| `pg_stat_database_xact_rollback` | Total rolled back transactions | Counter |
| `pg_stat_database_tup_inserted` | Rows inserted | Counter |
| `pg_stat_database_tup_updated` | Rows updated | Counter |
| `pg_stat_database_tup_deleted` | Rows deleted | Counter |
| `pg_stat_database_tup_fetched` | Rows fetched | Counter |

### Database Size Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `pg_database_size_bytes` | Total database size | Gauge |
| `pg_stat_database_blks_read` | Disk blocks read | Counter |
| `pg_stat_database_blks_hit` | Disk blocks in cache | Counter |

### Performance Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `pg_stat_database_deadlocks` | Deadlock count | Counter |
| `pg_stat_database_conflicts` | Query conflicts | Counter |
| `pg_stat_database_temp_bytes` | Temporary file bytes | Counter |

---

## 🐍 Backend Application Metrics (Port 8000)

### Custom Application Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `app_cpu_usage_percent` | Real-time CPU usage % | Gauge |
| `app_memory_usage_bytes` | Real-time memory usage | Gauge |
| `app_open_files_count` | Open file descriptors | Gauge |

### HTTP Request Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `http_requests_total` | Total HTTP requests (method, endpoint, status) | Counter |
| `http_request_duration_seconds` | Request duration histogram | Histogram |

### Authentication Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `auth_events_total` | Auth events (event_type, role) | Counter |

### Policy Operations Metrics
| Metric | Description | Type |
|--------|-------------|------|
| `policy_operations_total` | Policy CRUD operations (operation, user_role) | Counter |

### Process Metrics (Automatic)
| Metric | Description | Type |
|--------|-------------|------|
| `process_cpu_seconds_total` | Total CPU time of process | Counter |
| `process_resident_memory_bytes` | Physical memory (RSS) | Gauge |
| `process_virtual_memory_bytes` | Virtual memory | Gauge |
| `process_open_fds` | Open file descriptors | Gauge |
| `process_max_fds` | Maximum file descriptors | Gauge |
| `process_start_time_seconds` | Process start time | Gauge |

### Python GC Metrics (Automatic)
| Metric | Description | Type |
|--------|-------------|------|
| `python_gc_collections_total` | GC collections by generation | Counter |
| `python_gc_objects_collected_total` | Objects collected by GC | Counter |
| `python_gc_objects_uncollectable_total` | Uncollectable objects | Counter |
| `python_info` | Python version info | Info |

---

## 📊 Example Prometheus Queries

### Top CPU Consuming Containers
```promql
topk(5, rate(container_cpu_usage_seconds_total{name=~"anothersimplerinsuranceapp.*"}[5m]) * 100)
```

### Memory Usage Percentage
```promql
(container_memory_usage_bytes{name=~"anothersimplerinsuranceapp.*"} / container_spec_memory_limit_bytes) * 100
```

### Database Cache Hit Ratio
```promql
(pg_stat_database_blks_hit{datname="insurance"} / 
 (pg_stat_database_blks_hit{datname="insurance"} + pg_stat_database_blks_read{datname="insurance"})) * 100
```

### Request Rate (requests/second)
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

### Failed Login Rate
```promql
rate(auth_events_total{event_type="login_failed"}[5m])
```

### Average Request Duration (P95)
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Database Connections vs Limit
```promql
(pg_stat_database_numbackends{datname="insurance"} / pg_settings_max_connections) * 100
```

### Python Memory Growth Rate
```promql
deriv(process_resident_memory_bytes[5m])
```

---

## 🎨 Grafana Dashboard Panels

### Recommended Dashboard Layout

**Row 1: Container Overview**
- Panel 1: Container CPU Usage (Time Series)
- Panel 2: Container Memory Usage (Time Series)

**Row 2: Application Metrics**
- Panel 3: Backend CPU % (Gauge)
- Panel 4: Backend Memory MB (Gauge)
- Panel 5: Request Rate (Graph)
- Panel 6: Request Duration P95 (Graph)

**Row 3: Database Performance**
- Panel 7: DB Connections (Time Series)
- Panel 8: Transaction Rate (Time Series)
- Panel 9: Cache Hit Ratio (Stat)
- Panel 10: DB Size (Stat)

**Row 4: Network & I/O**
- Panel 11: Network I/O (Time Series)
- Panel 12: Disk I/O (Time Series)

**Row 5: Application Details**
- Panel 13: Auth Events (Graph)
- Panel 14: Policy Operations (Graph)
- Panel 15: Python GC Rate (Graph)
- Panel 16: Open File Descriptors (Stat)

---

## 🔔 Suggested Alerts

### Critical Alerts
```yaml
- High CPU Usage: app_cpu_usage_percent > 80 for 5m
- High Memory: app_memory_usage_bytes > 512MB for 5m
- DB Connections: pg_stat_database_numbackends > 50 for 2m
- High Error Rate: rate(http_requests_total{status=~"5.."}[5m]) > 1
```

### Warning Alerts
```yaml
- Moderate CPU: app_cpu_usage_percent > 50 for 10m
- Container Memory: container_memory_usage_bytes > 500MB
- Failed Logins: rate(auth_events_total{event_type="login_failed"}[5m]) > 0.5
- DB Deadlocks: increase(pg_stat_database_deadlocks[1m]) > 0
```

---

## 📍 Access Points Summary

| Component | URL | Purpose |
|-----------|-----|---------|
| **Grafana** | http://localhost:3001 | Dashboards & Visualization |
| **Prometheus** | http://localhost:9090 | Metrics Storage & Query |
| **cAdvisor** | http://localhost:8080 | Container Metrics UI |
| **Backend Metrics** | http://localhost:8000/metrics | Application Metrics |
| **DB Exporter** | http://localhost:9187/metrics | PostgreSQL Metrics |
| **Jaeger** | http://localhost:16686 | Distributed Tracing |
| **Frontend** | http://localhost:3023 | Application UI |

---

## 🔧 Metrics Collection Intervals

- **Prometheus Scrape Interval**: 15 seconds
- **Evaluation Interval**: 15 seconds
- **cAdvisor Update**: Real-time
- **PostgreSQL Exporter**: On scrape
- **Backend Metrics**: On request to /metrics endpoint
- **Grafana Refresh**: Configurable (default 10s for dashboards)

---

## 📚 Metric Types Reference

- **Counter**: Monotonically increasing value (resets on restart)
- **Gauge**: Value that can go up or down
- **Histogram**: Bucketed observations (e.g., request durations)
- **Summary**: Similar to histogram but calculated client-side
- **Info**: Metadata about the system

---

Generated: $(date)
Version: 1.0
