# Team & MCP Creation Commands for ElfAutomations

## Important: Use the Factory Tools!
All teams and MCPs must be created using:
- `tools/team_factory.py` - For creating teams
- `tools/mcp_factory.py` - For creating MCPs

Never manually create or edit team files!

## Step 1: Set Up Team Registry
```bash
cd scripts
python setup_team_registry.py
```

## Step 2: Create Missing Executive (CPO)
First, we need to add a Chief Product Officer to the executive team.

**Note**: The team factory creates NEW teams. To add CPO to existing executive team, we need to use the factory to create a patch/update mechanism or recreate the executive team with CPO included.

## Step 3: Create Product Team
```bash
cd tools
python team_factory.py
```

When prompted, enter:
- **Team Description**: "Create a product management team led by a Senior Product Manager who reports to the Chief Product Officer. The team includes a Business Analyst who researches market needs and creates detailed requirements, a Technical Product Manager who works closely with engineering teams, a UX Researcher who conducts user interviews and usability studies, and a Competitive Intelligence Analyst who monitors competitors and market trends. This team is responsible for creating comprehensive Product Requirements Documents, defining success metrics, and prioritizing features based on data-driven insights."
- **Framework**: CrewAI (better for collaborative research)
- **Organization**: product
- **LLM Provider**: openai

## Step 4: Create Engineering Team
```bash
cd tools
python team_factory.py
```

When prompted:
- **Team Description**: "Create an engineering team led by an Engineering Manager who reports to the CTO. The team includes a Principal Backend Engineer who designs system architecture, a Senior API Developer who creates RESTful and GraphQL APIs, a Database Architect who designs schemas and optimization strategies, and a DevOps Engineer who handles CI/CD and infrastructure. They build scalable, production-ready systems with proper monitoring and documentation."
- **Framework**: CrewAI
- **Organization**: engineering
- **LLM Provider**: openai

## Step 5: Create Mobile Engineering Team
```bash
cd tools
python team_factory.py
```

When prompted:
- **Team Description**: "Create a mobile engineering team led by a Mobile Engineering Lead who reports to the Engineering Manager. The team includes a Senior iOS Developer, Senior Android Developer, React Native Specialist who can build cross-platform apps, and a Mobile QA Engineer. They specialize in building mobile applications for field workers with offline-first architecture, GPS integration, and camera functionality."
- **Framework**: CrewAI
- **Organization**: engineering.mobile
- **LLM Provider**: openai

## Step 6: Create Frontend/Dashboard Team
```bash
cd tools
python team_factory.py
```

When prompted:
- **Team Description**: "Create a frontend engineering team led by a Frontend Lead who reports to the Engineering Manager. The team includes a Senior React Developer, Dashboard Specialist who excels at data visualization, UI Implementation Engineer, and Performance Optimization Expert. They build responsive web dashboards with real-time updates, complex filtering, and beautiful data visualizations."
- **Framework**: CrewAI
- **Organization**: engineering.frontend
- **LLM Provider**: openai

## Step 7: Create QA Team
```bash
cd tools
python team_factory.py
```

When prompted:
- **Team Description**: "Create a quality assurance team led by a QA Manager who reports to the CTO. The team includes a Test Automation Engineer who writes automated tests, a Mobile Testing Specialist, a Performance Testing Engineer, and a Security Testing Expert. They ensure product quality through comprehensive testing strategies including unit, integration, E2E, and security testing."
- **Framework**: LangGraph (good for test workflows)
- **Organization**: qa
- **LLM Provider**: openai

## Step 8: Create Marketing Team
```bash
cd tools
python team_factory.py
```

When prompted:
- **Team Description**: "Create a B2B marketing team led by a Marketing Director who reports to the CMO. The team includes a Product Marketing Manager who creates positioning and messaging, a Content Marketing Manager who develops thought leadership content, a Demand Generation Manager who drives qualified leads, and a Marketing Operations Specialist who manages tools and analytics. They focus on construction industry marketing."
- **Framework**: CrewAI
- **Organization**: marketing
- **LLM Provider**: openai

