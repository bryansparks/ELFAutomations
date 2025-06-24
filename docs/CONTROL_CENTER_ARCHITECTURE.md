# ElfAutomations Control Center Architecture

## Overview

The Control Center consists of two parts that run on DIFFERENT machines:

1. **Frontend UI** (Next.js) - Runs on deployment machine (Mac Mini)
2. **Backend API** (FastAPI) - Runs on development machine (your laptop)

## Why This Architecture?

The API server needs access to:
- Python scripts (`mcp_marketplace.py`, `mcp_factory.py`, `team_factory.py`)
- npm registry for searching MCPs
- GitHub API for discovering repositories
- Local file system for creating teams/MCPs
- Development tools and dependencies
- Docker for building team/MCP images
- kubectl for generating Kubernetes manifests
- Git for pushing changes to the repository

These resources only exist on your development machine, not on the deployment server.

## Setup Instructions

### 1. On Development Machine (Your Laptop)

```bash
# Get your machine's IP address
ifconfig | grep "inet " | grep -v 127.0.0.1

# Start the API server
cd ~/projects/ELFAutomations
./scripts/run_control_center_api.sh
```

The API will be available at:
- `http://localhost:8001` (local access)
- `http://YOUR_IP:8001` (network access)

### 2. On Deployment Machine (Mac Mini)

Create `.env.local` in the Control Center directory:

```bash
cd ~/projects/ELFAutomations/packages/templates/elf-control-center
cp .env.local.example .env.local
```

Edit `.env.local` and set your development machine's IP:
```
NEXT_PUBLIC_API_URL=http://192.168.1.100:8001  # Replace with your actual IP
```

Restart the Next.js app:
```bash
npm run build
npm start
```

## API Endpoints

The API server provides these real (not mocked) endpoints:

### MCP Discovery
- `GET /api/mcp/discover` - Search for available MCPs
- `POST /api/mcp/install` - Install an MCP via mcp_marketplace.py
- `GET /api/mcp/installed` - List installed MCPs

### Team Management
- `GET /api/teams` - Get all teams from Supabase
- `POST /api/teams/create` - Create new team via team_factory.py
- `POST /api/teams/deploy` - Generate deployment artifacts
- `GET /api/teams/hierarchy` - View organizational structure

### System Status
- `GET /api/system/status` - Real system health data
- `GET /api/costs/metrics` - Actual cost tracking from Supabase
- `GET /api/dashboard` - Combined dashboard data

## Data Flow

```
Mac Mini (UI) ─────────► Your Laptop (API) ─────────► Supabase
     │                           │                          │
     │                           ├── mcp_marketplace.py     │
     └── Next.js App             ├── mcp_factory.py        └── Database
         Port 3002               ├── team_factory.py
                                 ├── Docker builds
                                 ├── K8s manifests
                                 └── Port 8001
```

## What Runs Where

### Development Machine (Your Laptop)
- **API Server** (`control_center_minimal.py`)
- **Team Factory** (`team_factory.py`) - Creates team structures
- **MCP Factory** (`mcp_factory.py`) - Creates internal MCPs
- **MCP Marketplace** (`mcp_marketplace.py`) - Discovers/installs external MCPs
- **Docker** - Builds team and MCP images
- **Git** - Pushes changes for GitOps deployment
- **Python Environment** - All dependencies and tools

### Deployment Machine (Mac Mini)
- **Next.js UI** - The Control Center web interface
- **ArgoCD** - Pulls manifests from Git and deploys to K8s
- **K8s/OrbStack** - Runs the deployed teams and MCPs
- **No Python** - Cannot run factory scripts or API

## Complete Workflow Example

1. **Create a Team** (via UI on Mac Mini):
   - User fills out team creation form in browser
   - UI sends request to `http://YOUR_LAPTOP:8001/api/teams/create`
   - API server on laptop runs `team_factory.py`
   - Team files created in `teams/new-team/`
   - Team registered in Supabase
   - Response sent back to UI

2. **Build Team Docker Image** (on laptop):
   ```bash
   cd teams/new-team
   ./make-deployable-team.py
   docker build -t elf-automations/new-team:latest .
   ```

3. **Deploy Team** (GitOps flow):
   - Push manifests to GitHub from laptop
   - ArgoCD on Mac Mini pulls changes
   - Team deployed to K8s cluster

4. **Install External MCP** (via UI):
   - User searches for "Slack" MCP
   - UI queries `http://YOUR_LAPTOP:8001/api/mcp/discover`
   - API runs `mcp_marketplace.py search`
   - User clicks install
   - API runs `mcp_marketplace.py install slack`
   - MCP registered in AgentGateway config

## Troubleshooting

### "Failed to fetch" errors
1. Check API server is running: `curl http://YOUR_IP:8001/health`
2. Verify `.env.local` has correct IP address
3. Ensure firewall allows port 8001

### Mock data appearing
This only happens when the API is unreachable. Fix the connection to get real data.

### CORS errors
The API already includes CORS headers for localhost:3002. If using a different port, update `control_center_minimal.py`.

## Security Considerations

1. The API server binds to `0.0.0.0:8001` (all interfaces)
2. Only run on trusted networks
3. Consider adding authentication for production use
4. Use HTTPS proxy for internet-facing deployments

## Benefits of This Architecture

1. **Real Data**: No mock data - everything comes from actual sources
2. **Live Operations**: Can actually create teams, install MCPs, generate code
3. **Development Tools**: Full access to Python environment, Docker, Git
4. **Separation of Concerns**: UI can be deployed anywhere, API stays with dev tools
5. **GitOps Ready**: Changes made via API can be pushed to Git for deployment

## Limitations

1. **Network Dependency**: UI requires network access to development machine
2. **Single Point of Failure**: If laptop is off, Control Center can't create/modify
3. **Security**: API server is exposed on network (use VPN for production)
4. **Performance**: Operations depend on laptop performance and network speed
