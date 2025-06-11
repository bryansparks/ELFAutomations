# Infrastructure Automation Guide (Task 8)

## Overview

The Infrastructure Automation framework provides comprehensive automation for all infrastructure components in ElfAutomations, eliminating manual steps and ensuring reliable, repeatable deployments.

## Architecture

```
/elf_automations/shared/infrastructure/
├── __init__.py              # Package exports
├── docker_manager.py        # Docker operations & registry
├── database_manager.py      # Database migrations & health
├── deployment_pipeline.py   # Team deployment automation
├── health_checker.py        # Infrastructure health monitoring
├── config_manager.py        # Configuration & secrets
└── k8s_manager.py          # Kubernetes operations

/scripts/
└── setup_infrastructure.py  # Master setup orchestrator
```

## Components

### 1. Docker Manager

**Purpose**: Automates Docker registry management and image operations.

**Key Features**:
- Local Docker registry setup (eliminates manual transfers)
- Image building with automatic tagging
- Registry push/pull operations
- Image transfer via SSH (when needed)
- Automatic cleanup of old images

**Usage Example**:
```python
from elf_automations.shared.infrastructure import DockerManager, ImageTransfer

# Initialize manager
docker = DockerManager(
    registry_host="localhost:5000",
    remote_host="192.168.6.5",
    remote_user="bryan"
)

# Setup local registry
docker.setup_local_registry()

# Build and push image
image = docker.build_image(
    path="teams/marketing-team",
    image_name="elf-automations/marketing-team",
    tag="v1.0.0",
    push_to_registry=True
)

# Transfer to remote if needed
transfer = ImageTransfer(docker)
transfer.transfer_image(image)

# Cleanup old images
docker.cleanup_old_images(keep_last=5)
```

### 2. Database Manager

**Purpose**: Manages database schemas and migrations with tracking.

**Key Features**:
- Automatic migration discovery from SQL files
- Migration tracking (prevents duplicate runs)
- Schema health verification
- Backup hooks for safety
- Rollback capabilities (planned)

**Migration Workflow**:
1. Discovers SQL files in `/sql/` directory
2. Calculates checksums to detect changes
3. Tracks execution in `schema_migrations` table
4. Executes only pending migrations
5. Verifies schema health after execution

**Usage Example**:
```python
from elf_automations.shared.infrastructure import DatabaseManager, MigrationRunner

# Initialize manager
db_manager = DatabaseManager()

# Run all migrations
runner = MigrationRunner(db_manager)
results = runner.setup_all_schemas()

# Verify health
health = db_manager.verify_schema_health()
print(f"Database healthy: {health['healthy']}")
print(f"Tables: {health['tables']}")
```

### 3. Deployment Pipeline

**Purpose**: Automates the complete team deployment workflow with health checks.

**Pipeline Stages**:
1. **PRE_BUILD**: Environment preparation
2. **BUILD**: Docker image building
3. **TEST**: Container smoke tests
4. **PUSH**: Registry push
5. **DEPLOY**: Kubernetes deployment
6. **VERIFY**: Health verification
7. **POST_DEPLOY**: Cleanup and notifications

**Features**:
- Stage hooks for customization
- Automatic rollback on failure
- Parallel deployment support
- Comprehensive reporting

**Usage Example**:
```python
from elf_automations.shared.infrastructure import DeploymentPipeline

# Initialize pipeline
pipeline = DeploymentPipeline(
    docker_manager=docker,
    health_checker=health_checker
)

# Add custom hooks
async def notify_slack(context):
    print(f"Deploying {context.team_name}...")

pipeline.add_stage_hook(DeploymentStage.PRE_BUILD, notify_slack)

# Deploy single team
context = await pipeline.deploy_team(
    team_name="marketing-team",
    auto_rollback=True
)

# Deploy multiple teams
results = await pipeline.deploy_multiple_teams(
    ["marketing-team", "sales-team"],
    parallel=True
)

# Get report
report = pipeline.get_deployment_report(results)
```

### 4. Health Checker

**Purpose**: Comprehensive health monitoring for all infrastructure components.

**Monitors**:
- System resources (CPU, memory, disk)
- Docker daemon and registry
- Kubernetes cluster and nodes
- Database connections
- Individual deployments
- HTTP endpoints

