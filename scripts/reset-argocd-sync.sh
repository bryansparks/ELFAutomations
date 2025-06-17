#!/bin/bash

# Reset ArgoCD Sync Script
# This script helps troubleshoot and reset ArgoCD sync issues

set -e

echo "======================================"
echo "ArgoCD Sync Reset & Troubleshooting"
echo "======================================"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Function to check ArgoCD health
check_argocd_health() {
    echo -e "\n📊 Checking ArgoCD health..."
    kubectl get pods -n argocd
    echo ""
}

# Function to check application status
check_app_status() {
    local app_name=$1
    echo -e "\n🔍 Checking application: $app_name"
    kubectl get application $app_name -n argocd -o wide || echo "Application $app_name not found"
    echo ""
}

# Function to force refresh
force_refresh() {
    local app_name=$1
    echo -e "\n🔄 Force refreshing $app_name..."
    kubectl patch application $app_name -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"true"}}}'
    sleep 2
}

# Function to hard refresh (delete cache)
hard_refresh() {
    local app_name=$1
    echo -e "\n🔥 Hard refresh for $app_name (clearing cache)..."
    # Get the repo server pod
    REPO_SERVER=$(kubectl get pods -n argocd -l app.kubernetes.io/component=repo-server -o jsonpath='{.items[0].metadata.name}')
    
    # Clear the repository cache
    kubectl exec -n argocd $REPO_SERVER -- rm -rf /tmp/git@github.com:bryansparks:ELFAutomations* || true
    
    # Force refresh
    force_refresh $app_name
}

# Function to sync application
sync_app() {
    local app_name=$1
    echo -e "\n🚀 Syncing $app_name..."
    kubectl patch application $app_name -n argocd --type merge -p '{"operation":{"sync":{"prune":true,"revision":"HEAD"}}}'
    
    # Wait for sync to start
    sleep 3
    
    # Check sync status
    echo "⏳ Waiting for sync to complete..."
    kubectl wait --for=condition=Synced=true application/$app_name -n argocd --timeout=300s || {
        echo "❌ Sync timeout or failed. Checking detailed status..."
        kubectl describe application $app_name -n argocd | tail -20
    }
}

# Function to completely reset an application
reset_app() {
    local app_name=$1
    echo -e "\n🔧 Completely resetting $app_name..."
    
    # Delete the application
    echo "Deleting application..."
    kubectl delete application $app_name -n argocd --wait=false || true
    
    # Wait a bit
    sleep 5
    
    # Recreate based on app name
    case $app_name in
        "elf-teams")
            echo "Recreating elf-teams application..."
            kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: elf-teams
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/bryansparks/ELFAutomations.git
    targetRevision: main
    path: k8s/teams
    directory:
      recurse: true
      include: '{*.yaml,**/*.yaml}'
  destination:
    server: https://kubernetes.default.svc
    namespace: elf-teams
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF
            ;;
        "elf-infrastructure")
            echo "Recreating elf-infrastructure application..."
            kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: elf-infrastructure
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/bryansparks/ELFAutomations.git
    targetRevision: HEAD
    path: k8s/infrastructure
  destination:
    server: https://kubernetes.default.svc
    namespace: elf-infrastructure
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF
            ;;
        *)
            echo "❌ Unknown application: $app_name"
            return 1
            ;;
    esac
    
    # Wait for application to be created
    sleep 5
    
    # Force sync
    sync_app $app_name
}

# Function to check Git connectivity
check_git_connectivity() {
    echo -e "\n🌐 Checking Git connectivity..."
    
    # Get repo server pod
    REPO_SERVER=$(kubectl get pods -n argocd -l app.kubernetes.io/component=repo-server -o jsonpath='{.items[0].metadata.name}')
    
    # Test git connectivity
    kubectl exec -n argocd $REPO_SERVER -- git ls-remote https://github.com/bryansparks/ELFAutomations.git HEAD || {
        echo "❌ Git connectivity failed!"
        echo "Checking DNS..."
        kubectl exec -n argocd $REPO_SERVER -- nslookup github.com
        return 1
    }
    
    echo "✅ Git connectivity OK"
}

# Function to check for common issues
diagnose_issues() {
    echo -e "\n🏥 Running diagnostics..."
    
    # Check ArgoCD namespace
    kubectl get namespace argocd &>/dev/null || {
        echo "❌ ArgoCD namespace not found!"
        return 1
    }
    
    # Check ArgoCD pods
    UNHEALTHY_PODS=$(kubectl get pods -n argocd -o json | jq -r '.items[] | select(.status.phase != "Running") | .metadata.name')
    if [ ! -z "$UNHEALTHY_PODS" ]; then
        echo "❌ Unhealthy ArgoCD pods found:"
        echo "$UNHEALTHY_PODS"
        echo ""
        echo "Attempting to restart unhealthy pods..."
        for pod in $UNHEALTHY_PODS; do
            kubectl delete pod $pod -n argocd
        done
    else
        echo "✅ All ArgoCD pods are healthy"
    fi
    
    # Check applications
    echo -e "\n📋 Current applications:"
    kubectl get applications -n argocd
    
    # Check for sync errors
    echo -e "\n⚠️  Applications with sync errors:"
    kubectl get applications -n argocd -o json | jq -r '.items[] | select(.status.sync.status != "Synced") | "\(.metadata.name): \(.status.sync.status)"'
}

# Main menu
show_menu() {
    echo -e "\n======================================"
    echo "Select an option:"
    echo "1. Quick diagnosis (check health & status)"
    echo "2. Force refresh all apps"
    echo "3. Hard refresh all apps (clear cache)"
    echo "4. Reset specific application"
    echo "5. Reset ALL applications"
    echo "6. Check Git connectivity"
    echo "7. Full system reset"
    echo "8. Exit"
    echo "======================================"
}

# Main logic
main() {
    while true; do
        show_menu
        read -p "Enter choice [1-8]: " choice
        
        case $choice in
            1)
                check_argocd_health
                diagnose_issues
                check_app_status "elf-teams"
                check_app_status "elf-infrastructure"
                ;;
            2)
                force_refresh "elf-teams"
                force_refresh "elf-infrastructure"
                ;;
            3)
                hard_refresh "elf-teams"
                hard_refresh "elf-infrastructure"
                ;;
            4)
                read -p "Enter application name (elf-teams or elf-infrastructure): " app_name
                reset_app "$app_name"
                ;;
            5)
                reset_app "elf-teams"
                reset_app "elf-infrastructure"
                ;;
            6)
                check_git_connectivity
                ;;
            7)
                echo "⚠️  This will completely reset ArgoCD applications!"
                read -p "Are you sure? (yes/no): " confirm
                if [ "$confirm" = "yes" ]; then
                    check_argocd_health
                    check_git_connectivity
                    reset_app "elf-teams"
                    reset_app "elf-infrastructure"
                    diagnose_issues
                fi
                ;;
            8)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo "Invalid choice!"
                ;;
        esac
        
        echo -e "\nPress Enter to continue..."
        read
    done
}

# Run main
main