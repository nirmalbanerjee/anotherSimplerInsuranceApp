#!/bin/bash

echo "🚀 Generating sample data for Prometheus & Grafana..."
echo ""

# Generate some successful registrations
echo "📝 Creating users..."
for i in {1..5}; do
    curl -s -X POST http://localhost:8000/register \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"user$i\",\"password\":\"pass123\",\"role\":\"user\"}" > /dev/null
    echo "  ✓ Created user$i"
    sleep 0.5
done

# Create an admin
curl -s -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"admin123","role":"admin"}' > /dev/null
echo "  ✓ Created admin1"

echo ""
echo "🔐 Testing failed logins..."
for i in {1..3}; do
    curl -s -X POST http://localhost:8000/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d 'username=wronguser&password=wrongpass' > /dev/null
    echo "  ✗ Failed login attempt $i"
    sleep 0.3
done

echo ""
echo "📋 Creating policies..."

# Get token for a user
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=user1&password=pass123' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Create some policies
for i in {1..3}; do
    curl -s -X POST http://localhost:8000/policies \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "{\"name\":\"Policy $i\",\"details\":\"Auto-generated test policy\"}" > /dev/null
    echo "  ✓ Created Policy $i"
    sleep 0.3
done

# List policies (generates list metric)
curl -s -X GET http://localhost:8000/policies \
  -H "Authorization: Bearer $TOKEN" > /dev/null
echo "  ✓ Listed policies"

echo ""
echo "✅ Data generation complete!"
echo ""
echo "Now check your dashboards:"
echo "  📊 Grafana: http://localhost:3001 (admin/admin)"
echo "  🔍 Prometheus: http://localhost:9090"
echo "  📈 Metrics endpoint: http://localhost:8000/metrics"
echo ""
echo "💡 Tip: Run this script again to generate more data!"
