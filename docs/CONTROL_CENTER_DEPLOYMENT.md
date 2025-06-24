# Control Center Deployment Architecture

## The Two-Machine Architecture

```
┌─────────────────────────────────────┐     ┌─────────────────────────────────────┐
│   DEVELOPMENT MACHINE (Laptop)      │     │   DEPLOYMENT MACHINE (Mac Mini)     │
│                                     │     │                                     │
│  ┌─────────────────────────────┐   │     │  ┌─────────────────────────────┐   │
│  │   Control Center API        │   │     │  │   Control Center UI         │   │
│  │   (FastAPI on :8001)        │◄──┼─────┼──│   (Next.js on :3002)       │   │
│  └─────────────────────────────┘   │     │  └─────────────────────────────┘   │
│            │                        │     │                                     │
│            ▼                        │     │  ┌─────────────────────────────┐   │
│  ┌─────────────────────────────┐   │     │  │   ArgoCD                    │   │
│  │   Python Scripts:           │   │     │  │   (Watches GitHub)          │   │
│  │   - team_factory.py         │   │     │  └─────────────────────────────┘   │
│  │   - mcp_factory.py          │   │     │            │                        │
│  │   - mcp_marketplace.py      │   │     │            ▼                        │
│  └─────────────────────────────┘   │     │  ┌─────────────────────────────┐   │
│            │                        │     │  │   Kubernetes (OrbStack)     │   │
│            ▼                        │     │  │   - Deployed Teams          │   │
│  ┌─────────────────────────────┐   │     │  │   - Deployed MCPs           │   │
│  │   Generated Files:          │   │     │  └─────────────────────────────┘   │
│  │   - teams/*/                │   │     │                                     │
│  │   - mcps/*/                 │   │     │                                     │
│  │   - k8s manifests           │   │     │                                     │
│  └─────────────────────────────┘   │     │                                     │
│            │                        │     │                                     │
│            ▼                        │     │                                     │
│  ┌─────────────────────────────┐   │     │                                     │
│  │   Git Push to GitHub        │───┼─────┼────────────────────────────────────┘
│  └─────────────────────────────┘   │     │
│                                     │     │
│  ┌─────────────────────────────┐   │     │
│  │   Docker                    │   │     │
│  │   - Build team images       │   │     │
│  │   - Build MCP images        │   │     │
│  └─────────────────────────────┘   │     │
└─────────────────────────────────────┘     └─────────────────────────────────────┘
                    │                                          │
                    └──────────────────────────────────────────┘
                                       ▼
                           ┌─────────────────────┐
                           │     Supabase        │
                           │  - Team Registry    │
                           │  - MCP Registry     │
                           │  - Cost Tracking    │
                           └─────────────────────┘
```

## Why This Split?

### Development Machine Has:
- Python environment with all dependencies
- Access to `team_factory.py`, `mcp_factory.py`, etc.
- Docker for building images
- Git credentials for pushing to GitHub
- kubectl for generating manifests
- npm/yarn for JavaScript operations
- Direct file system access for code generation

### Deployment Machine Has:
- Kubernetes cluster (via OrbStack)
- ArgoCD for GitOps deployments
- Running teams and MCPs
- Next.js UI server
- But NO Python environment or development tools

## Workflow Examples

### Creating a New Team

1. **User Action** (on Mac Mini browser):
   - Navigate to Teams page
   - Click "Create Team"
   - Fill out form with team details

2. **API Call** (Mac Mini → Laptop):
   ```
   POST http://192.168.1.100:8001/api/teams/create
   {
     "name": "analytics-team",
     "description": "Data analysis and reporting",
     "agents": ["analyst", "reporter", "validator"]
   }
   ```

3. **Processing** (on Laptop):
   - API server receives request
   - Runs `team_factory.py` with parameters
   - Generates team structure in `teams/analytics-team/`
   - Registers team in Supabase
   - Returns success response

4. **Next Steps** (manual on Laptop):
   ```bash
   cd teams/analytics-team
   docker build -t elf-automations/analytics-team:latest .
   docker push ...  # If using registry
   git add .
   git commit -m "Add analytics team"
   git push
   ```

5. **Deployment** (automated on Mac Mini):
   - ArgoCD detects new commits
   - Pulls updated manifests
   - Deploys team to Kubernetes

### Installing an External MCP

1. **User Action** (on Mac Mini browser):
   - Navigate to MCP Discovery
   - Search for "Slack"
   - Click "Install"

2. **API Call** (Mac Mini → Laptop):
   ```
   POST http://192.168.1.100:8001/api/mcp/install
   {
     "name": "slack"
   }
   ```

3. **Processing** (on Laptop):
   - API server runs `mcp_marketplace.py install slack`
   - Updates AgentGateway config
   - Registers in Supabase MCP registry
   - Returns installation instructions

## Setup Checklist

### On Development Machine:
- [ ] Install Python dependencies
- [ ] Set up `.env` with Supabase credentials
- [ ] Run `./scripts/run_control_center_api.sh`
- [ ] Note your IP address

### On Deployment Machine:
- [ ] Create `.env.local` with `NEXT_PUBLIC_API_URL=http://DEV_MACHINE_IP:8001`
- [ ] Run `npm run build && npm start` in Control Center
- [ ] Ensure network connectivity to development machine

## Common Issues

### "Failed to fetch" in UI
- API server not running on development machine
- Incorrect IP in `.env.local`
- Firewall blocking port 8001

### "Mock data" appearing
- This means the API connection failed
- Check network and API server status

### Teams not deploying
- Ensure Git push was done after team creation
- Check ArgoCD sync status
- Verify Docker images are available
