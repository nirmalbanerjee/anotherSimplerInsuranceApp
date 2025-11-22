# Quick Fix: Viewing Metrics in Grafana

## Problem Solved! ✅

The datasource is now configured. Here's how to view your metrics:

## Step 1: Login to Grafana

1. Go to: **http://localhost:3001**
2. Login with:
   - Username: `admin`
   - Password: `admin`
3. Skip the password change (click "Skip")

## Step 2: Verify Prometheus Datasource

1. Click ☰ menu (top-left)
2. Go to **Connections** → **Data sources**
3. You should see **Prometheus** listed
4. Click on it to verify it's connected to `http://prometheus:9090`

## Step 3: Explore Metrics Directly

The easiest way to see your data:

1. Click ☰ menu → **Explore**
2. Make sure "Prometheus" is selected as the datasource (top dropdown)
3. Try these queries in the query box:

**Total Requests:**
```
http_requests_total
```

**Request Rate:**
```
rate(http_requests_total[5m])
```

**Requests by Endpoint:**
```
sum by(endpoint) (http_requests_total)
```

**Auth Events:**
```
auth_events_total
```

**Policy Operations:**
```
policy_operations_total
```

4. Click **Run query** button
5. You'll see the data!

## Step 4: Create a Simple Dashboard (Manual)

1. Click ☰ menu → **Dashboards**
2. Click **New** → **New Dashboard**
3. Click **+ Add visualization**
4. Select **Prometheus** datasource
5. In the query box, enter: `sum(http_requests_total)`
6. Click **Run queries**
7. You should see your data!
8. Click **Apply** (top-right)
9. Click **Save dashboard** icon (top-right)
10. Name it "Insurance App Dashboard"
11. Click **Save**

## Step 5: Add More Panels

Click **Add** → **Visualization** and try these queries:

**Panel 1 - Request Rate:**
```
rate(http_requests_total[5m])
```
Legend: `{{method}} {{endpoint}} - {{status}}`

**Panel 2 - Requests by Status (Pie Chart):**
```
sum by(status) (http_requests_total)
```
Change visualization type to "Pie chart"

**Panel 3 - Auth Events:**
```
sum by(event_type) (auth_events_total)
```

**Panel 4 - Policy Operations:**
```
sum by(operation) (policy_operations_total)
```

## Quick Prometheus Queries

You can also view metrics directly in Prometheus:

1. Go to: **http://localhost:9090**
2. Enter any of the queries above
3. Click **Execute**
4. Switch to **Graph** tab to see visualization

## Generate More Data

Run this to create traffic:
```bash
./generate-metrics-data.sh
```

Or just use your app at http://localhost:3023!

## Troubleshooting

**Still no data?**
1. Check Prometheus is scraping: http://localhost:9090/targets
   - Should show "UP" for backend
2. Verify metrics endpoint: http://localhost:8000/metrics
3. Generate traffic: visit http://localhost:3023
4. Wait 15-30 seconds for Prometheus to scrape

**Can't login to Grafana?**
- Username: `admin`
- Password: `admin`
- If changed, reset: `docker volume rm anothersimplerinsuranceapp_grafana_data && docker compose up -d grafana`

## Next Steps

- Explore other Prometheus queries
- Create custom dashboard panels
- Set up alerting rules
- Check Jaeger for traces: http://localhost:16686

Happy monitoring! 📊
