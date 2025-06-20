# Google Drive Integration MCP Setup Guide

## Overview
The Google Drive Watcher MCP monitors specified folders for new documents and automatically queues them for RAG processing.

## Prerequisites

### 1. Google Cloud Project Setup

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Note your project ID

2. **Enable Google Drive API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Configure OAuth consent screen if prompted:
     - Choose "External" for user type
     - Fill in required fields
     - Add test users if in development
   - For Application type, choose "Web application"
   - Add authorized redirect URI: `http://localhost:8080/oauth2callback`
   - Download the credentials JSON

4. **Set Environment Variables**:
   ```bash
   # Add to your .env file
   GOOGLE_CLIENT_ID=your-client-id-here
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2callback
   ```

## Building the MCP

### 1. Install Dependencies

```bash
cd mcps/google-drive-watcher
npm install
```

### 2. Build TypeScript

```bash
npm run build
```

### 3. Test Locally (Optional)

```bash
# Set environment variables
export GOOGLE_CLIENT_ID=your-client-id
export GOOGLE_CLIENT_SECRET=your-client-secret
export SUPABASE_URL=your-supabase-url
export SUPABASE_KEY=your-supabase-key

# Run the server
npm start
```

## Docker Build & Deployment

### 1. Build Docker Image

```bash
cd mcps/google-drive-watcher
docker build -t elf-automations/google-drive-watcher:latest .
```

### 2. Test Docker Image Locally

```bash
docker run -it --rm \
  -e GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID \
  -e GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_KEY=$SUPABASE_KEY \
  elf-automations/google-drive-watcher:latest
```

### 3. Deploy to Kubernetes

First, create the secrets:

```bash
# Create namespace if not exists
kubectl create namespace elf-mcps

# Create Google OAuth secret
kubectl create secret generic google-oauth-credentials \
  --from-literal=client_id=$GOOGLE_CLIENT_ID \
  --from-literal=client_secret=$GOOGLE_CLIENT_SECRET \
  -n elf-mcps

# Create Supabase credentials secret
kubectl create secret generic supabase-credentials \
  --from-literal=url=$SUPABASE_URL \
  --from-literal=service_key=$SUPABASE_KEY \
  -n elf-mcps
```

Deploy the MCP:

```bash
kubectl apply -f k8s/deployment.yaml
```

## Setting Up OAuth for Tenants

### 1. Run the OAuth Setup Script

```bash
python scripts/setup_google_oauth.py
```

This script will:
- Guide you through OAuth setup for each tenant
- Store credentials securely
- Test the connection

### 2. Manual OAuth Flow (if needed)

If you need to manually authorize a tenant:

1. Get the authorization URL:
   ```python
   from elf_automations.shared.auth import setup_google_oauth
   success, auth_url = setup_google_oauth("tenant_name")
   print(auth_url)
   ```

2. Visit the URL in a browser
3. Authorize access
4. Copy the authorization code
5. Exchange for tokens

## Using the MCP

### Available Tools

The Google Drive Watcher MCP provides these tools:

1. **Authentication**:
   - `get_auth_url` - Get OAuth authorization URL
   - `authenticate` - Complete OAuth flow with auth code

2. **Folder Management**:
   - `add_watch_folder` - Add a folder to monitor
   - `remove_watch_folder` - Stop monitoring a folder
   - `list_watch_folders` - List all monitored folders

3. **Document Operations**:
   - `list_documents` - List documents in a folder
   - `get_document_metadata` - Get document details
   - `download_document` - Download a document
   - `queue_document` - Queue document for RAG processing

4. **Monitoring**:
   - `start_monitoring` - Start automatic folder monitoring
   - `stop_monitoring` - Stop monitoring
   - `process_changes` - Manually check for changes

### Example Usage

```python
# Using the MCP client
from elf_automations.shared.mcp import MCPClient

client = MCPClient()

# Add a folder to watch
result = await client.call_tool(
    "google-drive-watcher",
    "add_watch_folder",
    {
        "folderId": "1234567890abcdef",
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

## Folder Structure in Google Drive

Set up your Google Drive with this structure:

```
/elf-drops/
├── core/           # Internal ELF documents
├── acme-corp/      # ACME Corporation documents
├── globex-inc/     # Globex Inc documents
└── stanford-edu/   # Stanford University documents
```

Each subfolder corresponds to a tenant in the RAG system.

## Monitoring & Troubleshooting

### Check MCP Status

```bash
kubectl get pods -n elf-mcps
kubectl logs -n elf-mcps deployment/google-drive-watcher
```

### Common Issues

1. **OAuth Error**: Check CLIENT_ID and CLIENT_SECRET are correct
2. **Folder Access Denied**: Ensure the authorized account has access to the folders
3. **Database Connection**: Verify Supabase credentials are correct

### Testing the Integration

1. Place a test document in a monitored folder
2. Check the processing queue:
   ```python
   result = client.from_("rag_processing_queue").select("*").execute()
   print(result.data)
   ```

## Next Steps

1. Set up folder monitoring for each tenant
2. Configure processing intervals
3. Deploy the RAG processor team to handle queued documents
4. Monitor the processing pipeline

The Google Drive MCP is now ready to automatically detect and queue documents for RAG processing!