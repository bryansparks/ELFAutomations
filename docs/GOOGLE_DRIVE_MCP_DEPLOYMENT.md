# Google Drive MCP Deployment Guide

## ✅ Build Complete!

Docker image successfully built:
- **Image**: `elf-automations/google-drive-watcher:latest`
- **Size**: 381MB
- **Ready for**: Local testing or Kubernetes deployment

## Option 1: Test Locally with Docker

### Quick Test
```bash
docker run -it --rm \
  -e GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  -e GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  -e SUPABASE_URL="$SUPABASE_URL" \
  -e SUPABASE_KEY="$SUPABASE_KEY" \
  -p 50051:50051 \
  elf-automations/google-drive-watcher:latest
```

### Test with Volume for Token Storage
```bash
docker run -it --rm \
  -e GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  -e GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  -e SUPABASE_URL="$SUPABASE_URL" \
  -e SUPABASE_KEY="$SUPABASE_KEY" \
  -v ${PWD}/google-tokens:/app/.google-tokens \
  -p 50051:50051 \
  elf-automations/google-drive-watcher:latest
```

## Option 2: Deploy to Kubernetes

### 1. Create Namespace
```bash
kubectl create namespace elf-mcps
```

### 2. Create Secrets
```bash
# Google OAuth credentials
kubectl create secret generic google-oauth-credentials \
  --from-literal=client_id="$GOOGLE_CLIENT_ID" \
  --from-literal=client_secret="$GOOGLE_CLIENT_SECRET" \
  -n elf-mcps

# Supabase credentials
kubectl create secret generic supabase-credentials \
  --from-literal=url="$SUPABASE_URL" \
  --from-literal=service_key="$SUPABASE_KEY" \
  -n elf-mcps
```

### 3. Deploy the MCP
```bash
cd mcps/google-drive-watcher
kubectl apply -f k8s/deployment.yaml
```

### 4. Check Deployment Status
```bash
# Check pod status
kubectl get pods -n elf-mcps

# Check logs
kubectl logs -n elf-mcps -l app=google-drive-watcher

# Get service details
kubectl get svc -n elf-mcps
```

## Option 3: Deploy to Local K8s (OrbStack/Docker Desktop)

If using OrbStack or Docker Desktop with Kubernetes:

### 1. Load Image to Local Registry
```bash
# For OrbStack
docker tag elf-automations/google-drive-watcher:latest \
  registry.local/elf-automations/google-drive-watcher:latest

# For Docker Desktop (already available)
# No action needed - images are shared
```

### 2. Update deployment.yaml
Change `imagePullPolicy: Never` to use local image:
```yaml
imagePullPolicy: IfNotPresent
```

### 3. Deploy
Same as Kubernetes steps above.

## Next Steps: OAuth Setup for Tenants

Once deployed, set up OAuth for each tenant:

```bash
python scripts/setup_google_oauth.py
```

This will:
1. Generate OAuth URLs for each tenant
2. Guide through authorization
3. Store tokens securely
4. Test connections

## Create Google Drive Structure

Create these folders in your Google Drive:
```
/elf-drops/
├── core/           # ELF internal
├── acme-corp/      # ACME Corporation
├── globex-inc/     # Globex Inc
└── stanford-edu/   # Stanford University
```

Get folder IDs from Google Drive:
1. Open folder in Google Drive
2. Look at URL: `https://drive.google.com/drive/folders/[FOLDER_ID]`
3. Copy the FOLDER_ID

## Using the MCP

### Add Watch Folder
```python
# Example: Add ACME Corp folder
result = await client.call_tool(
    "google-drive-watcher",
    "add_watch_folder",
    {
        "folderId": "1abc123def456ghi",  # From Drive URL
        "tenantName": "acme_corp"
    }
)
```

### Start Monitoring
```python
result = await client.call_tool(
    "google-drive-watcher",
    "start_monitoring",
    {
        "intervalSeconds": 300  # Check every 5 minutes
    }
)
```

### Check Queue
```sql
-- In Supabase SQL Editor
SELECT * FROM rag_processing_queue 
WHERE status = 'pending'
ORDER BY created_at DESC;
```

## Troubleshooting

### Pod Not Starting
```bash
kubectl describe pod -n elf-mcps [pod-name]
```

### Authentication Issues
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check redirect URI matches exactly
- Ensure OAuth consent screen is configured

### Database Connection
- Verify Supabase URL and key
- Check network connectivity
- Ensure tables exist (rag_*)

## Success Indicators

✅ Pod running: `kubectl get pods -n elf-mcps`
✅ No errors in logs: `kubectl logs -n elf-mcps -l app=google-drive-watcher`
✅ Can add watch folders
✅ Documents appear in processing queue

The Google Drive MCP is now ready to monitor folders and queue documents for processing!