# GitOps Validation Checklist

## Current Setup Understanding

### Machine Roles
1. **Development Machine (This one)**
   - Role: Create code, build artifacts
   - Does NOT run K8s
   - Does NOT deploy anything
   - Only pushes to Git

2. **ArgoCD Machine (Remote)**
   - Role: Runs K8s cluster + ArgoCD
   - Pulls from Git repository
   - Deploys applications
   - Runs the actual containers

## Key Questions to Validate

### 1. Container Image Strategy
**Question**: How do container images get from dev to K8s?

**Option A: Docker Registry (Traditional)**
```
Dev Machine → Build Image → Push to Registry → K8s pulls from Registry
```

**Option B: Local Images (Mac Mini setup)**
```
Dev Machine → Build Image → Save as tar → Copy to K8s machine → Load image
```

**Option C: Build on K8s Machine**
```
Dev Machine → Push code to Git → K8s machine pulls code → Builds image locally
```

### 2. Current ArgoCD Configuration
On the ArgoCD machine, check:

```bash
# What repository is ArgoCD watching?
argocd repo list

# What applications are configured?
argocd app list

# What path in the repo is ArgoCD looking at?
argocd app get <app-name> -o json | jq '.spec.source.path'
```

### 3. Repository Structure Check
ArgoCD needs to know WHERE in your repository to find manifests:

```
ELFAutomations/
├── gitops/                  # <- Does ArgoCD know about this?
│   └── manifests/
│       └── teams/
│           └── executive-team/
│               ├── deployment.yaml
│               └── service.yaml
├── teams/                   # <- Source code (not for ArgoCD)
├── tools/                   # <- Tools (not for ArgoCD)
└── k8s/                     # <- Old manifests location?
```

### 4. Image Reference Validation
Check what images your manifests reference:

```bash
# On dev machine
grep -r "image:" teams/executive-team/k8s/
grep -r "image:" gitops/manifests/teams/
```

Common patterns:
- `image: executive-team:latest` (expects local image)
- `image: localhost:5000/executive-team:latest` (local registry)
- `image: docker.io/org/executive-team:latest` (Docker Hub)
- `imagePullPolicy: Never` (for local images)

## Validation Steps

### Step 1: Check Git Repository Structure
```bash
# On dev machine
ls -la gitops/
tree gitops/ -L 3
```

### Step 2: Check ArgoCD Repository Configuration
```bash
# On ArgoCD machine
cd /path/to/ELFAutomations
git remote -v
git branch
cat .git/config
```

### Step 3: Check ArgoCD Application Path
```bash
# On ArgoCD machine
# If you have ArgoCD CLI:
argocd app get <your-app-name>

# Or check the Application YAML:
kubectl get application -n argocd <your-app-name> -o yaml | grep -A5 "source:"
```

### Step 4: Verify Image Strategy
Based on your Mac Mini setup, you likely use ONE of these:

1. **OrbStack's Local Registry**
   ```yaml
   image: localhost:5000/executive-team:latest
   imagePullPolicy: Always
   ```

2. **Pre-loaded Images**
   ```yaml
   image: elf-automations/executive-team:latest
   imagePullPolicy: Never  # Important!
   ```

3. **External Registry**
   ```yaml
   image: your-registry.com/elf-automations/executive-team:latest
   ```

## What We Need to Find Out

1. **On ArgoCD Machine**:
   - What path is ArgoCD configured to watch?
   - Is it watching the root of the repo or a specific folder?
   - What's in the ArgoCD Application definition?

2. **Image Loading Method**:
   - Does your K8s use a local registry?
   - Are images pre-loaded?
   - Is there a shared registry?

3. **Current Working Setup**:
   - Do you have any apps currently working with ArgoCD?
   - If yes, how are their images handled?

## Next Steps

Once we know:
1. Where ArgoCD is looking for manifests
2. How images are handled in your setup

We can:
1. Put manifests in the right location
2. Update image references correctly
3. Build/transfer images appropriately
