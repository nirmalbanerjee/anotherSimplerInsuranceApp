# 📊 Observability Quick Reference

## URLs
| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | None |
| **Jaeger** | http://localhost:16686 | None |
| **Backend API** | http://localhost:8000 | - |
| **Metrics Endpoint** | http://localhost:8000/metrics | - |
| **Frontend App** | http://localhost:3023 | - |

## Quick Commands

### Generate Test Data
```bash
./generate-metrics-data.sh
```

### View Metrics in Terminal
```bash
curl http://localhost:8000/metrics | grep http_requests_total
```

### Check Prometheus Targets
```bash
curl http://localhost:9090/api/v1/targets | jq
```

### Restart Services
```bash
docker compose restart grafana
docker compose restart prometheus
docker compose restart backend
```

## Prometheus Query Examples

Copy-paste these into Prometheus (http://localhost:9090):

**Request rate:**
```
rate(http_requests_total[5m])
```

**Total requests by endpoint:**
```
sum by(endpoint) (http_requests_total)
```

**Error rate percentage:**
```
sum(rate(http_requests_total{status=~"4..|5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m])) * 100
```

**Average response time:**
```
rate(http_request_duration_seconds_sum[5m]) 
/ 
rate(http_request_duration_seconds_count[5m])
```

**Login success rate:**
```
rate(auth_events_total{event_type="login_success"}[5m])
```

**Policy operations:**
```
sum by(operation) (policy_operations_total)
```

## Grafana Tips

1. **Access Dashboard**: ☰ Menu → Dashboards → "Insurance App Dashboard"
2. **Time Range**: Top-right corner (try "Last 5 minutes", "Last 1 hour")
3. **Refresh**: Dashboard auto-refreshes every 5 seconds
4. **Zoom**: Click & drag on any graph
5. **Panel Edit**: Click panel title → Edit
6. **Add Panel**: Click "Add" → "Visualization"
7. **Save Changes**: Click save icon (top-right)

## Metrics Available

### HTTP Metrics
- `http_requests_total{method, endpoint, status}` - Request counter
- `http_request_duration_seconds` - Latency histogram

### Business Metrics
- `auth_events_total{event_type, role}` - Auth events
- `policy_operations_total{operation, user_role}` - Policy ops

### System Metrics
- `python_gc_*` - Python garbage collection
- `process_*` - Process stats (CPU, memory)

## Troubleshooting

**No data in Grafana?**
1. Wait 30 seconds for first scrape
2. Generate traffic: `./generate-metrics-data.sh`
3. Check Prometheus targets: http://localhost:9090/targets

**Grafana login not working?**
```bash
docker compose logs grafana | grep password
```

**Prometheus not scraping?**
```bash
docker compose logs prometheus | grep backend
```

**Reset everything?**
```bash
docker compose down
docker volume rm anothersimplerinsuranceapp_grafana_data
docker compose up -d
```

## Next Steps
- [ ] Create custom dashboard panels
- [ ] Set up alerting rules
- [ ] Explore Jaeger traces
- [ ] Export dashboards for backup
- [ ] Add more business metrics

---
**Generated**: 21 Nov 2025  
**Docs**: See PROMETHEUS_GRAFANA_GUIDE.md for detailed guide
