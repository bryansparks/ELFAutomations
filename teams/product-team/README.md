# Product Team

## Overview
The product team is responsible for defining product strategy, creating PRDs, and ensuring we build the right products for the market.

**Framework**: CrewAI
**Department**: Product
**Process Type**: Hierarchical (5 members)
**Default LLM**: OpenAI GPT-4

## Team Members

1. **Senior Product Manager** (Manager)
   - Leads product strategy and roadmap
   - Creates comprehensive PRDs
   - Defines success metrics
   - Coordinates with all departments
   - Skills: Product strategy, Market analysis, Stakeholder management, Data-driven decisions

2. **Business Analyst**
   - Researches market needs
   - Creates detailed requirements
   - Analyzes competitor features
   - Defines user stories
   - Skills: Requirements analysis, Market research, Data analysis, Documentation

3. **Technical Product Manager**
   - Works closely with engineering
   - Defines technical requirements
   - Manages technical debt
   - Ensures feasibility
   - Skills: Technical architecture, API design, System integration, Engineering collaboration

4. **UX Researcher**
   - Conducts user interviews
   - Runs usability studies
   - Creates user personas
   - Validates product-market fit
   - Skills: User research, Usability testing, Survey design, Behavioral analysis

5. **Competitive Intelligence Analyst**
   - Monitors competitor products
   - Tracks market trends
   - Analyzes pricing strategies
   - Identifies opportunities
   - Skills: Competitive analysis, Market intelligence, Trend analysis, Strategic thinking

## Communication Patterns

### Intra-Team Communication
The team follows a hierarchical pattern with the Senior Product Manager as the lead who coordinates all product decisions:

- **Senior PM** communicates with: All team members, CEO, other department heads
- **Business Analyst** communicates with: Senior PM, UX Researcher, sales teams
- **Technical PM** communicates with: Senior PM, engineering teams, CTO
- **UX Researcher** communicates with: Senior PM, design teams, customers
- **Competitive Analyst** communicates with: Senior PM, marketing, sales

### Inter-Team Communication (A2A Protocol)
The Senior Product Manager communicates with other teams via A2A:

- **With Executive Team**: Receives product requests from CEO
- **With Engineering**: Sends PRDs and technical requirements
- **With Marketing**: Shares product positioning and features
- **With Sales**: Provides product capabilities and roadmap
- **With Customer Success**: Gathers feedback and feature requests

## Key Responsibilities

1. **Product Requirements Documents (PRDs)**
   - Comprehensive feature specifications
   - User stories and acceptance criteria
   - Success metrics and KPIs
   - Timeline and milestone planning

2. **Market Research**
   - Customer needs analysis
   - Competitive landscape mapping
   - Pricing strategy recommendations
   - Market opportunity sizing

3. **Product Strategy**
   - Roadmap development
   - Feature prioritization
   - Go-to-market planning
   - Product lifecycle management

## Deployment

### Local Development
```bash
pip install -r requirements.txt
python crew.py
```

### Containerization
```bash
python make-deployable-team.py
docker build -t elf-automations/product-team .
docker run -p 8091:8091 elf-automations/product-team
```

### Kubernetes Deployment
```bash
kubectl apply -f k8s/deployment.yaml
```

## API Endpoints

- `GET /health` - Health check
- `GET /capabilities` - Get team capabilities
- `POST /task` - Submit product task

### Example Task Request
```json
{
  "description": "Create PRD for construction project management platform",
  "context": {
    "target_users": "construction project managers",
    "key_features": ["SMS communication", "project dashboard", "multi-project support"],
    "timeline": "8 weeks to MVP",
    "constraints": ["mobile-first", "offline capable", "simple UI"]
  }
}
```

## Configuration

### Team Configuration
See `config/team_config.yaml` for agent definitions.

### A2A Configuration
See `config/a2a_config.yaml` for inter-team communication settings.

### LLM Configuration
Uses OpenAI GPT-4 by default. Set `OPENAI_API_KEY` environment variable.
