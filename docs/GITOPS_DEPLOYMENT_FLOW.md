# GitOps Deployment Flow

## Overview
```
Development Machine              →    Docker Registry    →    GitOps Machine (ArgoCD)
(Your current machine)                (Hub/Registry)          (K8s cluster)
```

## Detailed Flow

### 1. On Development Machine (Current)

```bash
# Build artifacts
teams/executive-team/
├── Dockerfile              # Created by make-deployable-team.py
├── team_server.py          # FastAPI wrapper with A2A
├── requirements.txt        # All dependencies
└── k8s/
    └── deployment.yaml     # K8s manifest

# Build and push
docker build -t registry.com/elf/executive-team:latest .
docker push registry.com/elf/executive-team:latest
```

### 2. Prepare GitOps Artifacts

```bash
# Run preparation script
python tools/prepare_gitops_artifacts.py

# Creates structure:
gitops/
├── manifests/
│   ├── teams/
│   │   ├── executive-team/
│   │   │   ├── deployment.yaml  # With updated image refs
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   └── kustomization.yaml
│   └── mcps/
│       └── kustomization.yaml
└── applications/
    ├── teams-app.yaml          # ArgoCD Application for teams
    └── mcps-app.yaml           # ArgoCD Application for MCPs
```

### 3. Push to GitOps Repository

```bash
# Option A: Separate GitOps repo
git clone git@github.com:your-org/gitops-repo.git
cp -r gitops/* gitops-repo/elf-automations/
cd gitops-repo
git add .
git commit -m "Deploy ElfAutomations teams"
git push

# Option B: Use this repo (subfolder)
git add gitops/
git commit -m "Update GitOps manifests"
git push origin main
```

### 4. On GitOps Machine (ArgoCD)

```bash
# ArgoCD watches the GitOps repository
# Apply the ArgoCD Application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: elf-teams
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/gitops-repo
    targetRevision: HEAD
    path: elf-automations/manifests/teams
  destination:
    server: https://kubernetes.default.svc
    namespace: elf-automations
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF

# ArgoCD will:
# 1. Pull manifests from GitOps repo
# 2. Apply them to K8s cluster
# 3. K8s will pull images from registry
# 4. Pods will start running
```

## Key Configuration Points

### 1. Image Registry Access
```yaml
# In K8s cluster, ensure imagePullSecrets if using private registry
apiVersion: v1
kind: Secret
metadata:
  name: regcred
  namespace: elf-automations
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
```

### 2. ArgoCD Repository Access
```yaml
# Add repository to ArgoCD
argocd repo add https://github.com/your-org/gitops-repo \
  --username <username> \
  --password <token>
```

### 3. Update Deployment Image References
The `prepare_gitops_artifacts.py` script automatically updates image references:
```yaml
# From:
image: elf-automations/executive-team:latest

# To:
image: your-registry.com/elf-automations/executive-team:latest
```

## Environment Variables Needed

On Development Machine:
```bash
export DOCKER_REGISTRY="your-registry.com"
export GITOPS_REPO="git@github.com:your-org/gitops-repo.git"
```

On GitOps Machine:
- ArgoCD needs access to GitOps repository
- K8s needs access to Docker registry

## Verification Steps

1. **Check ArgoCD Application Status**
   ```bash
   argocd app get elf-teams
   ```

2. **Check K8s Deployments**
   ```bash
   kubectl get deployments -n elf-automations
   kubectl get pods -n elf-automations
   ```

3. **Check A2A Discovery**
   ```bash
   kubectl logs deployment/agentgateway -n elf-automations | grep "Discovered"
   ```

## Troubleshooting

1. **Image Pull Errors**
   - Check registry credentials
   - Verify image exists: `docker pull <image>`

2. **ArgoCD Sync Errors**
   - Check ArgoCD has repo access
   - Verify manifest syntax
   - Check namespace exists

3. **Pod CrashLoopBackOff**
   - Check logs: `kubectl logs <pod-name> -n elf-automations`
   - Verify environment variables
   - Check resource limits
