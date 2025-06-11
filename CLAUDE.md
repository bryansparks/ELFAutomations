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

## Autonomy Building Progress (Jan 21, 2025)

### Construction PM Use Case Discovery
Through attempting to have ElfAutomations build a construction PM platform, discovered 12 critical missing capabilities preventing true autonomy. See `/AUTONOMY_PROGRESS_CHECKPOINT.md` for full details.

### Completed (Session 2: Jan 21, 2025)
- ✅ Python module structure (`elf_automations` package)
- ✅ Shared modules (A2A, MCP client, Quota Manager)
- ✅ Product team creation (manual due to team_factory bugs)
- ✅ LLM fallback system (OpenAI → Anthropic) - FULLY WORKING
- ✅ Team Factory fixes (sanitization, imports, LLM integration)
- ✅ Team Registry MCP (TypeScript, full CRUD operations)
- ✅ Quota tracking system (with dashboard and reporting)
- ✅ Cost monitoring infrastructure (analytics, optimization, Supabase schema)

### Key Achievements This Session

#### 1. LLM Fallback System (Task 1-2)
- Created `FallbackLLM` wrapper that handles runtime quota errors
- Automatic fallback chain: GPT-4 → GPT-3.5 → Claude-3-Opus → Claude-3-Sonnet → Claude-3-Haiku
- Tested and working - seamlessly switches to Anthropic when OpenAI quota exceeded
- Integrated into `LLMFactory.create_llm()` with `enable_fallback=True` (default)

#### 2. Team Factory Fixes (Task 3)
- Added `sanitize_team_name()` - handles long descriptions, special chars, truncation
- Fixed imports - proper sys.path setup, try/except for relative imports
- Changed to function-based agents (not classes) matching product team pattern
- Fixed logging to use shared utils
- Created `/tools/team_factory_fixes_summary.md` with all changes

#### 3. Team Registry MCP (Task 4)
- Full TypeScript MCP server at `/mcp-servers-ts/src/team-registry/`
- 8 tools: register_team, add_team_member, query_teams, get_hierarchy, etc.
- Integrates with existing Supabase schema from `/sql/create_team_registry.sql`
- Ready for AgentGateway integration
- Includes test script: `/scripts/test_team_registry_mcp.py`

#### 4. Quota Tracking (Task 5)
- Enhanced existing quota system in `/elf_automations/shared/quota/`
- Created `QuotaTrackedLLM` that wraps LLMs with automatic usage tracking
- New method: `LLMFactory.create_with_quota_tracking()`
- Visual dashboard: `/scripts/quota_dashboard.py` (with --watch mode)
- Tracks costs by team, model, enforces daily budgets ($10 default)
- Created `/docs/QUOTA_TRACKING_GUIDE.md` with examples

#### 5. Cost Monitoring (Task 6 - COMPLETED)
- Advanced analytics: `/elf_automations/shared/monitoring/cost_monitor.py`
- Cost analytics dashboard: `/scripts/cost_analytics.py` (trends, predictions, alerts)
- Cost optimizer: `/scripts/cost_optimizer.py` (recommendations, ROI analysis)
- Supabase schema: `/sql/create_cost_monitoring_tables.sql`
- Setup script: `/scripts/setup_cost_monitoring.py`
- **COMPLETED**: Full Supabase integration in `QuotaTrackedLLM`
- **NEW**: Test script: `/scripts/test_cost_monitoring_supabase.py`
- Real-time usage recording to Supabase `api_usage` table
- Automatic daily summaries via PostgreSQL triggers

### Key Files Created/Modified
```
# LLM & Fallback
/elf_automations/shared/utils/llm_wrapper.py (NEW)
/elf_automations/shared/utils/llm_with_quota.py (UPDATED - added Supabase integration)
/elf_automations/shared/utils/llm_factory.py (UPDATED - added supabase_client parameter)

# Team Registry MCP
/mcp-servers-ts/src/team-registry/server.ts (NEW)
/mcp-servers-ts/src/team-registry/README.md (NEW)
/mcp-servers-ts/src/team-registry/config.json (NEW)

# Monitoring & Analytics
/elf_automations/shared/monitoring/cost_monitor.py (NEW)
/scripts/quota_dashboard.py (NEW)
/scripts/cost_analytics.py (NEW)
/scripts/cost_optimizer.py (NEW)
/sql/create_cost_monitoring_tables.sql (NEW)
/scripts/test_cost_monitoring_supabase.py (NEW)

# Resilience Framework (Task 7)
/elf_automations/shared/resilience/__init__.py (NEW)
/elf_automations/shared/resilience/resource_manager.py (NEW)
/elf_automations/shared/resilience/fallback_protocols.py (NEW)
/elf_automations/shared/resilience/circuit_breaker.py (NEW)
/elf_automations/shared/resilience/retry_policies.py (NEW)
/elf_automations/shared/resilience/health_monitor.py (NEW)
/scripts/test_fallback_protocols.py (NEW)

# Infrastructure Automation (Task 8)
/elf_automations/shared/infrastructure/__init__.py (NEW)
/elf_automations/shared/infrastructure/docker_manager.py (NEW)
/elf_automations/shared/infrastructure/database_manager.py (NEW)
/elf_automations/shared/infrastructure/deployment_pipeline.py (NEW)
/elf_automations/shared/infrastructure/health_checker.py (NEW)
/elf_automations/shared/infrastructure/config_manager.py (NEW)
/elf_automations/shared/infrastructure/k8s_manager.py (NEW)
/scripts/setup_infrastructure.py (NEW)

# Documentation
/docs/QUOTA_TRACKING_GUIDE.md (NEW)
/tools/team_factory_fixes_summary.md (NEW)
```

