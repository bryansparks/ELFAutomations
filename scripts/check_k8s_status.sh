#!/bin/bash

# Virtual AI Company Platform - Kubernetes Status Check Script
# This script provides comprehensive status information for the deployed infrastructure

set -e

echo "🔍 Virtual AI Company Platform - Kubernetes Status Check"
echo "========================================================"
echo ""

# Check cluster connectivity
echo "🌐 Cluster Connectivity:"
if kubectl cluster-info &> /dev/null; then
    echo "  ✅ Kubernetes cluster is accessible"
    kubectl cluster-info | head -2
else
    echo "  ❌ Kubernetes cluster is not accessible"
    exit 1
fi
echo ""

# Check namespaces
echo "📁 Namespaces:"
kubectl get namespaces | grep -E "(virtual-ai|ingress)" || echo "  ⚠️  No Virtual AI namespaces found"
echo ""

# Check deployments across all Virtual AI namespaces
echo "🚀 Deployments Status:"
for namespace in virtual-ai-platform virtual-ai-agents virtual-ai-monitoring virtual-ai-data; do
    echo "  📦 Namespace: $namespace"
    deployments=$(kubectl get deployments -n $namespace --no-headers 2>/dev/null | wc -l)
    if [ $deployments -gt 0 ]; then
        kubectl get deployments -n $namespace
    else
        echo "    No deployments found"
    fi
    echo ""
done

# Check ingress controller
echo "🌐 Ingress Controller:"
kubectl get pods -n ingress-nginx
echo ""

# Check services
echo "🔗 Services:"
for namespace in virtual-ai-platform virtual-ai-agents virtual-ai-monitoring virtual-ai-data; do
    services=$(kubectl get services -n $namespace --no-headers 2>/dev/null | wc -l)
    if [ $services -gt 0 ]; then
        echo "  📦 Namespace: $namespace"
        kubectl get services -n $namespace
        echo ""
    fi
done

# Check ingress rules
echo "🔀 Ingress Rules:"
kubectl get ingress --all-namespaces
echo ""

# Check persistent volumes
echo "💾 Persistent Storage:"
kubectl get pvc --all-namespaces | grep -E "(virtual-ai|redis|prometheus|grafana)" || echo "  No PVCs found"
echo ""

# Check Custom Resource Definitions
echo "🤖 Custom Resource Definitions (kagent):"
kubectl get crd | grep kagent || echo "  No kagent CRDs found"
echo ""

# Check RBAC
echo "🔐 RBAC Configuration:"
echo "  Service Accounts:"
kubectl get serviceaccounts --all-namespaces | grep virtual-ai || echo "    No Virtual AI service accounts found"
echo ""
echo "  Cluster Roles:"
kubectl get clusterroles | grep virtual-ai || echo "    No Virtual AI cluster roles found"
echo ""

# Resource usage summary
echo "📊 Resource Usage Summary:"
echo "  Pods by namespace:"
for namespace in virtual-ai-platform virtual-ai-agents virtual-ai-monitoring virtual-ai-data ingress-nginx; do
    pod_count=$(kubectl get pods -n $namespace --no-headers 2>/dev/null | wc -l)
    if [ $pod_count -gt 0 ]; then
        running_pods=$(kubectl get pods -n $namespace --no-headers 2>/dev/null | grep Running | wc -l)
        echo "    $namespace: $running_pods/$pod_count running"
    fi
done
echo ""

# Health check
echo "🏥 Health Status:"
all_healthy=true

# Check if Redis is healthy
if kubectl get deployment redis -n virtual-ai-data &> /dev/null; then
    redis_ready=$(kubectl get deployment redis -n virtual-ai-data -o jsonpath='{.status.readyReplicas}')
    redis_desired=$(kubectl get deployment redis -n virtual-ai-data -o jsonpath='{.spec.replicas}')
    if [ "$redis_ready" = "$redis_desired" ]; then
        echo "  ✅ Redis: Healthy ($redis_ready/$redis_desired)"
    else
        echo "  ❌ Redis: Unhealthy ($redis_ready/$redis_desired)"
        all_healthy=false
    fi
else
    echo "  ⚠️  Redis: Not deployed"
fi

# Check if Prometheus is healthy
if kubectl get deployment prometheus -n virtual-ai-monitoring &> /dev/null; then
    prom_ready=$(kubectl get deployment prometheus -n virtual-ai-monitoring -o jsonpath='{.status.readyReplicas}')
    prom_desired=$(kubectl get deployment prometheus -n virtual-ai-monitoring -o jsonpath='{.spec.replicas}')
    if [ "$prom_ready" = "$prom_desired" ]; then
        echo "  ✅ Prometheus: Healthy ($prom_ready/$prom_desired)"
    else
        echo "  ❌ Prometheus: Unhealthy ($prom_ready/$prom_desired)"
        all_healthy=false
    fi
else
    echo "  ⚠️  Prometheus: Not deployed"
fi

# Check if Grafana is healthy
if kubectl get deployment grafana -n virtual-ai-monitoring &> /dev/null; then
    grafana_ready=$(kubectl get deployment grafana -n virtual-ai-monitoring -o jsonpath='{.status.readyReplicas}')
    grafana_desired=$(kubectl get deployment grafana -n virtual-ai-monitoring -o jsonpath='{.spec.replicas}')
    if [ "$grafana_ready" = "$grafana_desired" ]; then
        echo "  ✅ Grafana: Healthy ($grafana_ready/$grafana_desired)"
    else
        echo "  ❌ Grafana: Unhealthy ($grafana_ready/$grafana_desired)"
        all_healthy=false
    fi
else
    echo "  ⚠️  Grafana: Not deployed"
fi

# Check ingress controller
if kubectl get deployment ingress-nginx-controller -n ingress-nginx &> /dev/null; then
    ingress_ready=$(kubectl get deployment ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.readyReplicas}')
    ingress_desired=$(kubectl get deployment ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.replicas}')
    if [ "$ingress_ready" = "$ingress_desired" ]; then
        echo "  ✅ Ingress Controller: Healthy ($ingress_ready/$ingress_desired)"
    else
        echo "  ❌ Ingress Controller: Unhealthy ($ingress_ready/$ingress_desired)"
        all_healthy=false
    fi
else
    echo "  ⚠️  Ingress Controller: Not deployed"
fi

echo ""

# Overall status
if [ "$all_healthy" = true ]; then
    echo "🎉 Overall Status: HEALTHY - All components are running correctly"
    echo ""
    echo "🌐 Access Instructions:"
    echo "  1. Run 'minikube tunnel' in a separate terminal"
    echo "  2. Add these entries to your /etc/hosts file:"
    echo "     127.0.0.1 virtual-ai.local"
    echo "     127.0.0.1 monitoring.virtual-ai.local"
    echo "  3. Access services:"
    echo "     • Platform: http://virtual-ai.local"
    echo "     • Grafana: http://monitoring.virtual-ai.local/grafana (admin/admin)"
    echo "     • Prometheus: http://monitoring.virtual-ai.local/prometheus"
else
    echo "⚠️  Overall Status: DEGRADED - Some components need attention"
fi

echo ""
echo "📋 Quick Commands:"
echo "  • View all pods: kubectl get pods --all-namespaces"
echo "  • Check logs: kubectl logs -f deployment/<name> -n <namespace>"
echo "  • Port forward: kubectl port-forward svc/<service> <local-port>:<service-port> -n <namespace>"
echo "  • Delete all: kubectl delete -f k8s/base/"
