# RAG System Deployment Guide

## Architecture Overview

The RAG system consists of multiple components working together:

1. **Google Drive MCP** - Monitors folders and queues documents
2. **RAG Processor Team** - Processes queued documents
3. **Supabase** - Stores document metadata and processing queue
4. **Qdrant** - Vector database for embeddings
5. **Neo4j** - Graph database for knowledge representation

## Deployment Steps

### 1. Google Drive MCP (Completed)

The Google Drive MCP has been built and is ready for deployment:
- **Docker Image**: `elf-automations/google-drive-watcher:latest` (381MB)
- **Namespace**: `elf-mcps`
- **Features**: OAuth authentication, multi-tenant folder monitoring, document queuing

#### Deploy via GitOps:
```bash
# Run the deployment script
./scripts/deploy_google_drive_mcp_gitops.sh

# After script completes, commit and push
cd gitops
git add .
git commit -m "Deploy Google Drive MCP for RAG system"
git push origin main
```

#### Post-Deployment Setup:
```bash
# 1. Create namespace if not exists
kubectl create namespace elf-mcps

# 2. Create secrets
kubectl create secret generic google-oauth-credentials \
  --from-literal=client_id="$GOOGLE_CLIENT_ID" \
  --from-literal=client_secret="$GOOGLE_CLIENT_SECRET" \
  -n elf-mcps

kubectl create secret generic supabase-credentials \
  --from-literal=url="$SUPABASE_URL" \
  --from-literal=service_key="$SUPABASE_KEY" \
  -n elf-mcps

# 3. Monitor deployment
kubectl get pods -n elf-mcps
kubectl logs -n elf-mcps -l app=google-drive-watcher
```

### 2. RAG Processor Team (Next Step)

The RAG Processor Team will:
- Monitor the `rag_processing_queue` table
- Process documents based on type
- Generate embeddings
- Store in Qdrant and Neo4j
- Update document status

#### Team Structure:
```
rag-processor-team/
├── agents/
│   ├── queue_monitor.py      # Monitors processing queue
│   ├── document_classifier.py # Classifies document types
│   ├── pdf_processor.py      # Processes PDF documents
│   ├── text_processor.py     # Processes text documents
│   ├── embedding_generator.py # Generates embeddings
│   └── storage_coordinator.py # Manages vector/graph storage
├── workflows/
│   └── document_pipeline.py   # LangGraph workflow
└── k8s/
    ├── deployment.yaml
    ├── service.yaml
    └── configmap.yaml
```

### 3. Google Drive Folder Structure

Create these folders in your Google Drive:
```
/elf-drops/
├── core/           # ELF internal documents
├── acme-corp/      # ACME Corporation
├── globex-inc/     # Globex Inc
└── stanford-edu/   # Stanford University
```

Get folder IDs:
1. Open folder in Google Drive
2. Look at URL: `https://drive.google.com/drive/folders/[FOLDER_ID]`
3. Copy the FOLDER_ID

### 4. OAuth Setup for Tenants

After deployment, authorize each tenant:

```python
# Use the setup script
python scripts/setup_google_oauth.py

# Or manually via kubectl
kubectl exec -it -n elf-mcps deployment/google-drive-watcher -- \
  node dist/server.js get_auth_url
```

### 5. Add Watch Folders

Once OAuth is configured, add folders to monitor:

```python
# Example: Add ACME Corp folder
from elf_automations.shared.mcp import MCPClient

client = MCPClient()
result = await client.call_tool(
    "google-drive-watcher",
    "add_watch_folder",
    {
        "folderId": "1abc123def456ghi",  # From Drive URL
        "tenantName": "acme_corp"
    }
)

# Start monitoring
result = await client.call_tool(
    "google-drive-watcher",
    "start_monitoring",
    {
        "intervalSeconds": 300  # Check every 5 minutes
    }
)
```

## Monitoring & Troubleshooting

### Check Processing Queue
```sql
-- In Supabase SQL Editor
SELECT * FROM rag_processing_queue
WHERE status = 'pending'
ORDER BY created_at DESC;
```

### Common Issues

#### Pod Not Starting
```bash
kubectl describe pod -n elf-mcps [pod-name]
```

#### Authentication Issues
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check redirect URI matches exactly
- Ensure OAuth consent screen is configured

#### No Documents Being Queued
- Verify OAuth tokens are valid
- Check folder permissions
- Review logs for API errors

## Next Steps

1. **Deploy Google Drive MCP** ✓
2. **Create RAG Processor Team** (Week 2)
3. **Implement Document Classifiers** (Week 2)
4. **Build Specialized Processors** (Week 3)
5. **Create Query Interface** (Week 4)

## Success Metrics

- ✅ Google Drive MCP deployed and monitoring folders
- ⏳ Documents queued in `rag_processing_queue`
- ⏳ RAG Processor Team processing documents
- ⏳ Embeddings stored in Qdrant
- ⏳ Knowledge graph populated in Neo4j
- ⏳ Teams can query RAG system for information
