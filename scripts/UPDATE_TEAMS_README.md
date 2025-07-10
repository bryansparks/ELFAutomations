# Team Chat Update Scripts

This directory contains scripts for updating existing teams with WebSocket chat support.

## Main Scripts

### 1. `update_teams_with_chat.py`
**Purpose**: Quick update script for adding WebSocket chat to existing teams

**What it does**:
- Updates team_server.py files with WebSocket `/chat` endpoint
- Adds JWT authentication support
- Includes conversation management
- Updates requirements.txt with needed dependencies
- Creates timestamped backups of all modified files

**Teams Updated**:
- executive-team (CEO and C-suite)
- engineering-team (CTO's department)
- marketing-team (CMO's department)

**Usage**:
```bash
python scripts/update_teams_with_chat.py
```

### 2. `enhance_deployable_team.py` (in tools/team_factory/)
**Purpose**: Advanced script with Supabase integration

**Additional Features**:
- Queries Supabase for team configurations
- Can update individual teams or all at once
- Updates Kubernetes manifests
- More configuration options

**Usage**:
```bash
# Update all top-level teams
python tools/team_factory/enhance_deployable_team.py --all

# Update specific team
python tools/team_factory/enhance_deployable_team.py src/teams/teams/executive-team
```

## What Gets Modified

### team_server.py Changes
1. **New Imports**:
   ```python
   from fastapi import WebSocket, WebSocketDisconnect
   from elf_automations.shared.auth.jwt_handler import require_websocket_auth
   from elf_automations.shared.chat import ConversationManager
   ```

2. **New Endpoints**:
   - `WS /chat` - WebSocket endpoint for real-time chat
   - `POST /chat/delegation/confirm` - Confirm delegations

3. **Enhanced Endpoints**:
   - `/health` - Now includes `chat_enabled` field
   - `/capabilities` - Lists chat interface capability

### requirements.txt Additions
- `websockets>=10.0` - For WebSocket support
- `PyJWT>=2.8.0` - For JWT authentication

## Backups

All original files are backed up with timestamp:
- `team_server.py.backup.YYYYMMDD_HHMMSS`

To restore:
```bash
cd src/teams/teams/executive-team
cp team_server.py.backup.20250627_143022 team_server.py
```

## After Running Scripts

1. **Test Locally**:
   ```bash
   cd src/teams/teams/executive-team
   python team_server.py
   # In another terminal:
   curl http://localhost:8000/capabilities | grep chat
   ```

2. **Rebuild Docker Images**:
   ```bash
   for team in executive-team engineering-team marketing-team; do
     cd src/teams/teams/$team
     docker build -t elf-automations/$team:latest .
     cd -
   done
   ```

3. **Deploy to Kubernetes**:
   ```bash
   kubectl rollout restart deployment/executive-team -n elf-teams
   kubectl rollout restart deployment/engineering-team -n elf-teams
   kubectl rollout restart deployment/marketing-team -n elf-teams
   ```

## Troubleshooting

### Chat Not Working?
1. Check if dependencies installed: `pip list | grep -E "websockets|PyJWT"`
2. Verify team_server.py was updated: `grep websocket team_server.py`
3. Check logs: `python team_server.py 2>&1 | grep -i chat`

### Import Errors?
The server gracefully handles missing chat dependencies:
```
Warning: Chat dependencies not found. WebSocket chat will be disabled.
```
Install missing deps: `pip install websockets PyJWT`

### Need to Add More Teams?
Edit `CHAT_ENABLED_TEAMS` dict in `update_teams_with_chat.py`:
```python
CHAT_ENABLED_TEAMS = {
    "your-team-name": {
        "is_top_level": True,
        "chat_config": {
            "allowed_roles": ["admin", "user"],
            "max_session_duration_minutes": 60,
            ...
        }
    }
}
```

## Related Documentation
- [Team Chat Deployment Guide](../docs/guides/TEAM_CHAT_DEPLOYMENT_GUIDE.md)
- [Team Chat Quick Start](../docs/guides/TEAM_CHAT_QUICK_START.md)
- [Team Chat Interface Plan](../docs/TEAM_CHAT_INTERFACE_PLAN.md)
