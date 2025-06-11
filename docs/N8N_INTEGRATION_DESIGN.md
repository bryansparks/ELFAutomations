# n8n Integration Design for ElfAutomations

## Overview

This document outlines the integration of n8n workflow automation into the ElfAutomations team-based agentic system. The design follows a hybrid approach where n8n handles deterministic, high-volume automations while agentic teams focus on reasoning and decision-making tasks.

## Architecture Principles

1. **Loose Coupling**: n8n and ElfAutomations remain independent systems, communicating through well-defined interfaces
2. **Native Patterns**: Respect each system's natural workflows and conventions
3. **Async by Design**: All interactions are asynchronous, allowing both systems to operate independently
4. **Single Source of Truth**: Supabase remains the authoritative data store for all structured data

## Integration Pattern

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  ElfAutomations     │     │ n8n-interface    │     │   n8n Instance  │
│  Agentic Team       │────▶│     Team         │────▶│   (Dockerized)  │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
         │                           │                         │
         │                           ▼                         ▼
         │                    ┌──────────────┐         ┌──────────────┐
         │                    │   Supabase   │◀────────│  n8n + MCP   │
         │                    │  Job Table   │         │  Integration │
         └───────────────────▶└──────────────┘         └──────────────┘
                                    ▲
                                    │
                              Status Polling
```

## Components

### 1. n8n Dockerized Instance
- Runs as a container within the ElfAutomations K8s cluster
- Maintains its own web UI for workflow management
- Configured with MCP support for Supabase integration
- Deployed in the `elf-teams` namespace

### 2. n8n-interface Team
- Special agentic team that bridges ElfAutomations and n8n
- Responsibilities:
  - Accept automation requests from other teams
  - Create job entries in Supabase
  - Trigger n8n workflows (via webhook or message)
  - Monitor job status and retrieve results
  - Transform results for requesting teams

### 3. Supabase Job Tracking
- Central table for tracking all n8n automation requests
- Schema includes tracking ID, status, payloads, and timestamps
- Enables async coordination between systems
- Provides audit trail for all automations

### 4. Communication Flow
1. Agentic team requests automation from n8n-interface team via A2A
2. n8n-interface creates job record with unique tracking ID
3. n8n workflow triggered via webhook or message trigger
4. n8n updates job status during execution using MCP
5. n8n writes results to Supabase upon completion
6. n8n-interface polls for completion and returns results

## Implementation Phases

### Phase 1: Infrastructure Setup (Days 1-2)
**Goal**: Get n8n running in the K8s cluster with basic connectivity

Tasks:
1. Create n8n Docker deployment configuration
2. Configure persistent storage for n8n data
3. Set up n8n service and ingress for web UI access
4. Test basic n8n deployment and UI access

Deliverables:
- `k8s/n8n/deployment.yaml`
- `k8s/n8n/service.yaml`
- `k8s/n8n/pvc.yaml`
- Working n8n instance accessible via web UI

### Phase 2: Supabase Integration (Days 3-4)
**Goal**: Enable n8n to read/write from Supabase using MCP

Tasks:
1. Create job tracking schema in Supabase
2. Configure n8n with MCP settings
3. Mount MCP configuration in n8n container
4. Create test workflow that writes to Supabase

Deliverables:
- `sql/create_n8n_jobs_table.sql`
- `config/n8n_mcp_config.json`
- Updated deployment with MCP volume mounts
- Test workflow writing "Hello from n8n" to Supabase

### Phase 3: n8n-interface Team Creation (Days 5-6)
**Goal**: Build the bridge team between ElfAutomations and n8n

Tasks:
1. Use team factory to create n8n-interface team
2. Implement job creation and tracking logic
3. Add webhook trigger capability
4. Implement status polling and result retrieval

Deliverables:
- `teams/n8n-interface/` complete team structure
- Working A2A endpoints for automation requests
- Job tracking implementation

### Phase 4: Hello World Integration (Days 7-8)
**Goal**: Complete end-to-end automation request

Tasks:
1. Create simple n8n workflow (e.g., fetch weather, format response)
2. Configure webhook trigger in n8n
3. Test request from executive team to n8n-interface team
4. Verify job tracking and result retrieval

Success Criteria:
- Executive team can request weather for a city
- n8n-interface creates job and triggers workflow
- n8n fetches weather data and stores in Supabase
- Results returned to executive team via A2A

### Phase 5: Production Readiness (Days 9-10)
**Goal**: Harden the integration for production use

Tasks:
1. Add error handling and retry logic
2. Implement job timeout handling
3. Create monitoring dashboards
4. Document common workflow patterns

Deliverables:
- Error handling in n8n-interface team
- Grafana dashboard for job metrics
- n8n workflow templates
- Integration guide for team developers

## Example Workflow Request

```python
# From executive team to n8n-interface team
request = {
    "task": "automate_market_research",
    "workflow": "competitive_analysis",
    "parameters": {
        "competitors": ["Company A", "Company B"],
        "data_sources": ["news", "social_media", "financials"],
        "output_format": "executive_summary"
    },
    "deadline": "2025-01-25T17:00:00Z"
}

# Response from n8n-interface team
response = {
    "tracking_id": "job_123abc",
    "status": "accepted",
    "estimated_completion": "2025-01-25T16:30:00Z",
    "polling_endpoint": "/status/job_123abc"
}
```

## Security Considerations

1. **Network Isolation**: n8n instance only accessible within cluster
2. **Authentication**: Webhook endpoints secured with API keys
3. **Data Access**: n8n MCP limited to specific Supabase tables
4. **Audit Trail**: All automations logged with requesting team

## Future Enhancements

1. **Workflow Marketplace**: Pre-built n8n workflows for common tasks
2. **Dynamic Workflow Creation**: Teams can request custom workflow creation
3. **Result Caching**: Cache common automation results
4. **Workflow Versioning**: Track and manage workflow versions
5. **Cost Tracking**: Monitor API usage and costs per automation

## Conclusion

This integration design enables ElfAutomations to leverage n8n's automation capabilities while maintaining architectural integrity. The loose coupling ensures both systems can evolve independently while providing value through complementary strengths.
