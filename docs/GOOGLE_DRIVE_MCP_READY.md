# Google Drive Integration MCP - Ready to Deploy!

## What We've Done

### 1. Fixed Table References
Updated the Google Drive MCP to use the public schema tables:
- Changed from `rag.tenants` to `rag_tenants`
- Changed from `rag.documents` to `rag_documents`
- Updated all table references to match the new schema

### 2. Created Setup Tools
- **Setup Guide**: `/docs/GOOGLE_DRIVE_MCP_SETUP.md`
- **Quick Setup Script**: `/scripts/setup_drive_watcher.sh`
- **OAuth Test Script**: `/scripts/test_google_auth.py`

## Quick Start

### Step 1: Check Google OAuth Setup
```bash
python scripts/test_google_auth.py
```

This will verify you have:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- Proper configuration

### Step 2: Build and Deploy
```bash
# Quick build and optional deploy
./scripts/setup_drive_watcher.sh

# Or manual steps:
cd mcps/google-drive-watcher
npm install
npm run build
docker build -t elf-automations/google-drive-watcher:latest .
```

### Step 3: Set Up OAuth for Tenants
```bash
python scripts/setup_google_oauth.py
```

This will:
1. Guide you through OAuth for each tenant
2. Store credentials securely
3. Test the connection

### Step 4: Create Google Drive Structure
Create these folders in your Google Drive:
```
/elf-drops/
├── core/           # For ELF internal docs
├── acme-corp/      # For ACME Corporation
├── globex-inc/     # For Globex Inc
└── stanford-edu/   # For Stanford University
```

## Testing the Integration

### 1. Add a Watch Folder
Using the MCP tools, add a folder to monitor:
- Get the folder ID from Google Drive
- Use the `add_watch_folder` tool
- Specify the tenant name

### 2. Start Monitoring
- Use the `start_monitoring` tool
- Set check interval (e.g., 300 seconds)

### 3. Test Document Detection
- Drop a test file in a monitored folder
- Check the processing queue:
  ```python
  result = client.from_("rag_processing_queue").select("*").execute()
  ```

## Architecture

```
Google Drive
    ↓
[Drive Watcher MCP] 
    ↓ (detects new files)
[Supabase Queue]
    ↓
[RAG Processor Team] (next step)
    ↓
[Storage Systems]
```

## Troubleshooting

### OAuth Issues
- Ensure redirect URI matches exactly: `http://localhost:8080/oauth2callback`
- Check OAuth consent screen is configured
- Add test users if in development mode

### Database Connection
- Verify Supabase credentials in .env
- Check tables exist with `rag_` prefix
- Ensure RLS is properly configured

### Kubernetes Deployment
- Check secrets are created
- Verify pod is running: `kubectl get pods -n elf-mcps`
- Check logs: `kubectl logs -n elf-mcps deployment/google-drive-watcher`

## What's Next?

The Google Drive MCP is ready! Next steps in the RAG system:

1. **RAG Processor Team** (Week 2)
   - Create LangGraph-based processing team
   - Implement document classifiers
   - Build chunking strategies

2. **Embedding Pipeline**
   - OpenAI/Anthropic integration
   - Vector storage in Qdrant

3. **Document Processing**
   - Invoice processor
   - Contract processor
   - Research paper processor
   - General document processor

The foundation is set - documents dropped in Google Drive will automatically be queued for processing!