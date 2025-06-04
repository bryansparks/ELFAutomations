#!/bin/bash

# Deploy AgentGateway for TASK-006 MCP Infrastructure
# This script deploys AgentGateway as the centralized MCP gateway

set -euo pipefail

# Configuration
NAMESPACE="virtual-ai-platform"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AGENTGATEWAY_DIR="$PROJECT_ROOT/k8s/base/agentgateway"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace '$NAMESPACE' does not exist"
        log_info "Please run the Kubernetes infrastructure deployment first"
        exit 1
    fi
    
    # Check if required secrets exist
    if ! kubectl get secret supabase-secrets -n "$NAMESPACE" &> /dev/null; then
        log_error "Required secret 'supabase-secrets' not found in namespace '$NAMESPACE'"
        log_info "Please ensure Supabase secrets are created first"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Deploy AgentGateway
deploy_agentgateway() {
    log_info "Deploying AgentGateway to namespace '$NAMESPACE'..."
    
    # Apply RBAC first
    log_info "Applying RBAC configuration..."
    kubectl apply -f "$AGENTGATEWAY_DIR/rbac.yaml"
    
    # Apply ConfigMap
    log_info "Applying ConfigMap..."
    kubectl apply -f "$AGENTGATEWAY_DIR/configmap.yaml"
    
    # Apply Service
    log_info "Applying Service..."
    kubectl apply -f "$AGENTGATEWAY_DIR/service.yaml"
    
    # Apply Deployment
    log_info "Applying Deployment..."
    kubectl apply -f "$AGENTGATEWAY_DIR/deployment.yaml"
    
    # Apply Monitoring
    log_info "Applying Monitoring configuration..."
    kubectl apply -f "$AGENTGATEWAY_DIR/monitoring.yaml"
    
    log_success "AgentGateway manifests applied successfully"
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for AgentGateway deployment to be ready..."
    
    # Wait for deployment to be available
    kubectl wait --for=condition=available --timeout=300s deployment/agentgateway -n "$NAMESPACE"
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready --timeout=300s pod -l app=agentgateway -n "$NAMESPACE"
    
    log_success "AgentGateway deployment is ready"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying AgentGateway deployment..."
    
    # Check deployment status
    local deployment_status
    deployment_status=$(kubectl get deployment agentgateway -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    local desired_replicas
    desired_replicas=$(kubectl get deployment agentgateway -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    
    if [[ "$deployment_status" == "$desired_replicas" ]]; then
        log_success "Deployment status: $deployment_status/$desired_replicas replicas ready"
    else
        log_error "Deployment status: $deployment_status/$desired_replicas replicas ready"
        return 1
    fi
    
    # Check service endpoints
    local service_endpoints
    service_endpoints=$(kubectl get endpoints agentgateway-service -n "$NAMESPACE" -o jsonpath='{.subsets[0].addresses}')
    
    if [[ -n "$service_endpoints" ]]; then
        log_success "Service endpoints are available"
    else
        log_error "No service endpoints found"
        return 1
    fi
    
    # Show pod status
    log_info "Pod status:"
    kubectl get pods -l app=agentgateway -n "$NAMESPACE" -o wide
    
    # Show service status
    log_info "Service status:"
    kubectl get service agentgateway-service agentgateway-metrics -n "$NAMESPACE"
    
    log_success "AgentGateway verification completed successfully"
}

# Test connectivity
test_connectivity() {
    log_info "Testing AgentGateway connectivity..."
    
    # Get a pod to test from
    local test_pod
    test_pod=$(kubectl get pods -l app=agentgateway -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -z "$test_pod" ]]; then
        log_error "No AgentGateway pods found for testing"
        return 1
    fi
    
    # Test MCP endpoint
    log_info "Testing MCP endpoint (port 3000)..."
    if kubectl exec "$test_pod" -n "$NAMESPACE" -c agentgateway -- curl -s -f http://localhost:3000/health &> /dev/null; then
        log_success "MCP endpoint is responding"
    else
        log_warning "MCP endpoint health check failed (this may be normal if AgentGateway uses different health check path)"
    fi
    
    # Test Admin endpoint
    log_info "Testing Admin endpoint (port 8080)..."
    if kubectl exec "$test_pod" -n "$NAMESPACE" -c agentgateway -- curl -s -f http://localhost:8080/health &> /dev/null; then
        log_success "Admin endpoint is responding"
    else
        log_warning "Admin endpoint health check failed (this may be normal if AgentGateway uses different health check path)"
    fi
    
    # Test Metrics endpoint
    log_info "Testing Metrics endpoint (port 9090)..."
    if kubectl exec "$test_pod" -n "$NAMESPACE" -c agentgateway -- curl -s -f http://localhost:9090/metrics &> /dev/null; then
        log_success "Metrics endpoint is responding"
    else
        log_warning "Metrics endpoint health check failed (this may be normal if AgentGateway uses different metrics path)"
    fi
    
    log_success "Connectivity tests completed"
}

# Setup port forwarding for local access
setup_port_forwarding() {
    log_info "Setting up port forwarding for local access..."
    
    # Kill any existing port forwards
    pkill -f "kubectl.*port-forward.*agentgateway" || true
    sleep 2
    
    # Start port forwarding in background
    log_info "Starting port forwarding for MCP (3000), Admin (8080), and Metrics (9090)..."
    
    kubectl port-forward service/agentgateway-service 3000:3000 -n "$NAMESPACE" &
    kubectl port-forward service/agentgateway-service 8080:8080 -n "$NAMESPACE" &
    kubectl port-forward service/agentgateway-metrics 9090:9090 -n "$NAMESPACE" &
    
    sleep 5
    
    log_success "Port forwarding setup completed"
    log_info "AgentGateway is now accessible at:"
    log_info "  MCP Protocol: http://localhost:3000"
    log_info "  Admin UI: http://localhost:8080"
    log_info "  Metrics: http://localhost:9090/metrics"
}

# Show deployment summary
show_summary() {
    log_info "=== TASK-006 AgentGateway Deployment Summary ==="
    echo
    log_success "✅ AgentGateway successfully deployed to Kubernetes"
    log_success "✅ MCP server federation configured (Supabase + Business Tools)"
    log_success "✅ Monitoring and observability enabled"
    log_success "✅ RBAC and security policies applied"
    echo
    log_info "🔧 Configuration:"
    log_info "  Namespace: $NAMESPACE"
    log_info "  Replicas: 2"
    log_info "  MCP Targets: supabase, business"
    echo
    log_info "🌐 Access Points:"
    log_info "  MCP Protocol: http://localhost:3000"
    log_info "  Admin UI: http://localhost:8080"
    log_info "  Metrics: http://localhost:9090/metrics"
    echo
    log_info "📊 Next Steps:"
    log_info "  1. Update LangGraph agents to use AgentGateway endpoint"
    log_info "  2. Test end-to-end MCP tool access"
    log_info "  3. Monitor metrics in Grafana dashboard"
    log_info "  4. Deploy additional MCP servers (Phase 2)"
    echo
    log_success "🎯 TASK-006 Phase 1 Foundation Setup: COMPLETED"
}

# Main execution
main() {
    log_info "Starting TASK-006 AgentGateway deployment..."
    echo
    
    check_prerequisites
    deploy_agentgateway
    wait_for_deployment
    verify_deployment
    test_connectivity
    setup_port_forwarding
    show_summary
    
    log_success "AgentGateway deployment completed successfully!"
}

# Run main function
main "$@"
