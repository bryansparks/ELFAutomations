# Google Drive Watcher MCP

A Model Context Protocol server for monitoring Google Drive folders and managing document ingestion for the multi-tenant RAG system.

## Features

- Monitor multiple Google Drive folders for changes
- Multi-tenant folder structure support
- Automatic document detection and queuing
- OAuth2 authentication with Google
- Webhook support for real-time updates
- Batch processing capabilities

## Tools

### Authentication
- `authenticate` - Set up Google OAuth credentials
- `refresh_token` - Refresh OAuth access token

### Folder Management
- `add_watch_folder` - Add a folder to monitor
- `remove_watch_folder` - Stop monitoring a folder
- `list_watch_folders` - List all monitored folders
- `get_folder_status` - Get status of a specific folder

### Document Operations
- `list_documents` - List documents in a folder
- `get_document_metadata` - Get document details
- `download_document` - Download a document
- `queue_document` - Queue document for processing
- `check_document_status` - Check processing status

### Monitoring
- `start_monitoring` - Start folder monitoring
- `stop_monitoring` - Stop folder monitoring
- `get_monitoring_status` - Get current monitoring status
- `process_changes` - Process detected changes

## Configuration

The MCP uses the following environment variables:

```bash
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2callback
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Multi-Tenant Structure

The MCP expects the following folder structure in Google Drive:

```
/elf-drops/
├── core/           # Internal ELF documents
├── acme-corp/      # Customer tenant
├── globex-inc/     # Customer tenant
└── stanford-edu/   # Customer tenant
```

Each subfolder under `/elf-drops/` is treated as a separate tenant.