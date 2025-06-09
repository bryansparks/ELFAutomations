# ElfAutomations Team-Based Architecture Progress

## Current Status (January 20, 2025)

### Vision
- **Team-centric approach**: Teams (not individual agents) are the deployment unit
- Teams preserve internal collaboration (CrewAI natural language or LangGraph state machines)
- Inter-team communication via Google's A2A protocol
- All MCP access through AgentGateway
- Supabase for ALL structured data storage

### Key Documents
- `/docs/Agent Design Pattern V2.md` - Team-based architecture pattern
- `/docs/AI Team Culture Patterns.md` - Delegation and communication patterns
- `/docs/AI Team Size Patterns.md` - Two-pizza rule (3-7 agents, 5 optimal)
- `/docs/GITOPS_WORKFLOW.md` - Complete GitOps deployment guide

### Completed Work

#### 1. Team Factory (`tools/team_factory.py`)
**Status: Production Ready with Registry Integration**
- Natural language team description input
- Framework choice (CrewAI or LangGraph)
- LLM provider selection (OpenAI/Anthropic)
- Organizational placement via dot notation (e.g., `marketing`, `marketing.socialmedia`)
- Generates proper file structure per framework conventions
- Creates individual agent files with LLM configuration
- Generates crew.py orchestrator (CrewAI) or workflow.py (LangGraph)
- Includes make-deployable-team.py script
- Natural language logging for intra-team communication
- A2A structured logging for inter-team communication
- Manager agents get A2A client capabilities
- **NEW**: Registers teams in Supabase Team Registry
- **NEW**: Generates patches for parent teams when children are added

#### 2. Team Registry (Supabase)
**Status: Schema Created, Integrated with Factory**
- Location: `sql/create_team_registry.sql`
- Setup script: `scripts/setup_team_registry.py`
- Tracks all teams, members, relationships, and audit log
- Bidirectional updates when new teams report to executives
- Views for team hierarchy and executive overview
- Team Factory is the ONLY way to create teams (ensures integrity)

#### 3. MCP Factory (`tools/mcp_factory.py`)
**Status: Production Ready**
- Unified tool for creating internal and external MCPs
- Follows same patterns as team factory
- Generates complete deployment structure
- Auto-registers with AgentGateway
- Creates K8s manifests for deployment

#### 4. GitOps Pipeline (`tools/prepare_gitops_artifacts.py`)
**Status: Complete for Teams and MCPs**
- Collects all team and MCP manifests
- Updates image references with registry
- Generates Kustomization files
- Creates ArgoCD Applications
- Outputs to unified `gitops/` directory structure

#### 5. Executive Team 
**Status: Created and Enhanced**
- Location: `/teams/executive-team/`
- 5 C-suite executives (CEO, CTO, CMO, COO, CFO)
- Hierarchical process with CEO as delegating manager
- A2A communication patterns implemented
- Each executive manages specific subordinate teams:
  - CTO → engineering-team, qa-team, devops-team
  - CMO → marketing-team, content-team, brand-team
  - COO → operations-team, hr-team, facilities-team
  - CFO → finance-team, accounting-team, budget-team

### Communication Architecture

#### Intra-Team (Within Team)
- Natural language via CrewAI/LangGraph
- Unstructured logging to preserve team dynamics
- Example: "skeptic" engineer can challenge decisions naturally
- Logs: `/logs/{team-name}_communications.log`

#### Inter-Team (Between Teams) 
- Formal A2A protocol through managers only
- Structured messages with success criteria, deadlines, context
- No direct communication between teams (only through managers)
- Clear audit trail for accountability

### File Structure Pattern
```
teams/
├── {team-name}/
│   ├── README.md               # Auto-generated with LLM config
│   ├── agents/                 # Individual agent files
│   │   ├── __init__.py
│   │   └── {agent_name}.py     # With LLM config & A2A for managers
│   ├── crew.py                 # Main orchestrator (CrewAI)
│   ├── workflows/              # LangGraph workflows
│   ├── tasks/                  # Task definitions
│   ├── tools/                  # Team-specific tools
│   ├── config/                 # Configuration files
│   │   ├── team_config.yaml
│   │   └── a2a_config.yaml
│   ├── make-deployable-team.py # Creates deployable container
│   └── k8s/
│       └── deployment.yaml     # Complete with resources, probes, secrets

mcps/
├── {mcp-name}/
│   ├── src/                    # Source code (internal MCPs)
│   ├── k8s/                    # Kubernetes manifests
│   ├── Dockerfile
│   └── README.md
```

### Deployment Strategy
- Each team/MCP runs as a single K8s pod
- FastAPI server wraps the crew/workflow
- Exposes A2A endpoints (/task, /health, /capabilities)
- GitOps workflow with ArgoCD
- Unified `gitops/` directory for all manifests

### Key Technical Decisions
- A2A for inter-team (not intra-team) communication
- Natural language logging for team efficiency analysis
- Framework-agnostic team factory
- Supabase as single source of truth for data
- LLM provider choice per team
- Manager-only inter-team communication pattern
- Team Registry ensures organizational integrity
- MCPs follow same deployment patterns as teams

### Deployment Commands
```bash
# Create team
cd tools && python team_factory.py

# Create MCP
cd tools && python mcp_factory.py

# Build and push images
cd teams/{team-name} && docker build -t registry/elf/{team-name} .
docker push registry/elf/{team-name}

# Prepare GitOps artifacts
cd tools && python prepare_gitops_artifacts.py

# Deploy via GitOps
cd gitops && git add . && git commit && git push
```

### Recent Enhancements (Jan 20, 2025)
1. **LangGraph Support**: Full implementation for state-machine based teams
2. **Team Registry**: Supabase schema for tracking all teams and relationships
3. **MCP Integration**: MCPs now follow same patterns as teams
4. **Unified GitOps**: Single pipeline for teams and MCPs
5. **Organizational Placement**: Dot notation for team hierarchy (e.g., marketing.socialmedia)

### Next Steps
1. Run `setup_team_registry.py` to create schema
2. Test creating marketing team with team factory
3. Create MCPs for business tools
4. Deploy everything via GitOps pipeline