#!/bin/bash

# Virtual AI Company Platform - Kubernetes Infrastructure Deployment Script
# This script deploys the complete Kubernetes base infrastructure for TASK-002

set -e

echo "🚀 Starting Virtual AI Company Platform Kubernetes Infrastructure Deployment"
echo "============================================================================"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if minikube is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster is not accessible. Please start minikube first."
    echo "   Run: minikube start"
    exit 1
fi

echo "✅ Kubernetes cluster is accessible"

# Deploy namespaces first
echo "📁 Creating namespaces..."
kubectl apply -f k8s/base/namespaces.yaml
echo "✅ Namespaces created"

# Deploy RBAC policies
echo "🔐 Setting up RBAC policies..."
kubectl apply -f k8s/base/rbac.yaml
echo "✅ RBAC policies configured"

# Deploy Redis cluster
echo "💾 Deploying Redis cluster..."
kubectl apply -f k8s/base/redis.yaml
echo "✅ Redis cluster deployed"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/redis -n virtual-ai-data
echo "✅ Redis is ready"

# Deploy Prometheus monitoring
echo "📊 Deploying Prometheus monitoring..."
kubectl apply -f k8s/base/prometheus.yaml
echo "✅ Prometheus deployed"

# Wait for Prometheus to be ready
echo "⏳ Waiting for Prometheus to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n virtual-ai-monitoring
echo "✅ Prometheus is ready"

# Deploy Grafana dashboards
echo "📈 Deploying Grafana dashboards..."
kubectl apply -f k8s/base/grafana.yaml
echo "✅ Grafana deployed"

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n virtual-ai-monitoring
echo "✅ Grafana is ready"

# Enable ingress addon if not already enabled
echo "🌐 Enabling ingress controller..."
minikube addons enable ingress
echo "✅ Ingress addon enabled"

# Wait for ingress controller to be ready
echo "⏳ Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=300s
echo "✅ Ingress controller is ready"

# Deploy ingress rules
echo "🔗 Deploying ingress rules..."
kubectl apply -f k8s/base/ingress.yaml
echo "✅ Ingress rules deployed"

# Deploy kagent CRDs
echo "🤖 Deploying kagent Custom Resource Definitions..."
kubectl apply -f k8s/base/kagent-crd.yaml
echo "✅ kagent CRDs deployed"

# Check overall status
echo ""
echo "🎉 Kubernetes Infrastructure Deployment Complete!"
echo "=================================================="
echo ""
echo "📋 Deployment Summary:"
echo "  ✅ Namespaces: virtual-ai-platform, virtual-ai-agents, virtual-ai-monitoring, virtual-ai-data"
echo "  ✅ RBAC: Service accounts and role bindings configured"
echo "  ✅ Redis: Caching cluster with persistent storage"
echo "  ✅ Prometheus: Metrics collection and monitoring"
echo "  ✅ Grafana: Dashboard and visualization"
echo "  ✅ Ingress: External access routing"
echo "  ✅ kagent: Custom resources for AI agent management"
echo ""
echo "🔍 Cluster Status:"
kubectl get pods --all-namespaces | grep -E "(virtual-ai|ingress)"
echo ""
echo "🌐 Access Information:"
echo "  • To access services locally, run: minikube tunnel"
echo "  • Grafana will be available at: http://monitoring.virtual-ai.local/grafana"
echo "  • Prometheus will be available at: http://monitoring.virtual-ai.local/prometheus"
echo "  • Platform dashboard will be available at: http://virtual-ai.local"
echo ""
echo "📝 Next Steps:"
echo "  1. Deploy web dashboard: kubectl apply -f k8s/base/web-deployment.yaml"
echo "  2. Deploy AI agents using kagent controller"
echo "  3. Configure secrets for Supabase and LLM APIs"
echo "  4. Run minikube tunnel for external access"
echo ""
echo "✨ TASK-002 Kubernetes Base Infrastructure: COMPLETE"
