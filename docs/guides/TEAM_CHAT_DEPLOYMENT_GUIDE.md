# Team Chat Interface Deployment Guide

This guide explains how to deploy the WebSocket chat interface for existing teams in the ELF Automations system.

## Overview

The team chat interface allows users to have real-time conversations with top-level team managers (like the CEO, CTO, CMO) before delegating tasks. This creates a more interactive and collaborative experience compared to direct task assignment.

## Prerequisites

1. **Environment Variables**: Ensure these are set:
   ```bash
   export SUPABASE_URL="your-supabase-url"
   export SUPABASE_ANON_KEY="your-supabase-anon-key"
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```

2. **Database**: The chat tables must exist in Supabase (already completed)

3. **Python Dependencies**: Install required packages:
   ```bash
   pip install websockets PyJWT
   ```

## Available Scripts

### 1. Simple Update Script (Recommended for Quick Deployment)

**Location**: `/scripts/update_teams_with_chat.py`

**Purpose**: Updates existing team directories with WebSocket chat support.

**What it does**:
- Updates `team_server.py` files to include WebSocket endpoints
- Adds required dependencies to `requirements.txt`
- Creates backups of original files
- Pre-configured for executive, engineering, and marketing teams

**Usage**:
```bash
cd /Users/bryansparks/projects/ELFAutomations
python scripts/update_teams_with_chat.py
```

**Output Example**:
```
🚀 Updating teams with WebSocket chat support

Found 3 teams to update:

📁 executive-team (/Users/bryansparks/projects/ELFAutomations/src/teams/teams/executive-team)
  📄 Backed up to team_server.py.backup.20250627_143022
  ✅ Updated team_server.py with WebSocket chat support
  📦 Added dependencies: websockets>=10.0, PyJWT>=2.8.0

📁 engineering-team (/Users/bryansparks/projects/ELFAutomations/src/teams/teams/engineering-team)
  📄 Backed up to team_server.py.backup.20250627_143025
  ✅ Updated team_server.py with WebSocket chat support
  ✓ All dependencies already present

✅ Successfully updated 3/3 teams
```

### 2. Advanced Enhancement Script

**Location**: `/tools/team_factory/enhance_deployable_team.py`

**Purpose**: Full-featured script with Supabase integration and more options.

**Features**:
- Queries Supabase for team configurations
- Can update individual teams or all top-level teams
- Updates Kubernetes manifests
- More flexible configuration options

**Usage Examples**:

```bash
# Update a single team
python tools/team_factory/enhance_deployable_team.py src/teams/teams/executive-team

# Update all top-level teams from Supabase
python tools/team_factory/enhance_deployable_team.py --all

# Force enable chat for a specific team
python tools/team_factory/enhance_deployable_team.py src/teams/teams/marketing-team --enable-chat
```

## Step-by-Step Deployment Process

### Phase 1: Update Team Servers (5 minutes)

1. **Navigate to project root**:
   ```bash
   cd /Users/bryansparks/projects/ELFAutomations
   ```

2. **Run the update script**:
   ```bash
   python scripts/update_teams_with_chat.py
   ```

3. **Verify the updates**:
   ```bash
   # Check that team_server.py files were updated
   grep -l "websocket" src/teams/teams/*/team_server.py
   ```

### Phase 2: Test Locally (10 minutes)

1. **Test executive team server**:
   ```bash
   cd src/teams/teams/executive-team
   python team_server.py
   ```

2. **In another terminal, test the endpoints**:
   ```bash
   # Health check (should show chat_enabled: true)
   curl http://localhost:8000/health | jq .

   # Capabilities (should list WebSocket chat interface)
   curl http://localhost:8000/capabilities | jq .
   ```

3. **Stop the server** (Ctrl+C) and repeat for other teams if desired

### Phase 3: Build Docker Images (15 minutes)

1. **Build all team images**:
   ```bash
   # Run from project root
   for team in executive-team engineering-team marketing-team; do
     echo "Building $team..."
     cd src/teams/teams/$team
     docker build -t elf-automations/$team:latest .
     cd -
   done
   ```

2. **Verify images were created**:
   ```bash
   docker images | grep elf-automations
   ```