**Usage Example**:
```python
from elf_automations.shared.infrastructure import HealthChecker, InfrastructureHealth

async with HealthChecker() as checker:
    # Check all components
    health = InfrastructureHealth(checker)
    report = await health.get_health_report()

    # Check specific deployment
    deployment_health = await checker.check_deployment_health(
        "marketing-team",
        namespace="elf-teams"
    )

    # Wait for resource to be healthy
    healthy = await checker.wait_for_healthy(
        lambda: checker.check_deployment_health("marketing-team"),
        timeout=300
    )

    # Continuous monitoring
    await health.monitor_continuously(
        interval=60,
        callback=lambda report: print(f"Health: {report['overall_status']}")
    )
```

### 5. Config Manager

**Purpose**: Centralized configuration and secrets management.

**Features**:
- Environment-specific configurations
- Encrypted secrets storage
- Kubernetes secret generation
- Environment validation
- Team-specific configs

**Usage Example**:
```python
from elf_automations.shared.infrastructure import ConfigManager

# Initialize for environment
config = ConfigManager(environment="production")

# Validate environment
validation = config.validate_environment()
if not validation['valid']:
    print(f"Missing: {validation['missing']}")

# Manage secrets
config.set_secret("API_KEY", "secret-value", encrypt=True)
api_key = config.get_secret("API_KEY")

# Generate K8s secret
manifest = config.generate_k8s_secret_manifest(
    secret_name="app-secrets",
    namespace="elf-teams",
    keys=["API_KEY", "DATABASE_URL"]
)

# Export .env file
config.export_env_file()
```

### 6. K8s Manager

**Purpose**: Kubernetes cluster operations and resource management.

**Capabilities**:
- Cluster access validation
- Resource CRUD operations
- Pod operations (logs, exec)
- Service discovery
- Port forwarding
- Deployment management

**Usage Example**:
```python
from elf_automations.shared.infrastructure import K8sManager, ClusterSetup

# Initialize manager
k8s = K8sManager(context="docker-desktop")

# Check cluster
if k8s.check_cluster_access():
    print("Cluster accessible")

# Create namespace
k8s.create_namespace("elf-teams", labels={"env": "production"})

# Deploy resources
k8s.apply_manifests_from_directory(Path("k8s/base"))

# Wait for deployment
k8s.wait_for_deployment("marketing-team", namespace="elf-teams")

# Get logs
logs = k8s.get_pod_logs(
    "marketing-team-abc123",
    namespace="elf-teams",
    tail=100
)

# Port forward (returns process to manage)
port_forward = k8s.port_forward(
    "svc/marketing-team",
    local_port=8080,
    remote_port=8000
)
```

## Master Setup Script

The `setup_infrastructure.py` script orchestrates the complete infrastructure setup.

### Phases

1. **Environment Validation**
   - Checks required tools (docker, kubectl, python, git)
   - Validates environment variables
   - Reports missing dependencies

2. **Docker Setup**
   - Creates local registry on :5000
   - Configures remote Docker access (if specified)
   - Tests registry connectivity

3. **Kubernetes Setup**
   - Validates cluster access
   - Creates namespaces (elf-teams, elf-monitoring, argocd)
   - Applies base manifests

4. **Database Setup**
   - Connects to Supabase
   - Runs all pending migrations
   - Verifies schema health

5. **Monitoring Setup**
   - Deploys Prometheus
   - Deploys Grafana
   - Configures dashboards

6. **ArgoCD Setup**
   - Installs ArgoCD (if not present)
   - Waits for readiness
   - Configures applications

7. **Health Verification**
   - Comprehensive health check
   - Reports status of all components
   - Provides actionable next steps

### Usage

```bash
# Full setup
python scripts/setup_infrastructure.py

# Skip certain components
python scripts/setup_infrastructure.py --skip-docker --skip-db

# With remote Docker host
python scripts/setup_infrastructure.py \
    --remote-host 192.168.6.5 \
    --remote-user bryan

# Fix corrupted transfer script
python scripts/setup_infrastructure.py --fix-transfer
```

### Output Example

