# Team Chat Interface Enhancement Plan

## Overview
Enable direct chat interfaces with top-level team managers (CPO, CMO, etc.) in the ELF Control Center, allowing interactive conversations before task delegation.

## Use Cases

### 1. Executive Team Chat
- **User Story**: As a user, I want to chat with the CPO to discuss product requirements before they delegate to engineering
- **Flow**:
  1. User selects CPO team in Control Center
  2. Opens chat interface
  3. Has conversation to clarify requirements
  4. CPO understands and creates task plan
  5. CPO delegates to CTO/Engineering teams via A2A

### 2. Department Head Chat
- **User Story**: As a user, I want to chat with Marketing Manager about campaign ideas
- **Flow**: Similar to above, but for different organizational trees

### 3. N8N Workflow Interaction
- **User Story**: As a user, I want to speak to N8N workflows via Telegram
- **Flow**:
  1. User sends voice message to Telegram bot
  2. Speech-to-text conversion
  3. Text sent to N8N workflow as task input
  4. Workflow executes and responds

## Technical Architecture

### 1. Team Factory Enhancement

#### New Team Specification Fields
```python
@dataclass
class TeamSpecification:
    # ... existing fields ...

    # Chat interface configuration
    is_top_level: bool = False  # Marks team as top of organizational tree
    enable_chat_interface: bool = False  # Enable direct chat with manager
    chat_config: Dict[str, Any] = field(default_factory=dict)
    # chat_config can include:
    # - allowed_users: List of user IDs who can chat
    # - chat_history_retention: How long to keep chat logs
    # - pre_chat_instructions: Custom instructions for the manager
    # - max_conversation_length: Token/message limits
```

#### Team Factory UI Changes
- Add checkbox: "Is this a top-level team?"
- If checked, show option: "Enable chat interface for team manager"
- Add configuration options for chat behavior

### 2. Control Center Enhancement

#### New Chat Interface Component
```typescript
// /packages/templates/elf-control-center/src/components/team-chat.tsx
interface TeamChatProps {
  teamId: string
  teamName: string
  managerId: string
  managerName: string
}

export function TeamChat({ teamId, teamName, managerId, managerName }: TeamChatProps) {
  // WebSocket connection to team's chat endpoint
  // Message history display
  // Input field with send button
  // Status indicators (thinking, typing, etc.)
}
```

#### Teams Page Enhancement
```typescript
// Add chat button for top-level teams
{team.isTopLevel && team.enableChatInterface && (
  <Button onClick={() => openChat(team)}>
    <MessageCircle className="mr-2 h-4 w-4" />
    Chat with {team.managerName}
  </Button>
)}
```

### 3. Team Deployment Enhancement

#### FastAPI Chat Endpoint
Each top-level team deployment needs a chat endpoint:

```python
# In make-deployable-team.py generated server
@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Initialize conversation with team manager
    manager = crew.manager_agent  # or workflow equivalent
    conversation = ConversationManager(manager)

    try:
        while True:
            # Receive message from user
            data = await websocket.receive_json()
            user_message = data["message"]

            # Send to manager agent with special chat context
            response = await conversation.process_message(
                user_message,
                context={
                    "mode": "interactive_chat",
                    "user_id": data.get("user_id"),
                    "session_id": data.get("session_id")
                }
            )

            # Send response back
            await websocket.send_json({
                "response": response,
                "thinking_time": conversation.last_thinking_time,
                "ready_to_delegate": conversation.is_ready_to_delegate()
            })

            # If manager is ready to delegate, prepare A2A task
            if conversation.is_ready_to_delegate():
                task_spec = conversation.prepare_delegation()
                await websocket.send_json({
                    "delegation_preview": task_spec,
                    "confirm_required": True
                })

    except WebSocketDisconnect:
        print(f"Chat session ended for {team_name}")
```

### 4. A2A Protocol Extension

Add chat-related messages to A2A:

```python
# New A2A message types
class ChatInitiationRequest(A2AMessage):
    """Request to start interactive chat session"""
    user_id: str
    session_id: str
    initial_context: Dict[str, Any]

class ChatDelegationReady(A2AMessage):
    """Manager is ready to delegate after chat"""
    session_id: str
    task_specification: Dict[str, Any]
    chat_summary: str
    confirmed_by_user: bool
```

