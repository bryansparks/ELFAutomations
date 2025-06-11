#!/bin/bash
#
# Deploy to OrbStack + ArgoCD
#
# This script handles the specific setup where:
# 1. OrbStack runs K8s locally on Mac
# 2. ArgoCD watches the GitHub repo at path: k8s/teams
# 3. Images are loaded locally (no registry)

set -e

echo "🚀 ElfAutomations Deployment to OrbStack + ArgoCD"
echo "================================================"
echo ""

# Step 1: Build Docker images locally
echo "📦 Step 1: Building Docker images locally..."
echo ""

# Executive Team
if [ -d "teams/executive-team" ]; then
    echo "Building executive-team..."
    cd teams/executive-team

    # Make deployable
    python make-deployable-team.py

    # Build image locally (no registry prefix!)
    docker build -t elf-automations/executive-team:latest .

    echo "✅ Image built: elf-automations/executive-team:latest"
    cd ../..
fi

# Step 2: Copy K8s manifests to ArgoCD-watched directory
echo ""
echo "📝 Step 2: Copying manifests to k8s/teams/..."
echo ""

# Create directory if it doesn't exist
mkdir -p k8s/teams/executive-team

# Copy manifests from new team structure to ArgoCD location
if [ -d "teams/executive-team/k8s" ]; then
    cp teams/executive-team/k8s/*.yaml k8s/teams/executive-team/
    echo "✅ Copied manifests to k8s/teams/executive-team/"
fi

# Step 3: Update image references for local usage
echo ""
echo "🔧 Step 3: Updating manifests for local images..."
echo ""

# Update deployment.yaml to use local image with imagePullPolicy: Never
cat > k8s/teams/executive-team/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: executive-team
  namespace: elf-teams
  labels:
    app: executive-team
    component: team
    department: executive
spec:
  replicas: 1
  selector:
    matchLabels:
      app: executive-team
  template:
    metadata:
      labels:
        app: executive-team
        component: team
        department: executive
    spec:
      serviceAccountName: executive-team
      containers:
      - name: executive-team
        image: elf-automations/executive-team:latest
        imagePullPolicy: Never  # Critical for local images!
        ports:
        - containerPort: 8090
          name: http
        - containerPort: 8091
          name: a2a
        env:
        - name: TEAM_NAME
          value: "executive-team"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-credentials
              key: api-key
        - name: A2A_ENABLED
          value: "true"
        - name: AGENTGATEWAY_URL
          value: "http://agentgateway:8080"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8090
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8090
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: executive-team
  namespace: elf-teams
spec:
  selector:
    app: executive-team
  ports:
  - name: http
    port: 8090
    targetPort: 8090
  - name: a2a
    port: 8091
    targetPort: 8091
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: executive-team-config
  namespace: elf-teams
data:
  team_name: "executive-team"
  department: "executive"
  framework: "crewai"
  process_type: "hierarchical"
EOF

echo "✅ Updated deployment.yaml with imagePullPolicy: Never"

# Step 4: Commit and push to trigger ArgoCD
echo ""
echo "📤 Step 4: Committing changes..."
echo ""

git add k8s/teams/executive-team/
git commit -m "Deploy executive-team with local image for OrbStack" || echo "No changes to commit"

echo ""
echo "🔄 Step 5: Push to GitHub (ArgoCD will detect changes)..."
echo ""
echo "Run: git push origin main"
echo ""

# Step 6: Instructions for the ArgoCD machine
echo "📋 Step 6: On your ArgoCD/K8s machine:"
echo "======================================"
echo ""
echo "1. Pull the latest changes:"
echo "   cd /path/to/ELFAutomations"
echo "   git pull"
echo ""
echo "2. Load the Docker image into OrbStack:"
echo "   docker load < executive-team.tar"
echo "   # OR if the dev machine is the same as K8s machine:"
echo "   # The image should already be available"
echo ""
echo "3. ArgoCD should automatically sync, or manually sync:"
echo "   argocd app sync elf-teams"
echo "   # OR"
echo "   kubectl -n argocd patch app elf-teams --type merge -p '{\"operation\":{\"sync\":{}}}'"
echo ""
echo "4. Check deployment:"
echo "   kubectl get pods -n elf-teams"
echo "   kubectl logs -n elf-teams deployment/executive-team"
echo ""

# Optional: Save image as tar for transfer if needed
echo "💾 Optional: Save image for transfer"
echo "===================================="
echo "If dev and K8s are different machines:"
echo "  docker save elf-automations/executive-team:latest -o executive-team.tar"
echo "  # Transfer executive-team.tar to K8s machine"
echo "  # On K8s machine: docker load < executive-team.tar"
