# ElfAutomations.ai Control Center Guide

## Overview

The ElfAutomations.ai Control Center is a comprehensive dashboard for monitoring and controlling your autonomous AI ecosystem. It provides real-time insights into:

- **Team Management**: View team hierarchy, status, and relationships
- **Cost Analytics**: Monitor API usage, costs, and budget tracking
- **Workflow Status**: Track N8N workflows and execution metrics
- **System Health**: Monitor infrastructure and API availability
- **Activity Feed**: See recent system events and alerts

## Architecture

The Control Center consists of two main components:

### 1. Control Center API (Backend)
- FastAPI-based REST API at `http://localhost:8001`
- WebSocket support for real-time updates
- Integrates with Supabase for data storage
- Provides aggregated data from multiple sources

### 2. Control Center UI (Frontend)
- Next.js 14 app with App Router at `http://localhost:3002`
- Real-time data updates via WebSocket
- Beautiful dark theme with animations
- Responsive design for all screen sizes

## Quick Start

### Option 1: One-Command Start
```bash
./scripts/start_control_center.sh
```

This will start both the API and UI automatically.

### Option 2: Manual Start

**Start the API:**
```bash
python scripts/run_control_center_api.py
```

**Start the UI:**
```bash
cd packages/templates/elf-control-center
npm run dev
```

## Features

### System Status Dashboard
- Real-time metrics for active teams, workflows, costs, and health
- Animated counters with trend indicators
- Color-coded health scores

### Team Hierarchy View
- Interactive tree view of all teams
- Shows reporting relationships
- Team member counts and status
- Framework and LLM provider info

### Cost Analytics
- Today's cost vs budget
- Monthly spending tracking
- Cost breakdown by model (OpenAI, Anthropic)
- Hourly cost trends
- Top spending teams

### Workflow Monitoring
- Active workflow status
- Success rates and execution counts
- Average duration metrics
- Last run timestamps

### Infrastructure Health
- API availability monitoring
- System load metrics
- Service status indicators
- Real-time health scores

### Activity Feed
- Recent team operations
- Cost alerts and warnings
- System events
- Chronological event timeline

## API Endpoints

### Core Endpoints
- `GET /api/system/status` - System health and status
- `GET /api/costs/metrics` - Cost analytics data
- `GET /api/teams` - Team hierarchy and info
- `GET /api/workflows` - N8N workflow status
- `GET /api/activities` - Recent system activities
- `GET /api/dashboard` - All dashboard data (optimized)

### WebSocket
- `ws://localhost:8001/ws` - Real-time status updates

### Documentation
- `http://localhost:8001/docs` - Interactive API documentation

## Data Sources

The Control Center aggregates data from:

1. **Supabase Tables**:
   - `teams` - Team registry
   - `team_members` - Team composition
   - `team_relationships` - Organizational hierarchy
   - `api_usage` - Detailed API usage tracking
   - `daily_cost_summary` - Aggregated cost data
   - `cost_alerts` - Budget alerts
   - `n8n_workflow_registry` - Workflow metadata

2. **Live Services**:
   - Team health checks via `/health` endpoints
   - N8N status via API
   - Real-time cost tracking

## Customization

### Adding New Metrics
1. Update the API to fetch new data
2. Add to the dashboard response model
3. Create/update UI components
4. Add to the dashboard layout

### Theming
- Colors defined in `globals.css`
- Component variants in UI library
- Gradient system for accents

### Adding New Pages
1. Create new route in `app/` directory
2. Add navigation item
3. Create page components
4. Connect to API endpoints

## Troubleshooting

### API Connection Issues
- Ensure Supabase environment variables are set
- Check API is running on port 8001
- Verify CORS settings for your domain

### Missing Data
- Run team registry setup: `python scripts/setup_team_registry.py`
- Ensure cost monitoring tables exist
- Check Supabase connection

### UI Build Issues
- Run `npm install` in the UI directory
- Clear `.next` cache if needed
- Check Node.js version (18+ required)

## Development

### Adding New Features
1. Design API endpoint in `control_center.py`
2. Add TypeScript types in `api.ts`
3. Create React components
4. Update dashboard layout
5. Test with real data

### Best Practices
- Use React Query for data fetching
- Implement error boundaries
- Add loading states
- Keep components modular
- Use TypeScript for type safety

## Future Enhancements

Planned features include:
- Team deployment controls
- Workflow builder UI
- Budget management interface
- Advanced filtering and search
- Export capabilities
- Mobile app version
