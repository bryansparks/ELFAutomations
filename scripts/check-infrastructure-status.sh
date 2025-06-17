#!/bin/bash
# Check status of infrastructure components

echo "🔍 Checking ElfAutomations Infrastructure Status..."
echo ""

# Check ArgoCD app
echo "📱 ArgoCD Application Status:"
kubectl get app -n argocd elf-infrastructure 2>/dev/null || echo "❌ Infrastructure app not found. Run create-infrastructure-argocd-app.sh first."
echo ""

# Check namespace
echo "📦 Namespace Status:"
kubectl get ns elf-infrastructure 2>/dev/null || echo "❌ Namespace not found"
echo ""

# Check Neo4j
echo "🗄️ Neo4j Status:"
kubectl get pods -n elf-infrastructure -l app=neo4j 2>/dev/null || echo "❌ No Neo4j pods found"
echo ""

# Check services
echo "🌐 Services:"
kubectl get svc -n elf-infrastructure 2>/dev/null || echo "❌ No services found"
echo ""

# Check PVCs
echo "💾 Storage:"
kubectl get pvc -n elf-infrastructure 2>/dev/null || echo "❌ No PVCs found"
echo ""

# Get node IPs for access
if kubectl get svc -n elf-infrastructure neo4j-external &>/dev/null; then
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
    echo "🔗 Neo4j Access URLs:"
    echo "   Browser: http://$NODE_IP:30474"
    echo "   Bolt: bolt://$NODE_IP:30687"
fi
