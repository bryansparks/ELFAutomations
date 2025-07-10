# Team Chat Interface - Quick Start Guide

## 🚀 5-Minute Deployment

### Prerequisites Check (1 minute)
```bash
# Check environment variables
echo "SUPABASE_URL: ${SUPABASE_URL:0:20}..."
echo "SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:20}..."
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."

# Navigate to project
cd /Users/bryansparks/projects/ELFAutomations
```

### Step 1: Update Team Servers (2 minutes)
```bash
# Run the update script
python scripts/update_teams_with_chat.py

# Expected output:
# ✅ Successfully updated 3/3 teams
```

### Step 2: Quick Local Test (2 minutes)
```bash
# Test executive team
cd src/teams/teams/executive-team
python team_server.py &
sleep 5

# Verify chat is enabled
curl -s http://localhost:8000/capabilities | grep -i chat

# Kill the test server
kill %1
cd -
```

### Step 3: Build & Deploy (if needed)
```bash
# Quick rebuild for executive team only
cd src/teams/teams/executive-team
docker build -t elf-automations/executive-team:latest .

# Deploy to K8s
kubectl rollout restart deployment/executive-team -n elf-teams
```

## 📋 What Was Changed

### Files Modified
1. **team_server.py** - Added WebSocket `/chat` endpoint
2. **requirements.txt** - Added `websockets` and `PyJWT`

### New Endpoints
- `GET /health` - Now includes `chat_enabled` field
- `GET /capabilities` - Lists WebSocket chat capability
- `WS /chat` - WebSocket endpoint for real-time chat
- `POST /chat/delegation/confirm` - Confirm task delegation

## 🔍 Quick Verification

```bash
# Check all teams were updated
grep -l "@app.websocket" src/teams/teams/*/team_server.py

# Verify in UI
# 1. Open http://localhost:3000/teams
# 2. Look for chat icons next to team names
# 3. Click to test chat interface
```

## 🚨 If Something Goes Wrong

```bash
# Restore from backup
cd src/teams/teams/executive-team
ls -la team_server.py.backup.*
# Pick the latest backup and restore:
# cp team_server.py.backup.20250627_143022 team_server.py

# Check logs
kubectl logs -n elf-teams deployment/executive-team --tail=50
```

## ✅ Success Indicators

- Health endpoint shows `"chat_enabled": true`
- Chat icons appear in Control Center UI
- WebSocket connection establishes without errors
- Can send messages and receive responses

---

**Total Time**: ~5-10 minutes for basic deployment