## Step 9: Create Sales Team
```bash
cd tools
python team_factory.py
```

When prompted:
- **Team Description**: "Create an enterprise sales team led by a VP of Sales who reports to the CEO. The team includes an Enterprise Account Executive who sells to large construction companies, a Solutions Engineer who demonstrates technical capabilities, a Sales Operations Manager who optimizes the sales process, and a Customer Success Manager who ensures client satisfaction and renewal. They sell B2B SaaS to construction companies."
- **Framework**: CrewAI
- **Organization**: sales
- **LLM Provider**: openai

## Step 10: Create Finance Team
```bash
cd tools
python team_factory.py
```

When prompted:
- **Team Description**: "Create a finance team led by a Finance Director who reports to the CFO. The team includes a Senior Financial Analyst who creates financial models, a Pricing Strategist who optimizes SaaS pricing, a Revenue Operations Analyst who tracks metrics, and a FP&A Specialist who handles planning and analysis. They model unit economics, create pricing strategies, and project financial outcomes for SaaS products."
- **Framework**: CrewAI
- **Organization**: finance
- **LLM Provider**: openai

## Step 11: Create Critical MCPs

### Code Generator MCP
```bash
cd tools
python mcp_factory.py
```
- **Type**: internal
- **Name**: code-generator
- **Description**: Generates production-ready code in multiple languages following best practices, includes error handling, logging, tests, and documentation

### API Designer MCP
```bash
cd tools
python mcp_factory.py
```
- **Type**: internal
- **Name**: api-designer
- **Description**: Designs RESTful and GraphQL APIs with OpenAPI specifications, authentication patterns, rate limiting, and versioning strategies

### Database Architect MCP
```bash
cd tools
python mcp_factory.py
```
- **Type**: internal
- **Name**: database-architect
- **Description**: Designs optimized database schemas with proper normalization, indexing strategies, migration scripts, and backup procedures

### Market Research MCP
```bash
cd tools
python mcp_factory.py
```
- **Type**: internal
- **Name**: market-research
- **Description**: Researches industry trends, analyzes competitors, identifies market opportunities, and provides pricing intelligence using web scraping and data analysis

### Twilio Gateway MCP
```bash
cd tools
python mcp_factory.py
```
- **Type**: external
- **Name**: twilio-gateway
- **Description**: Integrates with Twilio API for SMS messaging, phone number management, message queuing, and delivery tracking

### UI Component Library MCP
```bash
cd tools
python mcp_factory.py
```
- **Type**: internal
- **Name**: ui-components
- **Description**: Provides reusable React components for dashboards, forms, tables, charts, and common UI patterns with consistent styling

## Step 12: Deploy Teams
For each team created:
```bash
cd teams/{team-name}
python make-deployable-team.py
docker build -t elf-automations/{team-name}:latest .
cd ../..
./scripts/transfer-docker-images-ssh.sh {team-name}
```

## Step 13: Test Communication
Once teams are deployed, test A2A communication:
```bash
# Test product team receiving request from CEO
kubectl exec -it executive-team-pod -n elf-teams -- curl -X POST http://product-team:8090/task \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create PRD for construction project management platform",
    "context": {
      "target_audience": "construction project managers",
      "key_feature": "SMS communication with field workers",
      "priority": "MVP in 8 weeks"
    }
  }'
```

## Important Notes
1. The team factory automatically registers teams in Supabase
2. Manager agents get A2A communication capabilities
3. Teams can be created in any order, but logical hierarchy helps
4. Each team gets its own K8s deployment
5. MCPs are shared across teams

## What Happens Next?
Once all teams are created and deployed, you can send your construction PM request to the CEO, and the entire organization will collaborate to build your product!
