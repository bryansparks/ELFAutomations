# GitOps Workflow for Team Deployment

## Overview
This document describes the complete workflow for deploying teams via GitOps with ArgoCD.

## Workflow Steps

### 1. Create Team (Development Machine)
```bash
cd tools
python team_factory.py
```
- Provide team description
- Choose framework (CrewAI/LangGraph)
- Select LLM provider
- Specify organizational placement (e.g., `marketing`, `marketing.brand`)
- Review and confirm team composition

### 2. Build Docker Image (Development Machine)
```bash
cd teams/{team-name}
python make-deployable-team.py  # Generates Dockerfile and server
docker build -t elf-automations/{team-name}:latest .
```

### 3. Push to Registry (Development Machine)
```bash
# Tag for your registry
docker tag elf-automations/{team-name}:latest {registry}/elf-automations/{team-name}:latest

# Push to registry
docker push {registry}/elf-automations/{team-name}:latest
```

### 4. Prepare GitOps Artifacts (Development Machine)
```bash
cd tools
python prepare_gitops_artifacts.py
```
This script:
- Collects all K8s manifests from team directories
- Updates image references to use your registry
- Generates Kustomization files
- Creates ArgoCD Application manifest
- Outputs everything to `gitops/` directory

### 5. Review and Commit (Development Machine)
```bash
cd gitops
git add .
git commit -m "Deploy {team-name}"
git push origin main
```

### 6. ArgoCD Sync (Production - Automatic)
ArgoCD will:
- Detect changes in the GitOps repository
- Apply the manifests to Kubernetes
- Create pods for each team
- Monitor health and sync status

## Directory Structure

### Source Repository (Development)
```
ElfAutomations/
├── teams/
│   ├── executive-team/
│   │   ├── agents/
│   │   ├── k8s/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   └── patches/           # Patches when child teams added
│   └── marketing-team/
│       └── ... (same structure)
├── tools/
│   ├── team_factory.py
│   └── prepare_gitops_artifacts.py
└── gitops/                    # Generated artifacts
```

### GitOps Repository (What ArgoCD Watches)
```
gitops-repo/
├── manifests/
│   └── teams/
│       ├── executive-team/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── configmap.yaml
│       ├── marketing-team/
│       │   └── ...
│       └── kustomization.yaml
└── applications/
    └── teams-app.yaml
```

## Environment Variables

### Development Machine
```bash
export SUPABASE_URL=your-supabase-url
export SUPABASE_ANON_KEY=your-supabase-key
export SUPABASE_DB_URL=postgresql://...  # For Team Registry
export DOCKER_REGISTRY=your-registry.io/your-org
export GITOPS_REPO_URL=https://github.com/your-org/gitops-repo
```

### Kubernetes Secrets (Production)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: supabase-credentials
  namespace: elf-automations
stringData:
  url: your-supabase-url
  key: your-supabase-key
---
apiVersion: v1
kind: Secret
metadata:
  name: llm-api-keys
  namespace: elf-automations
stringData:
  openai-api-key: sk-...
  anthropic-api-key: sk-ant-...
```

## Team Registry Integration

When a team is created:
1. Team Factory registers it in Supabase Team Registry
2. Relationships are tracked (who reports to whom)
3. If reporting to executive, a patch file is generated
4. Patch must be applied to update parent team

### Applying Patches
When a new team reports to an executive:
```bash
# 1. Review the patch
cat teams/executive-team/patches/add_marketing-team_*.yaml

# 2. Apply to executive team (manual process for now)
# Update the executive's manages_teams list

# 3. Rebuild executive team
cd teams/executive-team
docker build -t elf-automations/executive-team:latest .
docker push {registry}/elf-automations/executive-team:latest

# 4. Run GitOps preparation again
cd tools
python prepare_gitops_artifacts.py
```

## Best Practices

1. **Always use team_factory.py** - It's the single source of truth
2. **Build and push images before GitOps prep** - ArgoCD can't build images
3. **Review manifests before committing** - Check image references, resource limits
4. **Apply patches promptly** - Keep parent teams updated when children are added
5. **Use semantic versioning for images** - Don't always use :latest

## Troubleshooting

### Team not deploying
1. Check ArgoCD UI for sync status
2. Verify image exists in registry
3. Check pod logs: `kubectl logs -n elf-automations {team-name}-...`
4. Verify secrets are created

### Registry issues
1. Ensure Kubernetes can pull from your registry
2. Create imagePullSecrets if using private registry
3. Update deployment.yaml with imagePullSecrets

### A2A Communication failures
1. Check AgentGateway is running
2. Verify service discovery between teams
3. Check Team Registry for correct relationships

## Future Enhancements

1. **Automated Patch Application** - Tool to apply patches automatically
2. **CI/CD Pipeline** - Automated build and push on team creation
3. **Helm Charts** - Package teams as Helm charts for better templating
4. **Multi-Environment** - Support for dev/staging/prod deployments