```
ElfAutomations Infrastructure Setup
==================================

✅ Environment validation complete
✅ Docker registry running on localhost:5000
✅ Kubernetes cluster is ready
✅ Created namespace: elf-teams
✅ Connected to Supabase
✅ Ran 5 migrations
✅ Prometheus deployed
✅ Grafana deployed
✅ ArgoCD is ready

Infrastructure Health
====================
System      HEALTHY    System resources normal
Docker      HEALTHY    Docker daemon and registry healthy
Kubernetes  HEALTHY    Kubernetes cluster healthy
Database    HEALTHY    Database connection healthy

Infrastructure Setup Summary
===========================
Component    Status    Details
Environment  ✅ Valid   0 missing
Docker       ✅ Ready   Registry on :5000
Kubernetes   ✅ Ready   3 namespaces
Database     ✅ Ready   5 migrations
Monitoring   ✅ Ready   Prometheus + Grafana
ArgoCD       ✅ Ready   GitOps ready

Next Steps:
1. Deploy teams: python scripts/deploy_teams.py
2. Access ArgoCD: kubectl port-forward svc/argocd-server -n argocd 8080:443
3. Access Grafana: kubectl port-forward svc/grafana -n elf-monitoring 3000:80
4. Monitor health: python scripts/monitor_infrastructure.py
```

## Best Practices

### 1. Always Run Health Checks
```python
# Before deployment
health = await health_checker.check_deployment_health(team_name)
if not health.is_healthy:
    print(f"Unhealthy: {health.message}")
    return

# After deployment
await health_checker.wait_for_healthy(
    lambda: health_checker.check_deployment_health(team_name)
)
```

### 2. Use Configuration Manager for Secrets
```python
# Don't hardcode secrets
# BAD: api_key = "sk-12345"

# GOOD: Use config manager
config = ConfigManager()
api_key = config.get_secret("OPENAI_API_KEY")
```

### 3. Enable Auto-Rollback
```python
# Always enable rollback for production
context = await pipeline.deploy_team(
    team_name="critical-team",
    auto_rollback=True  # Default, but be explicit
)
```

### 4. Monitor Continuously
```python
# Setup continuous monitoring
async def alert_on_failure(report):
    if report['overall_status'] != 'healthy':
        send_alert(f"Infrastructure unhealthy: {report}")

await health.monitor_continuously(
    interval=60,
    callback=alert_on_failure
)
```

### 5. Clean Up Resources
```python
# Regularly clean up old images
docker.cleanup_old_images(keep_last=5)

# Remove failed deployments
if context.status == DeploymentStatus.FAILED:
    k8s.scale_deployment(context.team_name, replicas=0)
```

## Troubleshooting

### Docker Registry Issues
```bash
# Check registry is running
docker ps | grep registry

# Test registry access
curl http://localhost:5000/v2/

# Check registry contents
curl http://localhost:5000/v2/_catalog
```

### Kubernetes Deployment Failures
```bash
# Check deployment status
kubectl describe deployment marketing-team -n elf-teams

# Check pod events
kubectl describe pod marketing-team-xxx -n elf-teams

# View logs
kubectl logs deployment/marketing-team -n elf-teams
```

### Database Migration Failures
```python
# Check migration status
migrations = db_manager.discover_migrations()
for m in migrations:
    status = db_manager.get_migration_status(m)
    print(f"{m.name}: {status.value}")

# Verify specific tables
health = db_manager.verify_schema_health()
for table, status in health['tables'].items():
    print(f"{table}: {status}")
```

## Integration with Other Tasks

### With Fallback Protocols (Task 7)
```python
from elf_automations.shared.resilience import with_retry, with_circuit_breaker

@with_retry(max_retries=3)
@with_circuit_breaker(failure_threshold=5)
async def deploy_with_resilience(team_name: str):
    return await pipeline.deploy_team(team_name)
```

### With Cost Monitoring (Task 6)
```python
# Track deployment costs
from elf_automations.shared.monitoring import CostMonitor

monitor = CostMonitor()
start_time = datetime.now()

context = await pipeline.deploy_team("marketing-team")

duration = (datetime.now() - start_time).total_seconds()
monitor.record_deployment_cost(
    team_name="marketing-team",
    duration_seconds=duration,
    resources_used={"cpu": 2, "memory_gb": 4}
)
```

## Summary

The Infrastructure Automation framework provides:

1. **Complete Automation**: From Docker registry to deployment verification
2. **Error Resilience**: Automatic rollback and comprehensive error handling
3. **Health Monitoring**: Continuous health checks at every level
4. **Configuration Management**: Centralized config with encryption
5. **Easy Integration**: Works seamlessly with other automation tasks

This eliminates manual steps, reduces errors, and provides reliable, repeatable infrastructure deployments for ElfAutomations teams.
