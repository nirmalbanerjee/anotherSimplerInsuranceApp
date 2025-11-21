# Troubleshooting Observability Stack

## Issue: Prometheus not accessible (http://localhost:9090)

### Possible Causes & Solutions:

### 1. Docker Not Installed
**Symptom**: `docker: command not found`

**Solution**:
```bash
# macOS - Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Or use Homebrew
brew install --cask docker

# After install, start Docker Desktop app
```

### 2. Docker Compose Not Running
**Check**:
```bash
docker compose ps
# Should show: backend, frontend, db, jaeger, prometheus, grafana
```

**Solution**:
```bash
# Start services
docker compose up -d

# Check logs if services fail
docker compose logs prometheus
docker compose logs grafana
```

### 3. Port Already in Use
**Symptom**: Container starts but port not accessible

**Check**:
```bash
lsof -i :9090  # Check what's using Prometheus port
lsof -i :3001  # Check Grafana port
```

**Solution**:
```bash
# Kill process using port
kill -9 <PID>

# Or change port in docker-compose.yml
# prometheus:
#   ports:
#     - "9091:9090"  # Changed to 9091
```

### 4. Container Failed to Start
**Check**:
```bash
docker compose ps
# Look for "Exit" status

docker compose logs prometheus
# Look for error messages
```

**Common Issues**:
- **Volume permission errors**: `sudo chown -R $(whoami) prometheus_data grafana_data`
- **Config file errors**: Check `prometheus.yml` syntax
- **Port conflicts**: See solution #3

### 5. prometheus.yml Missing or Invalid
**Solution**:
```bash
# Verify file exists
cat prometheus.yml

# Should contain:
# global:
#   scrape_interval: 15s
# scrape_configs:
#   - job_name: 'insurance-backend'
#     static_configs:
#       - targets: ['backend:8000']

# Restart after fixing
docker compose restart prometheus
```

---

## Issue: Grafana Port Conflict (was on 3000, frontend also on 3000)

### ✅ FIXED
Grafana has been moved to **port 3001** to avoid conflict.

**Updated URLs**:
- Frontend: http://localhost:3023 (React app)
- Grafana: http://localhost:3001 (observability dashboard)

### If Still Having Issues:
```bash
# Check what's on port 3001
lsof -i :3001

# Restart Grafana
docker compose restart grafana

# View logs
docker compose logs grafana
```

---

## Complete Reset (Nuclear Option)

If nothing works:
```bash
# Stop all containers
docker compose down -v

# Remove all data
rm -rf prometheus_data grafana_data

# Rebuild and start fresh
docker compose build --no-cache
docker compose up -d

# Wait 30 seconds for services to start
sleep 30

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy  # Prometheus health
```

---

## Verification Checklist

Run these commands to verify everything:

```bash
# 1. Docker running?
docker ps

# 2. All services up?
docker compose ps
# Expected: 6 services (db, backend, frontend, jaeger, prometheus, grafana)

# 3. Prometheus accessible?
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# 4. Prometheus scraping backend?
curl http://localhost:9090/api/v1/targets
# Look for: "insurance-backend" with state "up"

# 5. Backend metrics available?
curl http://localhost:8000/metrics
# Should return Prometheus format metrics

# 6. Grafana accessible?
curl -I http://localhost:3001
# Expected: HTTP/1.1 302 Found (redirect to login)

# 7. Jaeger accessible?
curl -I http://localhost:16686
# Expected: HTTP/1.1 200 OK
```

---

## Port Summary (Updated)

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3023 | http://localhost:3023 |
| Backend | 8000 | http://localhost:8000 |
| Postgres | 5432 | localhost:5432 |
| Jaeger UI | 16686 | http://localhost:16686 |
| Jaeger OTLP | 4317 | grpc://localhost:4317 |
| Prometheus | 9090 | http://localhost:9090 |
| **Grafana** | **3001** | **http://localhost:3001** ⚠️ Changed from 3000 |

---

## Running Without Docker (Alternative)

If Docker is not available, you can run locally:

### Backend Only (No Observability)
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run backend
cd backend && uvicorn main:app --reload

# Access:
# - API: http://localhost:8000/docs
# - Metrics: http://localhost:8000/metrics
# - Logs: backend/logs/app.log
```

### With Standalone Prometheus (Mac/Linux)
```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.darwin-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Copy config
cp /path/to/project/prometheus.yml .

# Edit targets to use localhost
sed -i '' 's/backend:8000/localhost:8000/' prometheus.yml

# Run
./prometheus --config.file=prometheus.yml

# Access: http://localhost:9090
```

---

## Getting Help

If issues persist, collect this info:
```bash
# System info
uname -a
docker --version
docker compose version

# Service status
docker compose ps
docker compose logs --tail=50

# Port usage
lsof -i :8000 -i :9090 -i :3001 -i :16686

# Paste output when asking for help
```
