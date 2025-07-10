#!/bin/bash
# Deploy Neo4j to K3s cluster

set -e

echo "🚀 Deploying Neo4j to K3s cluster..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check cluster connection
echo "📡 Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to cluster"

# Create namespace if it doesn't exist
echo "📦 Creating namespace..."
kubectl create namespace elf-infrastructure --dry-run=client -o yaml | kubectl apply -f -

# Apply Neo4j manifests
echo "🔧 Applying Neo4j manifests..."
kubectl apply -k k8s/infrastructure/neo4j/

# Wait for deployment
echo "⏳ Waiting for Neo4j deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/neo4j -n elf-infrastructure

# Get pod status
echo "📊 Pod status:"
kubectl get pods -n elf-infrastructure -l app=neo4j

# Get service info
echo "🌐 Service information:"
kubectl get svc -n elf-infrastructure -l app=neo4j

# Get node IP for external access
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
echo ""
echo "✅ Neo4j deployed successfully!"
echo ""
echo "📍 Access Neo4j:"
echo "   Browser UI: http://$NODE_IP:30474"
echo "   Bolt URL: bolt://$NODE_IP:30687"
echo "   Username: neo4j"
echo "   Password: elfautomations2025"
echo ""
echo "🔐 IMPORTANT: Change the default password in production!"
echo ""
echo "🧪 Test connection with:"
echo "   python scripts/test_neo4j_connection.py --uri bolt://$NODE_IP:30687"
