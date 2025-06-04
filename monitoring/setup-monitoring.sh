#!/bin/bash

# Setup monitoring for Virtual AI Company Platform
set -e

echo "🔧 Setting up monitoring for Virtual AI Company Platform..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed"
    exit 1
fi

# Check if monitoring namespace exists
if ! kubectl get namespace virtual-ai-monitoring &> /dev/null; then
    echo "❌ Monitoring namespace 'virtual-ai-monitoring' not found"
    echo "Please ensure Prometheus and Grafana are deployed first"
    exit 1
fi

# Get Grafana admin password
echo "🔍 Getting Grafana admin password..."
GRAFANA_PASSWORD=$(kubectl get secret -n virtual-ai-monitoring grafana-admin-secret -o jsonpath="{.data.admin-password}" | base64 --decode)
echo "📝 Grafana admin password: $GRAFANA_PASSWORD"

# Wait for port forwarding to be available
echo "⏳ Waiting for Grafana to be accessible..."
sleep 5

# Import dashboard to Grafana
echo "📊 Importing Virtual AI Company Platform dashboard to Grafana..."

# Create datasource first (Prometheus)
curl -X POST \
  -H "Content-Type: application/json" \
  -u "admin:$GRAFANA_PASSWORD" \
  -d '{
    "name": "prometheus",
    "type": "prometheus",
    "url": "http://prometheus-service:9090",
    "access": "proxy",
    "isDefault": true
  }' \
  http://localhost:3000/api/datasources 2>/dev/null || echo "Datasource may already exist"

# Import the dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -u "admin:$GRAFANA_PASSWORD" \
  -d @monitoring/grafana-dashboards/virtual-ai-company-platform.json \
  http://localhost:3000/api/dashboards/db

echo "✅ Dashboard imported successfully!"

# Update Prometheus configuration
echo "🔧 Updating Prometheus configuration..."

# Create a ConfigMap with our custom Prometheus config
kubectl create configmap prometheus-config \
  --from-file=prometheus.yml=monitoring/prometheus-config.yml \
  -n virtual-ai-monitoring \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart Prometheus to pick up new config
echo "🔄 Restarting Prometheus to apply new configuration..."
kubectl rollout restart deployment/prometheus -n virtual-ai-monitoring

echo "✅ Monitoring setup complete!"
echo ""
echo "🎯 Access points:"
echo "   📊 Grafana: http://localhost:3000 (admin/$GRAFANA_PASSWORD)"
echo "   📈 Prometheus: http://localhost:9090"
echo "   🌐 Virtual AI Platform: http://localhost:8080"
echo "   📊 Platform Metrics: http://localhost:8080/metrics"
echo ""
echo "🎉 Virtual AI Company Platform monitoring is now fully configured!"
