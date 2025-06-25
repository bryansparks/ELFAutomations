# ELF Automations Central Dashboard

A comprehensive dashboard for managing and monitoring the entire ELF Automations ecosystem.

## Features

### 🎯 Team Operations Center
- Real-time team status and health monitoring
- Team creation wizard integrated with Team Factory
- Interactive team hierarchy visualization
- Inter-team communication flow tracking
- Team performance metrics and analytics

### 🔄 Workflow Management
- N8N workflow catalog and execution history
- Success/failure rate tracking
- Workflow builder interface
- Real-time execution monitoring
- Performance analytics

### 💰 Cost & Resource Management
- Real-time cost tracking by team and model
- Budget alerts and notifications
- Usage trends and predictions
- Cost optimization suggestions
- Resource allocation visualization

### 🏗️ Infrastructure Dashboard
- Kubernetes deployment status
- Container health monitoring
- Database migration status
- System resource usage graphs
- Service discovery interface

### 💬 Communication Hub
- A2A message flow visualization
- Team communication logs
- Message success/failure rates
- Communication pattern analysis

### 🧩 MCP Registry
- Available MCPs catalog
- MCP health status monitoring
- Usage statistics
- MCP creation interface

## Architecture

### Backend (FastAPI)
- **Location**: `/dashboard/backend/`
- **Port**: 8000
- **Features**:
  - REST API for all dashboard operations
  - WebSocket support for real-time updates
  - Direct Supabase integration
  - Aggregates data from all ELF systems
  - Authentication and authorization ready

### Frontend (Next.js + React)
- **Location**: `/dashboard/frontend/`
- **Port**: 3001
- **Features**:
  - Modern, responsive UI with dark mode
  - Real-time data updates via WebSocket
  - Interactive charts and visualizations
  - Team and workflow builders
  - Component-based architecture

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- Supabase account with configured database
- Access to ELF infrastructure

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd dashboard/backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables:
   ```bash
   export SUPABASE_URL="your-supabase-url"
   export SUPABASE_ANON_KEY="your-supabase-anon-key"
   export N8N_URL="http://n8n.n8n.svc.cluster.local:5678"  # Or your N8N URL
   export N8N_API_KEY="your-n8n-api-key"  # If required
   ```

5. Run the backend:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd dashboard/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

   The dashboard will be available at `http://localhost:3001`

## Development

### Backend Development
- API routes are defined in `backend/main.py`
- Add new endpoints following the existing pattern
- Use `DashboardService` class for data aggregation
- WebSocket broadcasts for real-time updates

### Frontend Development
- Components are in `frontend/components/`
- Dashboard components in `frontend/components/dashboard/`
- UI components in `frontend/components/ui/`
- API client in `frontend/lib/api.ts`
- State management with Zustand in `frontend/stores/`

### Adding New Features

1. **Backend**: Add endpoint in `main.py`
2. **Frontend**: Add API method in `lib/api.ts`
3. **Component**: Create new component in `components/dashboard/`
4. **Integration**: Add to main dashboard or create new tab

## Production Deployment

### Backend Deployment

1. Build Docker image:
   ```bash
   docker build -t elf-dashboard-backend dashboard/backend/
   ```

2. Deploy to Kubernetes:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: elf-dashboard-backend
     namespace: elf-system
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: elf-dashboard-backend
     template:
       metadata:
         labels:
           app: elf-dashboard-backend
       spec:
         containers:
         - name: backend
           image: elf-dashboard-backend:latest
           ports:
           - containerPort: 8000
           env:
           - name: SUPABASE_URL
             valueFrom:
               secretKeyRef:
                 name: elf-secrets
                 key: supabase-url
           - name: SUPABASE_ANON_KEY
             valueFrom:
               secretKeyRef:
                 name: elf-secrets
                 key: supabase-anon-key
   ```

### Frontend Deployment

1. Build production bundle:
   ```bash
   cd dashboard/frontend
   npm run build
   ```

2. Deploy using your preferred method (Vercel, Nginx, etc.)

## API Documentation

### REST Endpoints

- `GET /api/stats` - Dashboard overview statistics
- `GET /api/teams` - List all teams
- `POST /api/teams` - Create new team
- `GET /api/workflows` - List all workflows
- `POST /api/workflows` - Create new workflow
- `GET /api/costs` - Cost analytics data
- `GET /api/health` - System health status
- `GET /api/mcps` - List available MCPs
- `GET /api/communications` - Communication logs

### WebSocket Events

- `stats_update` - Real-time stats updates
- `alert` - System alerts and notifications
- `team_update` - Team status changes
- `workflow_update` - Workflow execution updates

## Troubleshooting

### Backend Issues
- Check Supabase connection and credentials
- Verify all required environment variables are set
- Check logs for detailed error messages
- Ensure proper network access to Supabase and N8N

### Frontend Issues
- Verify backend is running and accessible
- Check browser console for errors
- Ensure WebSocket connection is established
- Clear browser cache if UI doesn't update

## Future Enhancements

1. **Authentication & Authorization**
   - User login system
   - Role-based access control
   - Team-specific dashboards

2. **Advanced Analytics**
   - Machine learning cost predictions
   - Anomaly detection
   - Performance optimization recommendations

3. **Automation**
   - Automated team scaling
   - Workflow optimization
   - Cost reduction automation

4. **Integrations**
   - Slack notifications
   - Email alerts
   - External monitoring tools

## Contributing

1. Create feature branch
2. Make changes with tests
3. Update documentation
4. Submit pull request

## License

Part of ELF Automations ecosystem
