# Executive Team

## Overview
The executive team provides strategic leadership and coordinates all departments within ElfAutomations.

**Framework**: CrewAI  
**Department**: Executive  
**Process Type**: Hierarchical (5 members)  
**Default LLM**: OpenAI GPT-4 (via CrewAI defaults)

## Team Members

1. **Chief Executive Officer** (Manager)
   - Sets company vision and strategy
   - Makes final decisions on major initiatives
   - Coordinates with all department heads
   - Reports to board and stakeholders
   - Skills: Strategic thinking, Leadership, Decision making, Communication

2. **Chief Technology Officer**
   - Defines technical strategy and architecture
   - Oversees product development
   - Ensures technical excellence
   - Skills: Technical leadership, Architecture, Innovation, Product development

3. **Chief Marketing Officer**
   - Develops go-to-market strategies
   - Builds brand awareness
   - Drives demand generation
   - Skills: Marketing strategy, Brand building, Go-to-market, Analytics

4. **Chief Operations Officer**
   - Optimizes operational efficiency
   - Manages cross-functional processes
   - Drives continuous improvement
   - Skills: Operations management, Process optimization, Cross-functional leadership

5. **Chief Financial Officer**
   - Manages financial planning and analysis
   - Ensures financial health
   - Guides investment decisions
   - Skills: Financial planning, Analysis, Budgeting, Investment strategy

## Communication Patterns

### Intra-Team Communication (Within Executive Team)
The team follows a hierarchical communication pattern with the CEO as the top-level manager who can delegate tasks to other C-suite executives. Executives communicate naturally using CrewAI's built-in collaboration features:

- **CEO** communicates with: CTO, CMO, COO, CFO
- **CTO** communicates with: CEO, COO, CMO  
- **CMO** communicates with: CEO, CTO, CFO
- **COO** communicates with: CEO, CTO, CFO
- **CFO** communicates with: CEO, CMO, COO

### Inter-Team Communication (A2A Protocol)
Executives manage subordinate teams through formal A2A messages:

**Chief Executive Officer** manages:
- `executive-team` (coordinates through other executives)

**Chief Technology Officer** manages via A2A:
- `engineering-team`
- `qa-team`
- `devops-team`

**Chief Marketing Officer** manages via A2A:
- `marketing-team`
- `content-team`
- `brand-team`

**Chief Operations Officer** manages via A2A:
- `operations-team`
- `hr-team`
- `facilities-team`

**Chief Financial Officer** manages via A2A:
- `finance-team`
- `accounting-team`
- `budget-team`

#### A2A Communication Flow:
1. **Executive formulates request**: Creates detailed task with success criteria, deadlines, and context
2. **A2A message sent**: Formal request sent to subordinate team's manager
3. **Team executes**: Subordinate team works on the task internally
4. **Results returned**: Deliverables and status updates sent back via A2A

This separation ensures:
- Clear accountability and tracking
- Proper team boundaries and autonomy
- Scalable communication as organization grows
- Audit trail for all inter-team requests

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the crew directly
python crew.py
```

### Containerization
```bash
# Generate deployment files
python make-deployable-team.py

# Build Docker image
docker build -t elf-automations/executive-team .

# Run container
docker run -p 8090:8090 elf-automations/executive-team
```

### Kubernetes Deployment
```bash
# Apply the deployment
kubectl apply -f k8s/deployment.yaml
```

## API Endpoints

Once deployed, the team exposes the following endpoints:

- `GET /health` - Health check
- `GET /capabilities` - Get team capabilities and status
- `POST /task` - Execute a task with the team

### Example Task Request
```json
{
  "description": "Develop a strategic plan for Q2 focusing on market expansion",
  "context": {
    "current_revenue": "$2M ARR",
    "target_markets": ["enterprise", "mid-market"],
    "key_challenges": ["competition", "scalability"]
  }
}
```

## Configuration

### Team Configuration
See `config/team_config.yaml` for agent definitions and team settings.

### A2A Configuration  
See `config/a2a_config.yaml` for inter-team communication settings.

### LLM Configuration
Currently uses CrewAI defaults (OpenAI GPT-4). To use a different LLM provider:

1. Set environment variables:
   - For OpenAI: `OPENAI_API_KEY`
   - For Anthropic: `ANTHROPIC_API_KEY` (requires code modification)

2. Modify agent creation in individual agent files to specify LLM:
   ```python
   from langchain_openai import ChatOpenAI
   # or
   from langchain_anthropic import ChatAnthropic
   
   agent = Agent(
       role="...",
       goal="...",
       llm=ChatOpenAI(model="gpt-4")  # or ChatAnthropic(model="claude-3-opus")
   )
   ```

## Logs
Team communications are logged to `/logs/executive-team_communications.log` for natural language analysis and optimization.