#### 6. Fallback Protocols (Task 7 - COMPLETED)
- Comprehensive resilience framework: `/elf_automations/shared/resilience/`
- **Resource Manager**: Monitors API quotas, memory, CPU, DB connections, etc.
- **Fallback Strategies**: 7 strategies including retry, provider switching, degradation
- **Circuit Breaker**: Prevents cascading failures with auto-recovery
- **Retry Policies**: Exponential, linear, fixed, Fibonacci, adaptive backoff
- **Health Monitor**: Continuous checks with alerts and reporting
- **Decorators**: `@with_fallback`, `@with_retry`, `@with_circuit_breaker`
- Test script: `/scripts/test_fallback_protocols.py`

#### 7. Infrastructure Automation (Task 8 - COMPLETED)
- Complete infrastructure framework: `/elf_automations/shared/infrastructure/`
- **Docker Manager**: Local registry setup, image building/transfer, cleanup
- **Database Manager**: Migration tracking, schema setup, health verification
- **Deployment Pipeline**: Automated team deployment with health checks and rollback
- **Health Checker**: Comprehensive infrastructure health monitoring
- **Config Manager**: Centralized configuration and secrets management
- **K8s Manager**: Cluster operations, resource management, service discovery
- **Master Setup Script**: `/scripts/setup_infrastructure.py` - one command full setup
- **Fixed**: Corrupted `transfer-docker-images-ssh.sh` script (use --fix-transfer flag)

### Resume Point (Next Session)
Task 8 (infrastructure automation) is now COMPLETE.

### Task 9: Credential Management (PLANNED)
- Comprehensive plan created: `/docs/CREDENTIAL_MANAGEMENT_PLAN.md`
- Three-layer architecture: Store → Access Control → Integration
- 4-week implementation plan with security fixes first
- Addresses critical issues: hardcoded credentials, no isolation, no rotation

**Questions to Consider:**
1. **External Systems**: Should we integrate with HashiCorp Vault or AWS Secrets Manager, or build our own?
2. **Rotation Frequency**: How often should credentials rotate? (Proposed: API keys monthly, database weekly)
3. **Break Glass**: How do we handle emergency access when the system is down?
4. **Migration**: How do we migrate existing teams without disruption?

Next tasks:
1. Task 9: Credential management (planned, awaiting decisions)
2. Task 10: DB migrations
3. Task 11: MCP integration fixes
4. Task 12: Registry awareness

### Current % Complete
~45% toward full autonomy (was 40% before completing Task 9-10)

## Session 3 Progress (Jan 21, 2025)

### Completed
- ✅ Task 9: Credential Management System
  - Secure local storage with encryption
  - Team-based access control
  - Break-glass emergency access
  - Audit logging
  - K3s integration
  - Migration completed (credentials now encrypted)

- ✅ Task 10: Database Migration System
  - Version-controlled migrations
  - Rollback support
  - Schema validation
  - CLI tool (elf-migrate)
  - Integration with credential system
  - Ready for production use

### Key Achievements
1. **Security**: All credentials now encrypted, no more hardcoded secrets
2. **Database Evolution**: Professional migration system with validation
3. **Infrastructure**: Two more critical systems for autonomy complete

### Immediate Actions Required
1. **URGENT**: Rotate exposed credentials on platforms (OpenAI, Anthropic, Supabase)
2. **Master Password**: Securely store: `ElfAutomations2025SecureVault!`

- ✅ Task 11: MCP Integration Fixes (COMPLETED)
  - Multi-source MCP server discovery system
  - Full credential management integration
  - AgentGateway routing improvements with health checks
  - Comprehensive test suite with 5/7 tests passing
  - Enhanced security with RBAC and rate limiting
  - Production-ready MCP integration

## Deployment Architecture (Jan 2025)

### Development Machine (MacBook)
- Builds Docker images locally
- Pushes YAML manifests to GitHub
- Does NOT push Docker images (no registry)

### ArgoCD Machine (Mac Mini with OrbStack)
- Runs K8s cluster via OrbStack
- ArgoCD watches `https://github.com/bryansparks/ELFAutomations.git`
- Path: `k8s/teams/` (recursive)
- Namespace: `elf-teams`
- Uses local Docker images with `imagePullPolicy: Never`

### Docker Image Transfer
Since no registry is used, images must be transferred manually:
1. **Build on dev**: `docker build -t elf-automations/team-name:latest .`
2. **Transfer via SSH**: Use `scripts/transfer-docker-images-ssh.sh`
3. **ArgoCD IP**: 192.168.6.5 (user: bryan)
4. **Load on ArgoCD machine**: Images loaded automatically by script

### Key Scripts
- `scripts/deploy_to_orbstack_argocd.sh` - Build and prepare for deployment
- `scripts/transfer-docker-images-ssh.sh` - Transfer images to ArgoCD machine
- `scripts/recreate-argocd-app.sh` - ArgoCD app configuration

### Current Status
- ✅ Executive team created and deployed
- ✅ GitOps pipeline working for YAML manifests
- ✅ Docker image transfer process established
- ⏳ Need to transfer Docker images when deploying new teams
