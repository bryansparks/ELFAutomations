# ArgoCD Applications

This directory contains the GitOps-managed definitions of all ArgoCD applications.

## Important: Single Source of Truth

**ALL ArgoCD applications MUST be defined here!**

If an application exists in the cluster but not in this directory, it's "shadow state" and should be deleted.

## Current Applications

1. **elf-infrastructure.yaml** - Neo4j graph database
2. **elf-teams.yaml** - Minimal teams namespace
3. **n8n.yaml** - Workflow automation

## Managing Applications

### To Add a New Application:
1. Create a new YAML file in this directory
2. Commit and push to Git
3. Apply on deployment machine: `kubectl apply -f k8s/argocd-apps/<app-name>.yaml`

### To Remove an Application:
1. Delete the YAML file from this directory
2. Commit and push to Git
3. Delete from cluster: `kubectl delete application <app-name> -n argocd`

### To Update an Application:
1. Edit the YAML file
2. Commit and push to Git
3. Changes auto-apply if the app itself has auto-sync enabled