### Phase 4: Deploy to Kubernetes (10 minutes)

1. **Transfer images to K8s cluster** (if using local K8s):
   ```bash
   # If using the transfer script
   ./scripts/transfer-docker-images-ssh.sh
   ```

2. **Apply Kubernetes manifests**:
   ```bash
   # Deploy each team
   kubectl apply -f src/teams/teams/executive-team/k8s/deployment.yaml
   kubectl apply -f src/teams/teams/engineering-team/k8s/deployment.yaml
   kubectl apply -f src/teams/teams/marketing-team/k8s/deployment.yaml
   ```

3. **Verify deployments**:
   ```bash
   kubectl get pods -n elf-teams
   kubectl logs -n elf-teams -l app=executive-team --tail=50
   ```

### Phase 5: Update Control Center (5 minutes)

1. **Restart the Control Center** to pick up the new team capabilities:
   ```bash
   # Find and restart the control center pod
   kubectl rollout restart deployment/control-center -n elf-system
   ```

2. **Access the Control Center UI**:
   - Navigate to http://localhost:3000/teams (or your configured URL)
   - Look for the chat badges on eligible teams
   - Click the chat icon to test the interface

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - Check JWT_SECRET_KEY is set in environment
   - Verify ingress supports WebSocket (nginx annotations)
   - Check browser console for detailed errors

2. **Chat Dependencies Not Found**:
   - The server will run without chat if dependencies are missing
   - Install: `pip install websockets PyJWT`
   - Rebuild Docker image after adding dependencies

3. **No Chat Button in UI**:
   - Verify team has `enable_chat_interface: true` in database
   - Check Control Center logs for API errors
   - Ensure team status is "active"

### Verification Commands

```bash
# Check if team has chat enabled in database
curl http://localhost:8001/api/teams | jq '.[] | select(.enable_chat_interface == true)'

# Test WebSocket endpoint directly (requires wscat)
npm install -g wscat
wscat -c "ws://localhost:8000/chat?token=YOUR_JWT_TOKEN"

# Check team server logs
kubectl logs -n elf-teams deployment/executive-team --tail=100 | grep -i chat
```

## Rollback Procedure

If you need to rollback the changes:

1. **Restore backup files**:
   ```bash
   cd src/teams/teams/executive-team
   mv team_server.py.backup.* team_server.py
   ```

2. **Rebuild and redeploy**:
   ```bash
   docker build -t elf-automations/executive-team:latest .
   kubectl rollout restart deployment/executive-team -n elf-teams
   ```

## Security Considerations

1. **JWT Tokens**: Required for WebSocket authentication
   - Generated by Control Center API
   - Valid for 1 hour by default
   - Contains user_id and team_id claims

2. **Access Control**:
   - Only users with "admin" or "user" roles can chat
   - Team access is verified on connection
   - Sessions timeout after configured duration

3. **Rate Limiting**:
   - Max messages per session enforced
   - Connection limits per user (if configured)

## Next Steps

After successful deployment:

1. **Test Chat Flow**:
   - Open Control Center
   - Click chat icon on executive team
   - Have a conversation about a task
   - Verify delegation preview appears

2. **Monitor Logs**:
   ```bash
   # Watch team logs for chat activity
   kubectl logs -f -n elf-teams deployment/executive-team | grep -E "(chat|websocket|session)"
   ```

3. **Configure Additional Teams**:
   - Edit `/scripts/update_teams_with_chat.py` to add more teams
   - Or use the Supabase UI to enable chat for teams
   - Re-run the update script

## Estimated Total Time

- **Minimal Deployment**: ~30 minutes
  - Update scripts: 5 minutes
  - Build images: 15 minutes
  - Deploy to K8s: 10 minutes

- **Full Testing**: ~45 minutes
  - Includes local testing
  - Verification of all teams
  - UI testing

## Support

If you encounter issues:

1. Check the logs first (both team server and Control Center)
2. Verify all environment variables are set
3. Ensure database migrations were applied
4. Review the WebSocket browser console errors

For the chat interface to work properly, ensure:
- Teams are marked as `is_top_level` and `enable_chat_interface` in the database
- JWT authentication is properly configured
- WebSocket support is enabled in your ingress/load balancer