### 5. N8N Telegram Integration

#### Telegram Bot Setup
```yaml
# n8n-telegram-voice-workflow.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: n8n-telegram-config
data:
  workflow.json: |
    {
      "nodes": [
        {
          "type": "n8n-nodes-base.telegram",
          "typeVersion": 1,
          "position": [250, 300],
          "credentials": {
            "telegramApi": "telegram_bot_api"
          },
          "parameters": {
            "updates": ["message", "voice"]
          }
        },
        {
          "type": "n8n-nodes-base.openai",
          "typeVersion": 1,
          "position": [450, 300],
          "parameters": {
            "operation": "whisper",
            "model": "whisper-1"
          }
        },
        {
          "type": "n8n-nodes-base.httpRequest",
          "typeVersion": 1,
          "position": [650, 300],
          "parameters": {
            "url": "http://executive-team:8090/task",
            "method": "POST",
            "bodyParameters": {
              "task": "={{$json.transcription}}",
              "source": "telegram_voice"
            }
          }
        }
      ]
    }
```

## Implementation Plan

### Phase 1: Team Factory Enhancement (Week 1)
1. Add `is_top_level` and `enable_chat_interface` to TeamSpecification
2. Update team_factory UI to include new options
3. Modify team generation to include chat endpoint
4. Update deployment manifests for WebSocket support

### Phase 2: Control Center Chat UI (Week 2)
1. Create TeamChat component with WebSocket support
2. Add chat button to teams page for eligible teams
3. Implement chat history and session management
4. Add real-time status indicators

### Phase 3: Team Deployment Updates (Week 3)
1. Enhance make-deployable-team.py to generate chat endpoints
2. Add ConversationManager for maintaining chat context
3. Implement delegation preparation after chat
4. Test with executive team deployment

### Phase 4: N8N Telegram Integration (Week 4)
1. Set up Telegram bot credentials in K8s secrets
2. Create N8N workflow for voice processing
3. Connect to team A2A endpoints
4. Test end-to-end voice to task flow

## Security Considerations

1. **Authentication**:
   - Control Center users must be authenticated
   - WebSocket connections need JWT tokens
   - Telegram bot needs webhook validation

2. **Authorization**:
   - Only authorized users can chat with specific teams
   - Rate limiting on chat messages
   - Audit logging of all conversations

3. **Data Privacy**:
   - Chat logs stored securely in Supabase
   - Voice recordings deleted after transcription
   - PII handling in conversations

## Database Schema Updates

```sql
-- Add to team_registry schema
ALTER TABLE teams ADD COLUMN is_top_level BOOLEAN DEFAULT FALSE;
ALTER TABLE teams ADD COLUMN enable_chat_interface BOOLEAN DEFAULT FALSE;
ALTER TABLE teams ADD COLUMN chat_config JSONB DEFAULT '{}';

-- New table for chat sessions
CREATE TABLE team_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    delegated BOOLEAN DEFAULT FALSE,
    delegation_task_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages
CREATE TABLE team_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES team_chat_sessions(id),
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Testing Strategy

1. **Unit Tests**:
   - Team factory chat configuration
   - WebSocket connection handling
   - Message routing

2. **Integration Tests**:
   - End-to-end chat flow
   - Delegation after chat
   - Telegram voice processing

3. **User Acceptance Tests**:
   - Chat with CPO about product features
   - Chat with Marketing Manager about campaigns
   - Voice command to N8N workflow

## Success Metrics

1. **User Engagement**:
   - Number of chat sessions per day
   - Average conversation length
   - Successful delegations after chat

2. **Performance**:
   - WebSocket connection stability
   - Message latency < 500ms
   - Voice transcription accuracy > 95%

3. **Business Value**:
   - Reduced clarification cycles
   - Faster task initiation
   - Better requirement understanding

## Future Enhancements

1. **Multi-modal Chat**:
   - Support images/documents in chat
   - Screen sharing capabilities
   - Collaborative whiteboard

2. **AI Enhancements**:
   - Smart suggestions during chat
   - Auto-complete for common requests
   - Sentiment analysis for better responses

3. **Integration Expansion**:
   - Slack integration
   - Microsoft Teams integration
   - Email-to-chat gateway
