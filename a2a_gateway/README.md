# A2A Gateway

Central routing and discovery service for team-to-team communication using the Google A2A protocol.

## Overview

The A2A Gateway provides:
- **Central Registry**: All teams register with the gateway on startup
- **Smart Routing**: Routes tasks based on capabilities, availability, and performance
- **Health Monitoring**: Continuous health checks with circuit breakers
- **Load Balancing**: Distributes tasks across team instances
- **Discovery Service**: Teams can discover each other's capabilities
- **Analytics**: Tracks routing decisions and team performance

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Sales Team    │     │ Marketing Team  │     │  Product Team   │
│   Port: 8090    │     │   Port: 8091    │     │   Port: 8092    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │ Register              │ Register              │ Register
         │ & Route               │ & Route               │ & Route
         └───────────────────────┴───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      A2A Gateway        │
                    │      Port: 8080         │
                    │                         │
                    │ • Team Registry         │
                    │ • Smart Routing         │
                    │ • Health Monitoring     │
                    │ • Load Balancing        │
                    │ • Analytics             │
                    └────────────┬────────────┘
                                 │
                         ┌───────▼────────┐
                         │    Supabase    │
                         │   (Optional)   │
                         └────────────────┘
```

## Quick Start

### 1. Run the Gateway

```bash
# With Docker
docker build -t a2a-gateway .
docker run -p 8080:8080 -e SUPABASE_URL=<your-url> -e SUPABASE_ANON_KEY=<your-key> a2a-gateway

# Or with Python
pip install -r requirements.txt
python src/gateway_server.py
```

### 2. Register a Team

Teams should auto-register on startup using the provided client:

```python
from a2a_gateway.src.gateway_client import TeamAutoRegistration

# In your team's startup code
auto_reg = TeamAutoRegistration(
    team_id="sales-team",
    team_name="Sales Team",
    team_port=8090,
    capabilities=["sales", "customer-engagement", "proposal-generation"],
    department="sales"
)

# Register on startup
await auto_reg.register()

# Unregister on shutdown
await auto_reg.unregister()
```

### 3. Route Tasks Through Gateway

Update your A2A client to use the gateway:

```python
from elf_automations.shared.a2a.client import A2AClient

# Client will automatically use gateway if available
client = A2AClient(
    team_id="marketing-team",
    use_gateway=True  # Default
)

# Route by capability (gateway will find best team)
result = await client.send_task(
    target_team=None,  # Let gateway decide
    task_description="Generate a sales proposal for enterprise client",
    required_capabilities=["sales", "proposal-generation"]
)

# Or route to specific team
result = await client.send_task(
    target_team="sales-team",
    task_description="Generate a sales proposal"
)
```

## API Endpoints

### Registration
- `POST /register` - Register a team
- `DELETE /teams/{team_id}` - Unregister a team

### Discovery
- `GET /teams` - List all teams (optional: `?capability=sales`)
- `GET /teams/{team_id}` - Get team details
- `GET /capabilities` - List all available capabilities

### Routing
- `POST /route` - Route a task to appropriate team
- `POST /proxy/{team_id}/task` - Direct proxy to specific team

### Monitoring
- `GET /health` - Gateway health check
- `GET /stats` - Gateway and team statistics

## Configuration

### Environment Variables

```bash
# Server
PORT=8080
HOST=0.0.0.0
LOG_LEVEL=INFO

# Supabase (optional, for persistence)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Security
GATEWAY_REGISTRATION_TOKEN=your-secure-token

# Gateway URL (for teams to discover)
GATEWAY_URL=http://a2a-gateway-service:8080
```

### Configuration File

See `config/gateway_config.yaml` for detailed configuration options.

## Deployment

### Kubernetes

```bash
# Create namespace
kubectl create namespace elf-teams

# Create secrets
kubectl create secret generic a2a-gateway-secrets \
  --from-literal=registration-token=$(openssl rand -hex 32) \
  -n elf-teams

# Deploy
kubectl apply -f k8s/
```

### Docker Compose

```yaml
version: '3.8'
services:
  a2a-gateway:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - GATEWAY_REGISTRATION_TOKEN=${GATEWAY_REGISTRATION_TOKEN}
```

## Database Schema

The gateway uses Supabase for persistent storage. Run the schema:

```bash
# Apply schema
psql $DATABASE_URL < sql/create_a2a_gateway_schema.sql
```

Tables:
- `a2a_teams` - Registered teams and their status
- `a2a_routing_log` - Routing decisions and analytics

## Monitoring

### Health Checks

The gateway performs automatic health checks every 30 seconds. Teams are marked as:
- `healthy` - Responding normally
- `degraded` - Slow responses or intermittent failures
- `unhealthy` - Not responding

### Circuit Breaker

After 3 consecutive failures, a team's circuit breaker opens for 5 minutes.

### Metrics

Prometheus metrics available at `/metrics`:
- Team registration count
- Routing decisions
- Success/failure rates
- Response times

## Integration with Teams

### Team Configuration

Update your team's `a2a_config.yaml`:

```yaml
a2a:
  gateway_url: http://a2a-gateway-service:8080
  auto_register: true
  capabilities:
    - sales
    - customer-engagement
    - proposal-generation
```

### Team Server Updates

In your team's server startup:

```python
from a2a_gateway.src.gateway_client import TeamAutoRegistration

@app.on_event("startup")
async def startup_event():
    # Existing startup code...
    
    # Auto-register with gateway
    auto_reg = TeamAutoRegistration(
        team_id="your-team-id",
        team_name="Your Team Name",
        team_port=8090,
        capabilities=["capability1", "capability2"],
        department="your-department"
    )
    
    await auto_reg.register()
```

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Features

1. **Custom Routing Logic**: Extend `_find_target_team()` in `gateway_server.py`
2. **New Metrics**: Add to the `/stats` endpoint
3. **Authentication**: Implement in the security middleware

## Troubleshooting

### Teams Not Registering

1. Check gateway is running: `curl http://localhost:8080/health`
2. Verify registration token is set correctly
3. Check team can reach gateway URL
4. Look for errors in gateway logs

### Routing Failures

1. Check team health: `GET /teams/{team_id}`
2. Verify capabilities match
3. Check circuit breaker status
4. Review routing logs in Supabase

### Performance Issues

1. Monitor `/stats` endpoint
2. Check database query performance
3. Scale gateway replicas if needed
4. Enable caching for team discovery

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Team capability versioning
- [ ] Advanced load balancing algorithms
- [ ] Integration with MCP tools
- [ ] Multi-region support
- [ ] Team authentication and authorization
- [ ] Request replay and debugging tools