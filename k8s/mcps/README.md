# MCP Deployments

This directory contains Kubernetes manifests for MCP (Model Context Protocol) servers.

## Directory Structure
```
k8s/mcps/
├── google-drive-watcher/   # Google Drive monitoring MCP
│   ├── configmap.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── README.md
```

## Deployment
These manifests are automatically deployed by ArgoCD to the `elf-mcps` namespace.

## Adding New MCPs
1. Create a new subdirectory for your MCP
2. Add the Kubernetes manifests (deployment, service, configmap)
3. Commit and push - ArgoCD will automatically deploy

## Namespace
All MCPs are deployed to the `elf-mcps` namespace.
